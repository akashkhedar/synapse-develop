import { IconCross, IconExternal, IconPencil, IconWebhook } from "@synapse/icons";
import { Button, EmptyState, SimpleCard, Typography } from "@synapse/ui";
import clsx from "clsx";
import { format } from "date-fns";
import { useCallback } from "react";
import { Toggle } from "../../components/Form";
import { useAPI } from "../../providers/ApiProvider";
import { WebhookDeleteModal } from "./WebhookDeleteModal";
import { ABILITY, useAuth } from "@synapse/core/providers/AuthProvider";

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
        <div className="text-neutral-content-subtler text-sm pl-1">
          Created on {format(new Date(webhook.created_at), "MMM d, yyyy")} at {format(new Date(webhook.created_at), "h:mm a")}
        </div>
      </div>

      {canChangeWebhooks && (
        <div className="flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
          <Button 
            size="small" 
            variant="neutral" 
            look="outlined" 
            onClick={() => onSelectActive(webhook.id)} 
            icon={<IconPencil />}
          >
            Edit
          </Button>
          <Button
            size="small"
            variant="negative"
            look="outlined"
            onClick={() =>
              WebhookDeleteModal({
                onDelete,
              })
            }
            icon={<IconCross />}
          >
            Delete
          </Button>
        </div>
      )}
    </div>
  );
};

const WebhookList = ({ onSelectActive, onAddWebhook, webhooks, fetchWebhooks }) => {
  const api = useAPI();
  const { permissions } = useAuth();
  const canChangeWebhooks = permissions.can(ABILITY.can_change_webhooks);

  if (webhooks === null) return <></>;

  return (
    <>
      <header className="mb-8">
        <Typography variant="headline" size="medium" className="mb-2">
          Webhooks
        </Typography>
        {webhooks.length > 0 && (
          <Typography size="small" className="text-neutral-content-subtler max-w-2xl">
            Setup integrations that subscribe to certain events. When an event is triggered, Synapse sends an HTTP POST request to the configured URL.
          </Typography>
        )}
      </header>
      
      <div className="w-full">
        {webhooks.length === 0 ? (
          <div className="webhook-card flex flex-col items-center justify-center py-16 text-center">
             <div className="w-16 h-16 rounded-full bg-primary-background border border-primary-border flex items-center justify-center mb-6">
               <IconWebhook className="text-primary-link w-8 h-8" />
             </div>
             <h3 className="text-xl font-medium text-neutral-content mb-2">Add your first webhook</h3>
             <p className="text-neutral-content-subtler max-w-md mb-8">
               Setup integrations that subscribe to certain events using Webhooks.
             </p>
             {canChangeWebhooks ? (
               <Button className="gradient-button" onClick={onAddWebhook}>
                 Add Webhook
               </Button>
             ) : (
               <Typography variant="body" size="small">
                 Contact your administrator to create Webhooks
               </Typography>
             )}
          </div>
        ) : (
          <div className="webhook-card">
            <div className="flex justify-between items-center mb-6">
               <h3 className="section-title !mb-0">Active Integrations</h3>
               {canChangeWebhooks && (
                <Button className="gradient-button" onClick={onAddWebhook}>
                  Add Webhook
                </Button>
              )}
            </div>
            
            <div className="flex flex-col gap-3">
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
          </div>
        )}
      </div>
    </>
  );
};

export default WebhookList;

