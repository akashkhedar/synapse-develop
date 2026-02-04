import { IconChevronDown, IconChevronRight, IconTrash } from "@synapse/icons";
import { Button, Spinner, Tooltip } from "@synapse/ui";
import { inject, observer } from "mobx-react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import { useActions } from "../../../hooks/useActions";
import { cn } from "../../../utils/bem";
import { FF_LOPS_E_3, isFF } from "../../../utils/feature-flags";
import { Dropdown } from "@synapse/ui";
import Form from "../../Common/Form/Form";
import { Menu } from "../../Common/Menu/Menu";
import { Modal } from "../../Common/Modal/ModalPopup";
import "./TabPanel.scss"; // Ensure styles are loaded

const isFFLOPSE3 = isFF(FF_LOPS_E_3);
const injector = inject(({ store }) => ({
  store,
  hasSelected: store.currentView?.selected?.hasSelected ?? false,
}));

// Modern actions button styles matching OrderButton design
// Styles moved to TabPanel.scss (.dm-toolbar-button)

// Menu item styles
const menuItemStyle = {
  fontFamily: "'Space Grotesk', system-ui, -apple-system, sans-serif",
  fontSize: "13px",
  fontWeight: 500,
  letterSpacing: "0.02em",
  transition: "all 150ms cubic-bezier(0.4, 0, 0.2, 1)",
};

const menuTitleStyle = {
  fontFamily: "'Space Grotesk', system-ui, -apple-system, sans-serif",
  fontSize: "11px",
  fontWeight: 600,
  letterSpacing: "0.1em",
  textTransform: "uppercase",
  color: "#a78bfa",
};

const separatorStyle = {
  height: "1px",
  background:
    "linear-gradient(90deg, transparent, rgba(139, 92, 246, 0.3), transparent)",
  margin: "8px 0",
};

const DialogContent = ({ text, form, formRef, store, action }) => {
  const [formData, setFormData] = useState(form);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (!formData) {
      setIsLoading(true);
      store
        .fetchActionForm(action.id)
        .then((form) => {
          setFormData(form);
        })
        .finally(() => {
          setIsLoading(false);
        });
    }
  }, [formData, store, action.id]);

  const fields = formData?.toJSON ? formData.toJSON() : formData;

  return (
    <div className={cn("dialog-content").toClassName()}>
      <div className={cn("dialog-content").elem("text").toClassName()}>
        {text}
      </div>
      {isLoading && (
        <div
          className={cn("dialog-content").elem("loading").toClassName()}
          style={{ display: "flex", justifyContent: "center", marginTop: 16 }}
        >
          <Spinner />
        </div>
      )}
      {formData && (
        <div
          className={cn("dialog-content").elem("form").toClassName()}
          style={{ paddingTop: 16 }}
        >
          <Form.Builder
            ref={formRef}
            fields={fields}
            autosubmit={false}
            withActions={false}
          />
        </div>
      )}
    </div>
  );
};

const ActionButton = ({ action, parentRef, store, formRef }) => {
  const isDeleteAction = action.id.includes("delete");
  const hasChildren = !!action.children?.length;
  const submenuRef = useRef();

  const onClick = useCallback(
    (e) => {
      e.preventDefault();
      if (action.disabled) return;
      action?.callback
        ? action?.callback(store.currentView?.selected?.snapshot, action)
        : invokeAction(action, isDeleteAction, store, formRef);
      parentRef?.current?.close?.();
    },
    [
      store.currentView?.selected,
      action,
      isDeleteAction,
      parentRef,
      store,
      formRef,
    ]
  );

  const titleContainer = (
    <Menu.Item
      key={action.id}
      className={cn("actionButton dm-toolbar-button")
        .mod({
          hasSeperator: isDeleteAction,
          hasSubMenu: action.children?.length > 0,
          isSeparator: action.isSeparator,
          isTitle: action.isTitle,
          danger: isDeleteAction,
          disabled: action.disabled,
        })
        .toClassName()}
      size="small"
      onClick={onClick}
      aria-label={action.title}
      style={
        action.isTitle
          ? menuTitleStyle
          : action.isSeparator
            ? separatorStyle
            : menuItemStyle
      }
    >
      <div
        className={cn("actionButton").elem("titleContainer").toClassName()}
        {...(action.disabled ? { title: action.disabledReason } : {})}
        style={{
          display: "flex",
          alignItems: "center",
          gap: "8px",
          justifyContent: "space-between",
        }}
      >
        <div style={{ flexGrow: 1 }}>{action.title}</div>
        {hasChildren ? <IconChevronRight style={{ opacity: 0.7 }} /> : null}
      </div>
    </Menu.Item>
  );

  if (hasChildren) {
    return (
      <Dropdown.Trigger
        key={action.id}
        align="top-right-outside"
        toggle={false}
        ref={submenuRef}
        content={
          <ul style={{ margin: 0, padding: 0, listStyle: "none" }}>
            {action.children.map((childAction) => (
              <ActionButton
                key={childAction.id}
                action={childAction}
                parentRef={parentRef}
                store={store}
                formRef={formRef}
              />
            ))}
          </ul>
        }
      >
        {titleContainer}
      </Dropdown.Trigger>
    );
  }

  return (
    <Tooltip
      key={action.id}
      title={action.disabled_reason}
      disabled={!action.disabled}
      alignment="bottom-center"
    >
      <div>
        <Menu.Item
          size="small"
          key={action.id}
          variant={isDeleteAction ? "negative" : undefined}
          onClick={onClick}
          icon={isDeleteAction && <IconTrash />}
          title={action.disabled ? action.disabledReason : null}
          aria-label={action.title}
          style={
            action.isSeparator
              ? separatorStyle
              : action.isTitle
              ? menuTitleStyle
              : menuItemStyle
          }
        >
          {action.title}
        </Menu.Item>
      </div>
    </Tooltip>
  );
};

const TaskDeleteModal = ({ store, onConfirm, onCancel }) => {
  const [refundInfo, setRefundInfo] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchRefundInfo = async () => {
      setLoading(true);
      setError(null);

      try {
        // Get selected task IDs
        const selectedTasks = Array.from(store.currentView?.selected?.list || []);
        
        if (selectedTasks.length === 0) {
          setError("No tasks selected");
          setLoading(false);
          return;
        }

        // Call API to get refund information
        const response = await store.apiCall("calculateDeletionRefund", {}, {
          project_id: store.project.id,
          task_ids: selectedTasks,
        });

        if (response?.success) {
          setRefundInfo(response);
        } else {
          setError(response?.error || "Failed to calculate refund");
        }
      } catch (err) {
        console.error("Error calculating deletion refund:", err);
        setError(err.message || "Failed to calculate refund");
      } finally {
        setLoading(false);
      }
    };

    fetchRefundInfo();
  }, [store]);

  return (
    <div style={{
      position: "fixed",
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      background: "rgba(0, 0, 0, 0.85)",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      zIndex: 10000,
    }}>
      <div style={{
        background: "#0a0a0a",
        border: "1px solid #1f2937",
        borderRadius: "8px",
        padding: "32px",
        maxWidth: "520px",
        width: "90%",
        position: "relative",
      }}>
        {/* Corner accents */}
        <div style={{
          position: 'absolute',
          top: '-1px',
          left: '-1px',
          width: '20px',
          height: '20px',
          borderTop: '2px solid #8b5cf6',
          borderLeft: '2px solid #8b5cf6'
        }} />
        <div style={{
          position: 'absolute',
          bottom: '-1px',
          right: '-1px',
          width: '20px',
          height: '20px',
          borderBottom: '2px solid #8b5cf6',
          borderRight: '2px solid #8b5cf6'
        }} />

        <h3 style={{
          marginBottom: '20px',
          color: '#ffffff',
          fontSize: '12px',
          fontWeight: 500,
          textTransform: 'uppercase',
          letterSpacing: '0.1em',
          fontFamily: 'ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace'
        }}>
          <span style={{ color: '#6b7280' }}>// </span>Delete selected tasks?
        </h3>

        {loading ? (
          <div style={{ display: "flex", alignItems: "center", gap: "16px", padding: "48px 24px", justifyContent: "center" }}>
            <Spinner size={24} />
            <span style={{
              color: '#6b7280',
              fontSize: '12px',
              textTransform: 'uppercase',
              letterSpacing: '0.1em',
              fontFamily: 'ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace'
            }}>
              Calculating refund...
            </span>
          </div>
        ) : error ? (
          <div style={{
            background: "rgba(239, 68, 68, 0.1)",
            border: "1px solid rgba(239, 68, 68, 0.3)",
            borderRadius: "6px",
            padding: "16px",
            color: "#fca5a5",
            marginBottom: "24px",
            fontSize: "13px",
          }}>
            {error}
          </div>
        ) : refundInfo ? (
          <>
            {/* Warning message */}
            <div style={{
              background: "rgba(251, 191, 36, 0.1)",
              border: "1px solid rgba(251, 191, 36, 0.3)",
              borderRadius: "6px",
              padding: "16px",
              marginBottom: "24px",
              color: "#fbbf24",
              fontSize: "13px",
            }}>
              You are about to delete {refundInfo.tasks_total} task{refundInfo.tasks_total > 1 ? 's' : ''}. This action cannot be undone.
            </div>

            {/* Tasks breakdown */}
            {refundInfo.tasks_with_annotations > 0 && (
              <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                padding: '16px 0',
                borderBottom: '1px solid #1f2937'
              }}>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                  <span style={{ color: '#e8e4d9', fontSize: '13px' }}>Tasks with Annotations</span>
                  <span style={{
                    color: '#6b7280',
                    fontSize: '11px',
                    letterSpacing: '0.02em'
                  }}>
                    No refund (work was done)
                  </span>
                </div>
                <span style={{
                  fontWeight: 600,
                  color: '#ef4444',
                  fontFamily: 'ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace',
                  fontSize: '16px'
                }}>
                  {refundInfo.tasks_with_annotations}
                </span>
              </div>
            )}

            {refundInfo.tasks_refundable > 0 && (
              <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                padding: '16px 0',
                borderBottom: '1px solid #1f2937'
              }}>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                  <span style={{ color: '#e8e4d9', fontSize: '13px' }}>Unannotated Tasks</span>
                  <span style={{
                    color: '#6b7280',
                    fontSize: '11px',
                    letterSpacing: '0.02em'
                  }}>
                    {refundInfo.tasks_refundable} × {refundInfo.cost_per_task} credits
                  </span>
                </div>
                <span style={{
                  fontWeight: 600,
                  color: '#10b981',
                  fontFamily: 'ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace',
                  fontSize: '16px'
                }}>
                  {refundInfo.tasks_refundable}
                </span>
              </div>
            )}

            {/* Refund amount */}
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              padding: '24px 0',
              background: refundInfo.refund_amount > 0 ? 'rgba(16, 185, 129, 0.05)' : 'rgba(239, 68, 68, 0.05)',
              margin: '0 -32px',
              paddingLeft: '32px',
              paddingRight: '32px',
            }}>
              <span style={{
                color: '#ffffff',
                fontSize: '14px',
                fontWeight: 600,
                letterSpacing: '0.05em'
              }}>
                {refundInfo.refund_amount > 0 ? 'REFUND AMOUNT' : 'NO REFUND'}
              </span>
              <span style={{
                fontWeight: 700,
                color: refundInfo.refund_amount > 0 ? '#10b981' : '#ef4444',
                fontFamily: 'ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace',
                fontSize: '20px'
              }}>
                {refundInfo.refund_amount > 0 ? `${Math.round(refundInfo.refund_amount)} credits` : '0 credits'}
              </span>
            </div>
          </>
        ) : null}

        {/* Action buttons */}
        <div style={{ display: "flex", gap: "12px", justifyContent: "flex-end", marginTop: "24px" }}>
          <button
            onClick={onCancel}
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: "6px",
              padding: "0 20px",
              height: "40px",
              minWidth: "90px",
              background: "rgba(239, 68, 68, 0.12)",
              border: "1px solid rgba(239, 68, 68, 0.3)",
              color: "#fca5a5",
              fontSize: "13px",
              fontWeight: 600,
              fontFamily: "'Space Grotesk', system-ui, sans-serif",
              cursor: "pointer",
              transition: "all 0.2s ease",
              borderRadius: "6px",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = "rgba(239, 68, 68, 0.2)";
              e.currentTarget.style.borderColor = "rgba(239, 68, 68, 0.5)";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = "rgba(239, 68, 68, 0.12)";
              e.currentTarget.style.borderColor = "rgba(239, 68, 68, 0.3)";
            }}
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            disabled={loading || error}
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: "6px",
              padding: "0 16px",
              height: "40px",
              minWidth: "90px",
              background: "#ef4444",
              border: "1px solid #ef4444",
              color: "#ffffff",
              fontSize: "13px",
              fontWeight: 600,
              fontFamily: "'Space Grotesk', system-ui, sans-serif",
              cursor: (loading || error) ? "not-allowed" : "pointer",
              opacity: (loading || error) ? 0.5 : 1,
              transition: "all 0.2s ease",
              borderRadius: "6px",
            }}
            onMouseEnter={(e) => {
              if (!loading && !error) {
                e.currentTarget.style.background = "#dc2626";
                e.currentTarget.style.borderColor = "#dc2626";
                e.currentTarget.style.transform = "translateY(-1px)";
                e.currentTarget.style.boxShadow = "0 4px 12px rgba(239, 68, 68, 0.4)";
              }
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = "#ef4444";
              e.currentTarget.style.borderColor = "#ef4444";
              e.currentTarget.style.transform = "translateY(0)";
              e.currentTarget.style.boxShadow = "none";
            }}
          >
            Delete Tasks
          </button>
        </div>
      </div>
    </div>
  );
};

const invokeAction = (action, destructive, store, formRef) => {
  // Special handling for delete_tasks action
  if (action.id === "delete_tasks") {
    const modalContainer = document.createElement("div");
    document.body.appendChild(modalContainer);

    const handleConfirm = () => {
      document.body.removeChild(modalContainer);
      store.SDK.invoke("actionDialogOk", action.id, {});
      store.invokeAction(action.id, {});
    };

    const handleCancel = () => {
      document.body.removeChild(modalContainer);
    };

    const root = createRoot(modalContainer);
    root.render(
      <TaskDeleteModal
        store={store}
        onConfirm={handleConfirm}
        onCancel={handleCancel}
      />
    );
    return;
  }

  if (action.dialog) {
    const { type: dialogType, text, form, title } = action.dialog;
    const dialog = Modal[dialogType] ?? Modal.confirm;

    // Generate dynamic content for destructive actions
    let dialogTitle = title;
    let dialogText = text;
    let okButtonText = "OK";

    if (destructive && !title) {
      // Extract object type from action ID and title
      const objectMap = {
        delete_tasks: "tasks",
        delete_annotations: "annotations",
        delete_predictions: "predictions",
        delete_reviews: "reviews",
        delete_reviewers: "review assignments",
        delete_annotators: "annotator assignments",
        delete_ground_truths: "ground truths",
      };

      const objectType =
        objectMap[action.id] ||
        action.title.toLowerCase().replace("delete ", "");
      dialogTitle = `Delete selected ${objectType}?`;

      // Convert to title case for button text
      const titleCaseObject = objectType
        .split(" ")
        .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
        .join(" ");
      okButtonText = `Delete ${titleCaseObject}`;
    }

    if (destructive && !form) {
      // Use standardized warning message for simple delete actions
      const objectType = dialogTitle
        ? dialogTitle.replace("Delete selected ", "").replace("?", "")
        : "items";
      dialogText = `You are about to delete the selected ${objectType}.\n\nThis can't be undone.`;
    }

    dialog({
      title: dialogTitle
        ? dialogTitle
        : destructive
        ? "Destructive action"
        : "Confirm action",
      body: (
        <DialogContent
          text={dialogText}
          form={form}
          formRef={formRef}
          store={store}
          action={action}
        />
      ),
      buttonLook: destructive ? "negative" : "primary",
      okText: destructive ? okButtonText : undefined,
      onOk() {
        const body = formRef.current?.assembleFormData({ asJSON: true });

        store.SDK.invoke("actionDialogOk", action.id, { body });
        store.invokeAction(action.id, { body });
      },
      closeOnClickOutside: false,
    });
  } else {
    store.invokeAction(action.id);
  }
};

export const ActionsButton = injector(
  observer(({ store, size, hasSelected, ...rest }) => {
    const formRef = useRef();
    const selectedCount = store.currentView.selectedCount;
    const [isOpen, setIsOpen] = useState(false);
    const [isHovered, setIsHovered] = useState(false);

    // Use TanStack Query hook for fetching actions
    const {
      actions: serverActions,
      isLoading,
      isFetching,
    } = useActions({
      enabled: isOpen,
      projectId: store.SDK.projectId,
    });

    const actions = useMemo(() => {
      return [...store.availableActions, ...serverActions]
        .filter((a) => !a.hidden)
        .sort((a, b) => a.order - b.order);
    }, [store.availableActions, serverActions]);
    const actionButtons = actions.map((action) => (
      <ActionButton
        key={action.id}
        action={action}
        parentRef={formRef}
        store={store}
        formRef={formRef}
      />
    ));
    const recordTypeLabel =
      isFFLOPSE3 && store.SDK.type === "DE" ? "Record" : "Task";

    return (
      <Dropdown.Trigger
        content={
          <Menu size="compact">
            {isLoading || isFetching ? (
              <Menu.Item data-testid="loading-actions" disabled>
                Loading actions...
              </Menu.Item>
            ) : (
              actionButtons
            )}
          </Menu>
        }
        openUpwardForShortViewport={false}
        disabled={!hasSelected}
        onToggle={setIsOpen}
      >
        <button
          disabled={!hasSelected}
          aria-label="Tasks Actions"
          onMouseEnter={() => setIsHovered(true)}
          onMouseLeave={() => setIsHovered(false)}
          style={{
            background: 'black',
            border: `1px solid ${isHovered && hasSelected ? 'rgba(139, 92, 246, 0.5)' : 'rgba(55, 65, 81, 0.5)'}`,
            borderRadius: '10px',
            color: '#c4b5fd',
            fontWeight: 600,
            fontSize: '13px',
            height: '32px',
            padding: '0 14px',
            cursor: hasSelected ? 'pointer' : 'not-allowed',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '6px',
            opacity: hasSelected ? 1 : 0.5,
            fontFamily: "'Space Grotesk', system-ui, -apple-system, sans-serif",
            transition: 'all 0.15s ease',
            boxShadow: isHovered && hasSelected ? '0 0 12px rgba(139, 92, 246, 0.15)' : 'none',
          }}
        >
          {selectedCount > 0
            ? `${selectedCount} ${recordTypeLabel}${
                selectedCount > 1 ? "s" : ""
              }`
            : "Actions"}
          <IconChevronDown style={{ width: 16, height: 16 }} />
        </button>
      </Dropdown.Trigger>
    );
  })
);
