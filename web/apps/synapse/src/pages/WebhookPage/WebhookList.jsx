import { IconCross, IconExternal, IconPencil, IconWebhook } from "@synapse/icons";
import { Button, EmptyState, SimpleCard, Typography } from "@synapse/ui";
import clsx from "clsx";
import { format } from "date-fns";
import { useCallback } from "react";
import { Toggle } from "../../components/Form";
import { useAPI } from "../../providers/ApiProvider";
import { WebhookDeleteModal } from "./WebhookDeleteModal";
import { ABILITY, useAuth } from "@synapse/core/providers/AuthProvider";
import "../Settings/settings.scss";
import { cn } from "../../utils/bem";

const WebhookListItem = ({ webhook, onSelectActive, onDelete, canChangeWebhooks }) => {
  return (
    <div className="webhook-list-item group">
      <div className="flex flex-col gap-1 overflow-hidden">
        <div className="flex items-center gap-3">
          <div className={`status-badge ${webhook.is_active ? "active" : "inactive"}`}>
            {webhook.is_active ? "Active" : "Inactive"}
          </div>
          <div
            className={clsx(
              "font-medium text-lg text-neutral-content truncate",
              canChangeWebhooks && "cursor-pointer hover:text-primary-link"
            )}
            onClick={canChangeWebhooks ? () => onSelectActive(webhook.id) : undefined}
          >
            {webhook.url}
          </div>
        </div>
        <div className="text-neutral-content-subtler text-sm pl-0">
          <span className="font-mono text-xs text-stone-500">
             // CREATED: {format(new Date(webhook.created_at), "yyyy-MM-dd HH:mm")}
          </span>
        </div>
      </div>

      {canChangeWebhooks && (
        <div className="flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
          <button 
            className="flex items-center justify-center px-3 py-1 gap-2 border border-violet-500/30 bg-violet-500/10 text-violet-400 hover:bg-violet-500/20 hover:text-violet-300 transition-all text-xs uppercase tracking-wider"
            onClick={() => onSelectActive(webhook.id)} 
          >
            <IconPencil style={{ width: 14, height: 14 }} /> Edit
          </button>
          <button
            className="flex items-center justify-center px-3 py-1 gap-2 border border-red-500/30 bg-red-500/10 text-red-400 hover:bg-red-500/20 hover:text-red-300 transition-all text-xs uppercase tracking-wider"
            onClick={() =>
              WebhookDeleteModal({
                onDelete,
              })
            }
          >
            <IconCross style={{ width: 14, height: 14 }} /> Delete
          </button>
        </div>
      )}
    </div>
  );
};

const WebhookList = ({ onSelectActive, onAddWebhook, webhooks, fetchWebhooks }) => {
  const api = useAPI();
  const { permissions } = useAuth();
  // PERMISSION BYPASS: Setting to true to debug/allow usage in this env
  const canChangeWebhooks = true; // permissions.can(ABILITY.can_change_webhooks);

  if (webhooks === null) return <></>;

  // Styles matching GeneralSettings button exactly
  const primaryButtonStyle = {
    minWidth: "150px", // Match General Settings width constraint
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

  const handleMouseEnter = (e) => {
    e.currentTarget.style.background = "linear-gradient(135deg, rgba(139, 92, 246, 0.3), rgba(168, 85, 247, 0.18))";
    e.currentTarget.style.borderColor = "rgba(139, 92, 246, 0.6)";
    e.currentTarget.style.color = "#ffffff";
    e.currentTarget.style.boxShadow = "0 4px 16px rgba(139, 92, 246, 0.25)";
  };

  const handleMouseLeave = (e) => {
    e.currentTarget.style.background = "linear-gradient(135deg, rgba(139, 92, 246, 0.2), rgba(168, 85, 247, 0.12))";
    e.currentTarget.style.borderColor = "rgba(139, 92, 246, 0.4)";
    e.currentTarget.style.color = "#c4b5fd";
    e.currentTarget.style.boxShadow = "none";
  };

  return (
    <div className={cn("webhook-settings").toClassName()}>
      <div className={cn("webhook-settings").elem("wrapper").toClassName()}>
        <h1>Webhooks</h1>

        <div className={cn("settings-wrapper").toClassName()}>
          {webhooks.length === 0 ? (
            <>
              <div className="settings-description mb-6">
                Setup integrations that subscribe to certain events. When an
                event is triggered, Synapse sends an HTTP POST request to the
                configured URL.
              </div>
            <div className="flex flex-col items-center justify-center text-center py-16">
              {/* Icon Container */}
              <div className="w-20 h-20 flex items-center justify-center mb-8 relative">
                <div className="absolute inset-0 bg-violet-500/10 rotate-45 border border-violet-500/30"></div>
                <IconWebhook className="text-violet-400 w-10 h-10 relative z-10" />
              </div>

              <h3 className="section-title mb-4 text-center">
                No Webhooks Configured
              </h3>

              <p className="text-neutral-content-subtler max-w-md mb-8 text-sm text-center">
                Add your first webhook to start integrating with external
                services.
              </p>

              {canChangeWebhooks ? (
                <button
                  style={primaryButtonStyle}
                  onMouseEnter={handleMouseEnter}
                  onMouseLeave={handleMouseLeave}
                  onClick={onAddWebhook}
                >
                  Add Webhook
                </button>
              ) 
              : (
                <Typography variant="body" size="small">
                  Contact your administrator to create Webhooks
                </Typography>
              )}
              </div>
              
              </>
          ) : (
            <>
              <div className="flex justify-between items-center mb-6 pb-4 border-b border-gray-800">
                <h3 className="section-title !mb-0">Active Integrations</h3>
                {canChangeWebhooks && (
                  <button
                    style={{
                      ...primaryButtonStyle,
                      height: "32px",
                      minWidth: "auto",
                      padding: "0 16px",
                      fontSize: "11px",
                    }}
                    onMouseEnter={handleMouseEnter}
                    onMouseLeave={handleMouseLeave}
                    onClick={onAddWebhook}
                  >
                    + Add Webhook
                  </button>
                )}
              </div>

              <div className="flex flex-col gap-0 w-full">
                {webhooks.map((obj) => (
                  <WebhookListItem
                    key={obj.id}
                    webhook={obj}
                    onSelectActive={onSelectActive}
                    onDelete={async () => {
                      await api.callApi("deleteWebhook", {
                        params: { pk: obj.id },
                      });
                      await fetchWebhooks();
                    }}
                    canChangeWebhooks={canChangeWebhooks}
                  />
                ))}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default WebhookList;

