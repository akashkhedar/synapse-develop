import { IconCross, IconPlus } from "@synapse/icons";
import { Button, Typography } from "@synapse/ui";
import cloneDeep from "lodash/cloneDeep";
import { useEffect, useState } from "react";
import { Form, Input, Label, Toggle } from "../../components/Form";
import { useAPI } from "../../providers/ApiProvider";
import { cn } from "../../utils/bem";
import { useProject } from "../../providers/ProjectProvider";
import { WebhookDeleteModal } from "./WebhookDeleteModal";

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
      <div className="webhook-card">
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
      <div className="webhook-card">
        <div className="flex justify-between items-center mb-4">
          <h3 className="section-title !mb-0">Headers</h3>
          <Button
            type="button"
            variant="neutral"
            look="outlined"
            size="small"
            onClick={onAddHeaderClick}
            icon={<IconPlus />}
          >
            Add Header
          </Button>
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
                <Button
                  variant="negative"
                  look="string"
                  className="h-8 w-8 !p-0 flex items-center justify-center opacity-50 hover:opacity-100"
                  type="button"
                  icon={<IconCross />}
                  onClick={() => onHeaderRemove(index)}
                  tooltip="Remove"
                />
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Payload Section */}
      <div className="webhook-card">
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
          <Button
            type="button"
            variant="negative"
            look="outlined"
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
          </Button>
        ) : <div />} 

        <div className="flex items-center gap-3">
           <div className={rootClass.elem("status")}>
             <Form.Indicator />
           </div>
           <Button
            variant="neutral"
            look="outlined"
            type="button"
            onClick={onBack}
          >
            Cancel
          </Button>
          <Button
            className="gradient-button"
            aria-label={webhook === null ? "Add Webhook" : "Save Changes"}
          >
            {webhook === null ? "Add Webhook" : "Save Changes"}
          </Button>
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
    <>
      <header className="page-header flex items-center gap-2">
        <Typography
          as="a"
          variant="headline"
          size="medium"
          onClick={() => onSelectActive(null)}
          className="cursor-pointer text-neutral-content-subtler hover:text-neutral-content-subtle"
        >
          Webhooks
        </Typography>
        <Typography variant="headline" size="medium" className="text-neutral-content-subtler">
          / {webhook === null ? "New Webhook" : "Edit Webhook"}
        </Typography>
      </header>
      <div className="mt-base">
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
    </>
  );
};

export default WebhookDetail;

