import { useMemo, useState, useCallback } from "react";
import { useHistory } from "react-router";
import { Button, Typography, useToast } from "@synapse/ui";
import { useUpdatePageTitle, createTitleFromSegments } from "@synapse/core";
import { Label } from "../../components/Form";
import { modal } from "../../components/Modal/Modal";
import { useModalControls } from "../../components/Modal/ModalPopup";
import Input from "../../components/Form/Elements/Input/Input";
import { Space } from "../../components/Space/Space";
import { Spinner } from "../../components/Spinner/Spinner";
import { useAPI } from "../../providers/ApiProvider";
import { useProject } from "../../providers/ProjectProvider";
import { cn } from "../../utils/bem";
import "./DangerZone.scss";
import { Form, TextArea } from "../../components/Form";

// Severity indicators for warnings - no emojis, dark theme
const severityConfig = {
  critical: { label: "CRITICAL", color: "#f87171", bgColor: "rgba(239, 68, 68, 0.1)" },
  high: { label: "HIGH", color: "#fb923c", bgColor: "rgba(251, 146, 60, 0.1)" },
  medium: { label: "MEDIUM", color: "#fbbf24", bgColor: "rgba(251, 191, 36, 0.1)" },
  low: { label: "LOW", color: "#60a5fa", bgColor: "rgba(96, 165, 250, 0.1)" },
  info: { label: "INFO", color: "#9ca3af", bgColor: "rgba(156, 163, 175, 0.1)" },
};

const primaryButtonStyle = {
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  gap: "6px",
  padding: "0 16px",
  height: "40px",
  minWidth: "90px",
  background: "#8b5cf6",
  border: "1px solid #8b5cf6",
  color: "#ffffff",
  fontSize: "13px",
  fontWeight: 600,
  fontFamily: "'Space Grotesk', system-ui, sans-serif",
  cursor: "pointer",
  transition: "all 0.2s ease",
};

const dangerButtonStyle = {
  ...primaryButtonStyle,
  background: "rgba(239, 68, 68, 0.12)",
  border: "1px solid rgba(239, 68, 68, 0.3)",
  color: "#fca5a5",
};

const outlineButtonStyle = {
  ...primaryButtonStyle,
  background: "transparent",
  color: "#8b5cf6",
};

export const DangerZone = () => {
  const { project } = useProject();
  const api = useAPI();
  const history = useHistory();
  const toast = useToast();
  const [processing, setProcessing] = useState(null);
  const [loadingWarnings, setLoadingWarnings] = useState(false);

  useUpdatePageTitle(createTitleFromSegments([project?.title, "Danger Zone"]));

  // Fetch deletion warnings from the API
  const fetchDeletionWarnings = useCallback(async () => {
    if (!project?.id) return null;

    try {
      const response = await fetch(
        `/api/billing/project-billing/deletion_warnings/?project_id=${project.id}`,
        {
          method: "GET",
          headers: {
            "Content-Type": "application/json",
          },
          credentials: "include",
        }
      );

      if (!response.ok) {
        console.warn("Failed to fetch deletion warnings");
        return null;
      }

      return await response.json();
    } catch (error) {
      console.error("Error fetching deletion warnings:", error);
      return null;
    }
  }, [project?.id]);

  // Render warning item
  const WarningItem = ({ warning }) => {
    const config = severityConfig[warning.severity] || severityConfig.info;

    return (
      <div
        className="deletion-warning-item"
        style={{
          backgroundColor: config.bgColor,
          borderLeft: `3px solid ${config.color}`,
          borderRadius: "0",
          padding: "12px 16px",
          marginBottom: "8px",
        }}
      >
        <div className="warning-header" style={{ display: "flex", alignItems: "center", gap: "12px", marginBottom: "8px" }}>
          <span
            className="warning-severity"
            style={{
              backgroundColor: config.color,
              color: "#000000",
              padding: "4px 10px",
              borderRadius: "0",
              fontSize: "10px",
              fontWeight: "700",
              letterSpacing: "0.08em",
              textTransform: "uppercase",
              fontFamily: "'Space Grotesk', system-ui, sans-serif",
            }}
          >
            {config.label}
          </span>
          <span className="warning-title" style={{ color: config.color, fontWeight: "600", fontFamily: "'Space Grotesk', system-ui, sans-serif" }}>
            {warning.title}
          </span>
        </div>
        <p className="warning-message" style={{ margin: "0", color: "#d1d5db", fontSize: "14px" }}>{warning.message}</p>
        {warning.action_suggested && (
          <p className="warning-action" style={{ margin: "8px 0 0", color: "#a78bfa", fontSize: "13px" }}>
            <strong>Suggested:</strong> {warning.action_suggested}
          </p>
        )}
      </div>
    );
  };

  const showDangerConfirmation = ({
    title,
    message,
    requiredWord,
    buttonText,
    onConfirm,
    warnings = [],
    summary = null,
    refundBreakdown = null,
  }) => {
    const isDev = process.env.NODE_ENV === "development";
    const hasUnexportedWork = summary?.has_unexported_work || false;
    const hasCriticalWarnings = warnings.some((w) => w.severity === "critical");

    return modal({
      title,
      width: 700,
      allowClose: false,
      body: () => {
        const ctrl = useModalControls();
        const inputValue = ctrl?.state?.inputValue || "";
        const isDeleting = ctrl?.state?.isDeleting || false;

        return (
          <div className="danger-zone-modal-body">
            {/* Warnings Section */}
            {warnings.length > 0 && (
              <div className="deletion-warnings-container">
                <Typography variant="title" size="medium" className="mb-tight" style={{ color: "#fbbf24" }}>
                  Please Review Before Deleting
                </Typography>

                {/* Summary stats */}
                {summary && (
                  <div className="deletion-summary">
                    <div className="summary-stat">
                      <span className="stat-value">{summary.task_count}</span>
                      <span className="stat-label">Tasks</span>
                    </div>
                    <div className="summary-stat">
                      <span className="stat-value">
                        {summary.annotation_count}
                      </span>
                      <span className="stat-label">Annotations</span>
                    </div>
                    {summary.refund_estimate > 0 && (
                      <div className="summary-stat refund">
                        <span className="stat-value">
                          ₹{summary.refund_estimate.toFixed(0)}
                        </span>
                        <span className="stat-label">Est. Refund</span>
                      </div>
                    )}
                  </div>
                )}

                {/* Refund Breakdown */}
                {refundBreakdown && refundBreakdown.deposit_paid > 0 && (
                  <div className="refund-breakdown">
                    <Typography
                      variant="title"
                      size="small"
                      className="mb-tight"
                      style={{ color: "#4ade80" }}
                    >
                      Credit Refund Breakdown
                    </Typography>

                    {/* Work percentage and threshold info */}
                    {typeof refundBreakdown.work_done_percentage !== 'undefined' && (
                      <div className="work-percentage-info" style={{
                        background: "rgba(139, 92, 246, 0.1)",
                        border: "1px solid rgba(139, 92, 246, 0.3)",
                        padding: "12px 16px",
                        marginBottom: "16px",
                        borderRadius: "0",
                      }}>
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
                          <span style={{ color: "#a78bfa", fontSize: "13px", fontWeight: "600" }}>
                            Work Completion
                          </span>
                          <span style={{ 
                            color: refundBreakdown.meets_threshold ? "#fbbf24" : "#4ade80",
                            fontSize: "16px",
                            fontWeight: "700",
                            fontFamily: "'Space Mono', monospace"
                          }}>
                            {refundBreakdown.work_done_percentage.toFixed(1)}%
                          </span>
                        </div>
                        <div style={{ 
                          fontSize: "12px", 
                          color: "#9ca3af",
                          fontFamily: "'Space Grotesk', system-ui, sans-serif"
                        }}>
                          {refundBreakdown.meets_threshold ? (
                            <>
                              Work exceeds 30% threshold. Only unannotated tasks will be refunded.
                            </>
                          ) : (
                            <>
                              Work below 30% threshold. Base fee, buffer, and unannotated tasks will be refunded.
                            </>
                          )}
                        </div>
                      </div>
                    )}

                    <div className="breakdown-table">
                      <div className="breakdown-row">
                        <span className="breakdown-label">
                          Project Expenditure Paid:
                        </span>
                        <span className="breakdown-value">
                          ₹{refundBreakdown.deposit_paid.toFixed(0)}
                        </span>
                      </div>

                      {/* Show base fee refund if below threshold */}
                      {refundBreakdown.base_fee_refund > 0 && (
                        <div className="breakdown-row refund">
                          <span className="breakdown-label">
                            Base Fee Refund:
                          </span>
                          <span className="breakdown-value" style={{ color: "#4ade80" }}>
                            + ₹{refundBreakdown.base_fee_refund.toFixed(0)}
                          </span>
                        </div>
                      )}

                      {/* Show buffer refund if below threshold */}
                      {refundBreakdown.buffer_refund > 0 && (
                        <div className="breakdown-row refund">
                          <span className="breakdown-label">
                            Buffer Refund (20%):
                          </span>
                          <span className="breakdown-value" style={{ color: "#4ade80" }}>
                            + ₹{refundBreakdown.buffer_refund.toFixed(0)}
                          </span>
                        </div>
                      )}

                      {/* Show unannotated tasks refund */}
                      {refundBreakdown.unannotated_tasks_refund > 0 && (
                        <div className="breakdown-row refund">
                          <span className="breakdown-label">
                            Unannotated Tasks Refund:
                          </span>
                          <span className="breakdown-value" style={{ color: "#4ade80" }}>
                            + ₹{refundBreakdown.unannotated_tasks_refund.toFixed(0)}
                          </span>
                        </div>
                      )}

                      {refundBreakdown.annotation_cost > 0 && (
                        <div className="breakdown-row deduction">
                          <span className="breakdown-label">
                            Annotated Tasks Cost:
                          </span>
                          <span className="breakdown-value">
                            - ₹{refundBreakdown.annotation_cost.toFixed(0)}
                          </span>
                        </div>
                      )}
                      {refundBreakdown.credits_consumed > 0 && (
                        <div className="breakdown-row deduction">
                          <span className="breakdown-label">
                            Other Credits Used:
                          </span>
                          <span className="breakdown-value">
                            - ₹{refundBreakdown.credits_consumed.toFixed(0)}
                          </span>
                        </div>
                      )}
                      <div className="breakdown-row total">
                        <span className="breakdown-label">Total Refund:</span>
                        <span className="breakdown-value refund-amount">
                          ₹{refundBreakdown.refund_amount.toFixed(0)}
                        </span>
                      </div>
                    </div>
                  </div>
                )}

                <div className="warnings-list">
                  {warnings.map((warning, index) => (
                    <WarningItem key={index} warning={warning} />
                  ))}
                </div>

                {/* Export button if unexported work */}
                {hasUnexportedWork && (
                  <div className="export-suggestion">
                    <button
                      style={primaryButtonStyle}
                      onClick={() => {
                        ctrl?.hide();
                        history.push(
                          `/projects/${project?.id}/data?dialog=export`
                        );
                      }}
                    >
                      Export Data First 
                    </button>
                  </div>
                )}
              </div>
            )}

            {/* Original message */}
            <Typography
              variant="body"
              size="medium"
              className="mb-tight deletion-main-message"
            >
              {message}
            </Typography>

            {hasCriticalWarnings && (
              <div className="critical-warning-banner" style={{
                background: "rgba(239, 68, 68, 0.1)",
                border: "1px solid rgba(239, 68, 68, 0.3)",
                padding: "12px 16px",
                borderRadius: "0",
                marginBottom: "16px",
                color: "#f87171",
              }}>
                <strong>Critical warnings detected!</strong> Please ensure
                you understand the consequences before proceeding.
              </div>
            )}

            <TextArea
              label={`To proceed, type "${requiredWord}" in the field below:`}
              value={inputValue}
              onChange={(e) => ctrl?.setState({ inputValue: e.target.value })}
              data-testid="danger-zone-confirmation-input"
              autoComplete="off"
              style={{
                width: "100%",
                fontFamily: "'Space Grotesk', system-ui, sans-serif",
                background: "rgba(0, 0, 0, 0.2)",
                border: "1px solid #374151",
                color: "#ffffff",
                // minHeight: "42px",
                outline: "none",
                boxShadow: "none",
              }}
              onFocus={(e) => {
                e.currentTarget.style.borderColor = "#8b5cf6";
                e.currentTarget.style.boxShadow = "0 0 0 3px rgba(139, 92, 246, 0.1)";
              }}
              onBlur={(e) => {
                e.currentTarget.style.borderColor = "#374151";
                e.currentTarget.style.boxShadow = "none";
              }}
            />
          </div>
        );
      },
      footer: () => {
        const ctrl = useModalControls();
        const inputValue = (ctrl?.state?.inputValue || "").trim().toLowerCase();
        const isValid = isDev || inputValue === requiredWord.toLowerCase();
        const isDeleting = ctrl?.state?.isDeleting || false;

        return (
          <Space align="end">
            <button
              style={outlineButtonStyle}
              onClick={() => ctrl?.hide()}
              data-testid="danger-zone-cancel-button"
              disabled={isDeleting}
            >
              Cancel
            </button>
            <button
              style={{
                ...dangerButtonStyle,
                opacity: (isValid && !isDeleting) ? 1 : 0.5,
                cursor: (isValid && !isDeleting) ? "pointer" : "not-allowed",
              }}
              disabled={!isValid || isDeleting}
              onMouseEnter={(e) => {
                if (isValid && !isDeleting) {
                  e.currentTarget.style.background = "rgba(239, 68, 68, 0.2)";
                  e.currentTarget.style.borderColor = "rgba(239, 68, 68, 0.5)";
                }
              }}
              onMouseLeave={(e) => {
                if (isValid && !isDeleting) {
                  e.currentTarget.style.background = "rgba(239, 68, 68, 0.12)";
                  e.currentTarget.style.borderColor = "rgba(239, 68, 68, 0.3)";
                }
              }}
              onClick={async () => {
                if (isDeleting) return;
                ctrl?.setState({ isDeleting: true });
                try {
                  await onConfirm();
                  ctrl?.hide();
                } catch (error) {
                  ctrl?.setState({ isDeleting: false });
                  throw error;
                }
              }}
              data-testid="danger-zone-confirm-button"
            >
              {isDeleting ? "Deleting..." : buttonText}
            </button>
          </Space>
        );
      },
    });
  };

  const handleOnClick = (type) => async () => {
    // For project deletion, fetch warnings first
    if (type === "project") {
      setLoadingWarnings(true);

      try {
        const warningsData = await fetchDeletionWarnings();
        setLoadingWarnings(false);

        showDangerConfirmation({
          title: "Delete Project",
          message: (
            <>
              You are about to delete the project{" "}
              <strong>{project.title}</strong>. This action cannot be undone.
            </>
          ),
          requiredWord: "delete",
          buttonText: "Delete Project",
          warnings: warningsData?.warnings || [],
          summary: warningsData?.summary || null,
          refundBreakdown: warningsData?.refund_breakdown || null,
          onConfirm: async () => {
            setProcessing(type);
            try {
              const response = await api.callApi("deleteProject", {
                params: {
                  pk: project.id,
                },
              });

              // Build success message with refund info
              let successMessage = "Project deleted successfully!";

              if (response?.refund?.success) {
                const refundAmount = response.refund.amount || 0;
                const consumed = response.refund.consumed || 0;

                if (refundAmount > 0) {
                  successMessage = `Project deleted! ₹${refundAmount.toFixed(
                    0
                  )} credits have been refunded to your account.`;
                  if (consumed > 0) {
                    successMessage += ` (₹${consumed.toFixed(
                      0
                    )} were consumed for annotations)`;
                  }
                } else if (consumed > 0) {
                  successMessage = `Project deleted! All deposit credits (₹${consumed.toFixed(
                    0
                  )}) were consumed for annotations.`;
                }
              } else if (response?.refund?.error) {
                successMessage = `Project deleted, but refund could not be processed: ${response.refund.error}`;
              }

              toast.show({ message: successMessage });
              history.replace("/projects");
            } catch (error) {
              toast.show({ message: `Error: ${error.message}`, type: "error" });
            } finally {
              setProcessing(null);
            }
          },
        });
      } catch (error) {
        setLoadingWarnings(false);
        toast.show({
          message: `Error checking project status: ${error.message}`,
          type: "error",
        });
      }
      return;
    }

    // Other actions (non-project deletion)
    const actionConfig = {
      reset_cache: {
        title: "Reset Cache",
        message: (
          <>
            You are about to reset the cache for{" "}
            <strong>{project.title}</strong>. This action cannot be undone.
          </>
        ),
        requiredWord: "cache",
        buttonText: "Reset Cache",
      },
      tabs: {
        title: "Drop All Tabs",
        message: (
          <>
            You are about to drop all tabs for <strong>{project.title}</strong>.
            This action cannot be undone.
          </>
        ),
        requiredWord: "tabs",
        buttonText: "Drop All Tabs",
      },
    };

    const config = actionConfig[type];

    if (!config) {
      return;
    }

    showDangerConfirmation({
      ...config,
      onConfirm: async () => {
        setProcessing(type);
        try {
          if (type === "reset_cache") {
            await api.callApi("projectResetCache", {
              params: {
                pk: project.id,
              },
            });
            toast.show({ message: "Cache reset successfully" });
          } else if (type === "tabs") {
            await api.callApi("deleteTabs", {
              body: {
                project: project.id,
              },
            });
            toast.show({ message: "All tabs dropped successfully" });
          }
        } catch (error) {
          toast.show({ message: `Error: ${error.message}`, type: "error" });
        } finally {
          setProcessing(null);
        }
      },
    });
  };

  const buttons = useMemo(
    () => [
      {
        type: "annotations",
        disabled: true, //&& !project.total_annotations_number,
        label: `Delete ${project.total_annotations_number} Annotations`,
      },
      {
        type: "tasks",
        disabled: true, //&& !project.task_number,
        label: `Delete ${project.task_number} Tasks`,
      },
      {
        type: "predictions",
        disabled: true, //&& !project.total_predictions_number,
        label: `Delete ${project.total_predictions_number} Predictions`,
      },
      {
        type: "reset_cache",
        help:
          "Reset Cache may help in cases like if you are unable to modify the labeling configuration due " +
          "to validation errors concerning existing labels, but you are confident that the labels don't exist. You can " +
          "use this action to reset the cache and try again.",
        label: "Reset Cache",
      },
      {
        type: "tabs",
        help: "If the Data Manager is not loading, dropping all Data Manager tabs can help.",
        label: "Drop All Tabs",
      },
      {
        type: "project",
        help: "Deleting a project removes all tasks, annotations, and project data from the database. You will see a list of warnings before deletion if there are any issues.",
        label: "Delete Project",
      },
    ],
    [project]
  );

  return (
    <div className={cn("simple-settings")}>
      <Typography variant="headline" size="medium" className="mb-tighter">
        Danger Zone
      </Typography>
      <Typography
        variant="body"
        size="medium"
        className="text-neutral-content-subtler !mb-base"
      >
        Perform these actions at your own risk. Actions you take on this page
        can't be reverted. Make sure your data is backed up.
      </Typography>

      {project.id ? (
        <div style={{ marginTop: 16 }}>
          {buttons.map((btn) => {
            const waiting =
              processing === btn.type ||
              (btn.type === "project" && loadingWarnings);
            const disabled =
              btn.disabled || (processing && !waiting) || loadingWarnings;

            return (
              btn.disabled !== true && (
                <div className={cn("settings-wrapper")} key={btn.type}>
                  <Typography variant="title" size="large">
                    {btn.label}
                  </Typography>
                  {btn.help && (
                    <Label
                      description={btn.help}
                      style={{ width: 600, display: "block" }}
                    />
                  )}
                  <button
                    key={btn.type}
                    disabled={disabled}
                    onClick={handleOnClick(btn.type)}
                    style={{
                      ...dangerButtonStyle,
                      marginTop: 16,
                      opacity: disabled ? 0.6 : 1,
                      cursor: disabled ? 'not-allowed' : 'pointer',
                    }}
                    onMouseEnter={(e) => {
                      if (!disabled) {
                         e.currentTarget.style.background = "rgba(239, 68, 68, 0.2)";
                         e.currentTarget.style.borderColor = "rgba(239, 68, 68, 0.5)";
                      }
                    }}
                    onMouseLeave={(e) => {
                       if (!disabled) {
                          e.currentTarget.style.background = "rgba(239, 68, 68, 0.12)";
                          e.currentTarget.style.borderColor = "rgba(239, 68, 68, 0.3)";
                       }
                    }}
                  >
                    {btn.type === "project" && loadingWarnings
                      ? "Checking project status..."
                      : btn.label}
                  </button>
                </div>
              )
            );
          })}
        </div>
      ) : (
        <div
          style={{ display: "flex", justifyContent: "center", marginTop: 32 }}
        >
          <Spinner size={32} />
        </div>
      )}
    </div>
  );
};

DangerZone.title = "Danger Zone";
DangerZone.path = "/danger-zone";

