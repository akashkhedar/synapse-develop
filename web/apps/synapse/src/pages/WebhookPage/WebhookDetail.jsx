import { IconCross, IconPlus } from "@synapse/icons";
import { Button, Typography } from "@synapse/ui";
import cloneDeep from "lodash/cloneDeep";
import { useEffect, useState } from "react";
import { Form, Input, Label, Toggle } from "../../components/Form";
import { useAPI } from "../../providers/ApiProvider";
import { cn } from "../../utils/bem";
import { useProject } from "../../providers/ProjectProvider";
import { WebhookDeleteModal } from "./WebhookDeleteModal";

// Button Styles matching GeneralSettings/WebhookList
const primaryButtonStyle = {
  minWidth: "150px",
  height: "44px",
  background: "linear-gradient(135deg, rgba(139, 92, 246, 0.2), rgba(168, 85, 247, 0.12))",
  border: "1px solid rgba(139, 92, 246, 0.4)",
  borderRadius: "0",
  color: "#c4b5fd",
  fontSize: "13px",
  fontWeight: "600",
  textTransform: "uppercase",
  letterSpacing: "0.05em",
  cursor: "pointer",
  transition: "all 0.2s cubic-bezier(0.4, 0, 0.2, 1)",
  fontFamily: "'Space Grotesk', system-ui, sans-serif",
  display: "inline-flex",
  alignItems: "center",
  justifyContent: "center",
};

const dangerButtonStyle = {
  ...primaryButtonStyle,
  background: "rgba(239, 68, 68, 0.1)",
  border: "1px solid rgba(239, 68, 68, 0.3)",
  color: "#fca5a5",
};

const neutralButtonStyle = {
  ...primaryButtonStyle,
  background: "transparent",
  border: "1px solid rgba(75, 85, 99, 0.5)",
  color: "#9ca3af",
};

const handleMouseEnter = (e, variant = "primary") => {
  if (variant === "primary") {
    e.currentTarget.style.background = "linear-gradient(135deg, rgba(139, 92, 246, 0.3), rgba(168, 85, 247, 0.18))";
    e.currentTarget.style.borderColor = "rgba(139, 92, 246, 0.6)";
    e.currentTarget.style.color = "#ffffff";
    e.currentTarget.style.boxShadow = "0 4px 16px rgba(139, 92, 246, 0.25)";
  } else if (variant === "danger") {
    e.currentTarget.style.background = "rgba(239, 68, 68, 0.18)";
    e.currentTarget.style.borderColor = "rgba(239, 68, 68, 0.5)";
    e.currentTarget.style.color = "#f87171";
    e.currentTarget.style.boxShadow = "0 4px 16px rgba(239, 68, 68, 0.2)";
  } else if (variant === "neutral") {
     e.currentTarget.style.borderColor = "rgba(139, 92, 246, 0.5)";
     e.currentTarget.style.color = "#c4b5fd";
  }
};

const handleMouseLeave = (e, variant = "primary") => {
  if (variant === "primary") {
    e.currentTarget.style.background = "linear-gradient(135deg, rgba(139, 92, 246, 0.2), rgba(168, 85, 247, 0.12))";
    e.currentTarget.style.borderColor = "rgba(139, 92, 246, 0.4)";
    e.currentTarget.style.color = "#c4b5fd";
    e.currentTarget.style.boxShadow = "none";
  } else if (variant === "danger") {
    e.currentTarget.style.background = "rgba(239, 68, 68, 0.1)";
    e.currentTarget.style.borderColor = "rgba(239, 68, 68, 0.3)";
    e.currentTarget.style.color = "#fca5a5";
    e.currentTarget.style.boxShadow = "none";
  } else if (variant === "neutral") {
    e.currentTarget.style.background = "transparent";
    e.currentTarget.style.borderColor = "rgba(75, 85, 99, 0.5)";
    e.currentTarget.style.color = "#9ca3af";
  }
};

const WebhookForm = ({
  webhook,
  webhooksInfo,
  fetchWebhooks,
  onSelectActive,
  onBack,
  projectId,
  headers,
  onAddHeaderClick,
  onHeaderRemove,
  onHeaderChange,
  sendForAllActions,
  setSendForAllActions,
  actions,
  onActionChange,
  isActive,
  setIsActive,
  sendPayload,
  setSendPayload,
  api,
  rootClass,
}) => {
  return (
    <Form
      action={webhook === null ? "createWebhook" : "updateWebhook"}
      params={webhook === null ? {} : { pk: webhook.id }}
      formData={webhook}
      prepareData={(data) => {
        return {
          ...data,
          project: projectId,
          send_for_all_actions: sendForAllActions,
          headers: Object.fromEntries(
            headers.filter((header) => header.key !== "").map((header) => [header.key, header.value]),
          ),
          actions: Array.from(actions),
          is_active: isActive,
          send_payload: sendPayload,
        };
      }}
      onSubmit={async (response) => {
        if (!response.error_message) {
          await fetchWebhooks();
          onSelectActive(null);
        }
      }}
      className="flex flex-col gap-6"
    >
      {/* General Section */}
      <div className={cn("settings-wrapper").toClassName()}>
        <h3 className="section-title">General Information</h3>
        <div className="grid grid-cols-[1fr_auto] gap-6 items-start">
          <Input 
            name="url" 
            label="Payload URL"
            placeholder="https://api.example.com/webhook" 
            className="w-full"
          />
          <div className="pt-8">
            <Toggle
              skip
              checked={isActive}
              onChange={(e) => setIsActive(e.target.checked)}
              label="Active"
            />
          </div>
        </div>
      </div>

      {/* Headers Section */}
      <div className={cn("settings-wrapper").toClassName()}>
        <div className="flex justify-between items-center mb-4">
          <h3 className="section-title !mb-0">Headers</h3>
          <button
            type="button"
            style={{...neutralButtonStyle, height: '32px', minWidth: 'auto', padding: '0 12px', fontSize: '11px'}}
            onMouseEnter={(e) => handleMouseEnter(e, "neutral")}
            onMouseLeave={(e) => handleMouseLeave(e, "neutral")}
            onClick={onAddHeaderClick}
            className="flex items-center gap-2"
          >
            <IconPlus style={{ width: 12, height: 12 }}/> Add Header
          </button>
        </div>
        
        {headers.length === 0 ? (
           <div className="text-neutral-content-subtler text-sm italic">No custom headers configured</div>
        ) : (
          <div className="space-y-3">
            {headers.map((header, index) => (
              <div key={header.id} className="grid grid-cols-[1fr_1fr_40px] gap-3 items-center">
                <Input
                  skip
                  placeholder="Key (e.g. Authorization)"
                  value={header.key}
                  onChange={(e) => onHeaderChange("key", e, index)}
                />
                <Input
                  skip
                  placeholder="Value"
                  value={header.value}
                  onChange={(e) => onHeaderChange("value", e, index)}
                />
                <button
                  type="button"
                  style={{
                    ...dangerButtonStyle, 
                    height: '32px', 
                    width: '32px', 
                    minWidth: 'auto', 
                    padding: 0,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center'
                  }}
                  onMouseEnter={(e) => handleMouseEnter(e, "danger")}
                  onMouseLeave={(e) => handleMouseLeave(e, "danger")}
                  onClick={() => onHeaderRemove(index)}
                  title="Remove"
                >
                  <IconCross style={{ width: 14, height: 14 }} />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Payload Section */}
      <div className={cn("settings-wrapper").toClassName()}>
        <h3 className="section-title">Events & Payload</h3>
        <div className="space-y-4">
          <Toggle
            skip
            checked={sendPayload}
            onChange={(e) => setSendPayload(e.target.checked)}
            label="Send Payload Data"
            description="Include full event data in the webhook request body"
          />
          
          <div className="border-t border-neutral-border pt-4 mt-4">
             <Toggle
              skip
              checked={sendForAllActions}
              label="Trigger on All Events"
              onChange={(e) => setSendForAllActions(e.target.checked)}
            />
            
            {!sendForAllActions && (
              <div className="mt-4 pl-4 border-l-2 border-primary-border bg-neutral-surface p-4 rounded-r-lg">
                <h4 className="text-sm font-medium text-neutral-content mb-3">Select Events</h4>
                <div className="grid grid-cols-2 gap-3">
                  {Object.entries(webhooksInfo).map(([key, value]) => (
                    <Toggle
                      key={key}
                      skip
                      name={key}
                      type="checkbox"
                      label={value.name}
                      onChange={onActionChange}
                      checked={actions.has(key)}
                    />
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Actions Footer */}
      <div className="flex items-center justify-between mt-4">
        {webhook !== null ? (
          <button
            type="button"
            style={dangerButtonStyle}
            onMouseEnter={(e) => handleMouseEnter(e, "danger")}
            onMouseLeave={(e) => handleMouseLeave(e, "danger")}
            onClick={() =>
              WebhookDeleteModal({
                onDelete: async () => {
                  await api.callApi("deleteWebhook", {
                    params: { pk: webhook.id },
                  });
                  onBack();
                  await fetchWebhooks();
                },
              })
            }
          >
            Delete Webhook
          </button>
        ) : <div />} 

        <div className="flex items-center gap-3">
           <div className={rootClass.elem("status")}>
             <Form.Indicator />
           </div>
           <button
            type="button"
            style={neutralButtonStyle}
            onMouseEnter={(e) => handleMouseEnter(e, "neutral")}
            onMouseLeave={(e) => handleMouseLeave(e, "neutral")}
            onClick={onBack}
          >
            Cancel
          </button>
          <button
            style={primaryButtonStyle}
            onMouseEnter={(e) => handleMouseEnter(e, "primary")}
            onMouseLeave={(e) => handleMouseLeave(e, "primary")}
          >
            {webhook === null ? "Add Webhook" : "Save Changes"}
          </button>
        </div>
      </div>
    </Form>
  );
};

const WebhookDetail = ({ webhook, webhooksInfo, fetchWebhooks, onBack, onSelectActive }) => {
  const rootClass = cn("webhook-detail");

  const api = useAPI();
  const [headers, setHeaders] = useState(
    webhook?.headers
      ? Object.entries(webhook.headers).map(([key, value], index) => ({
          id: `header-${Date.now()}-${index}`,
          key,
          value,
        }))
      : [],
  );
  const [sendForAllActions, setSendForAllActions] = useState(webhook ? webhook.send_for_all_actions : true);
  const [actions, setActions] = useState(new Set(webhook?.actions));
  const [isActive, setIsActive] = useState(webhook ? webhook.is_active : true);
  const [sendPayload, setSendPayload] = useState(webhook ? webhook.send_payload : true);

  const { project } = useProject();

  const [projectId, setProjectId] = useState(project.id);

  useEffect(() => {
    if (Object.keys(project).length === 0) {
      setProjectId(null);
    } else {
      setProjectId(project.id);
    }
  }, [project]);

  const onAddHeaderClick = () => {
    setHeaders([
      ...headers,
      {
        id: `header-${Date.now()}-${Math.random()}`,
        key: "",
        value: "",
      },
    ]);
  };
  const onHeaderRemove = (index) => {
    const newHeaders = cloneDeep(headers);

    newHeaders.splice(index, 1);
    setHeaders(newHeaders);
  };
  const onHeaderChange = (aim, event, index) => {
    const newHeaders = cloneDeep(headers);

    if (aim === "key") {
      newHeaders[index].key = event.target.value;
    }
    if (aim === "value") {
      newHeaders[index].value = event.target.value;
    }
    setHeaders(newHeaders);
  };

  const onActionChange = (event) => {
    const newActions = new Set(actions);

    if (event.target.checked) {
      newActions.add(event.target.name);
    } else {
      newActions.delete(event.target.name);
    }
    setActions(newActions);
  };

  useEffect(() => {
    if (webhook === null) {
      setHeaders([]);
      setSendForAllActions(true);
      setActions(new Set());
      setIsActive(true);
      setSendPayload(true);
      return;
    }
    setHeaders(
      Object.entries(webhook.headers).map(([key, value], index) => ({
        id: `header-${Date.now()}-${index}`,
        key,
        value,
      })),
    );
    setSendForAllActions(webhook.send_for_all_actions);
    setActions(new Set(webhook.actions));
    setIsActive(webhook.is_active);
    setSendPayload(webhook.send_payload);
  }, [webhook]);

  if (projectId === undefined) return <></>;

  return (
    <div className={cn("webhook-settings").toClassName()}>
      <div className={cn("webhook-settings").elem("wrapper").toClassName()}>
        <h1>{webhook === null ? "New Webhook" : "Edit Webhook"}</h1>
        <div className="settings-description mb-6">
           Configure the payload URL, secret headers, and trigger events for this webhook.
        </div>

        <WebhookForm
          webhook={webhook}
          webhooksInfo={webhooksInfo}
          fetchWebhooks={fetchWebhooks}
          onSelectActive={onSelectActive}
          onBack={onBack}
          projectId={projectId}
          headers={headers}
          onAddHeaderClick={onAddHeaderClick}
          onHeaderRemove={onHeaderRemove}
          onHeaderChange={onHeaderChange}
          sendForAllActions={sendForAllActions}
          setSendForAllActions={setSendForAllActions}
          actions={actions}
          onActionChange={onActionChange}
          isActive={isActive}
          setIsActive={setIsActive}
          sendPayload={sendPayload}
          setSendPayload={setSendPayload}
          api={api}
          rootClass={rootClass}
        />
      </div>
    </div>
  );
};

export default WebhookDetail;

