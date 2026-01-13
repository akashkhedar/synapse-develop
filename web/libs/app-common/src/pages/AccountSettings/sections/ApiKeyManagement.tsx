import { Callout, CalloutContent, CalloutHeader, CalloutIcon, CalloutTitle } from "@synapse/ui/lib/callout/callout";
import { IconWarning, IconFileCopy, IconPlus, IconTrash, IconRefresh } from "@synapse/icons";
import { atomWithMutation, atomWithQuery, queryClientAtom } from "jotai-tanstack-query";
import { useAtomValue } from "jotai";
import { useCallback, useState } from "react";
import { format } from "date-fns";
import { useCopyText } from "@synapse/core";
import { Button, Tooltip } from "@synapse/ui";
import { getApiInstance } from "@synapse/core";
import { modal, confirm } from "@synapse/ui/lib/modal";
import styles from "./PersonalJWTToken.module.scss";

type APIKey = {
  id: number;
  name: string;
  description: string;
  key?: string;
  key_prefix: string;
  is_active: boolean;
  last_used_at: string | null;
  expires_at: string | null;
  created_at: string;
  updated_at: string;
};

const API_KEYS_QUERY_KEY = ["api-keys"];

// List all existing API keys
const apiKeysListAtom = atomWithQuery(() => ({
  queryKey: API_KEYS_QUERY_KEY,
  async queryFn() {
    const api = getApiInstance();
    const keys = await api.invoke("apiKeysList");
    if (!keys.$meta.ok) {
      console.error(keys.error);
      return [];
    }
    return keys as unknown as APIKey[];
  },
}));

// Create a new API key
const createApiKeyAtom = atomWithMutation((get) => {
  const queryClient = get(queryClientAtom);
  return {
    mutationKey: ["create-api-key"],
    async mutationFn({ name, description }: { name: string; description?: string }) {
      const api = getApiInstance();
      const key = await api.invoke("apiKeysCreate", undefined, {
        body: { name, description: description || "" },
      });
      if (!key.$meta.ok) {
        throw new Error(key.error);
      }
      return key as unknown as APIKey;
    },
    onSettled() {
      queryClient.invalidateQueries({ queryKey: API_KEYS_QUERY_KEY });
    },
  };
});

// Delete an API key
const deleteApiKeyAtom = atomWithMutation((get) => {
  const queryClient = get(queryClientAtom);
  return {
    mutationKey: ["delete-api-key"],
    async mutationFn({ id }: { id: number }) {
      const api = getApiInstance();
      await api.invoke("apiKeysDelete", { id });
    },
    async onMutate({ id }: { id: number }) {
      await queryClient.cancelQueries({ queryKey: API_KEYS_QUERY_KEY });
      const previousKeys = queryClient.getQueryData(API_KEYS_QUERY_KEY) as APIKey[];
      const filtered = previousKeys.filter((k) => k.id !== id);
      queryClient.setQueryData(API_KEYS_QUERY_KEY, filtered);
      return { previousKeys };
    },
    onError: (err, vars, context) => {
      queryClient.setQueryData(API_KEYS_QUERY_KEY, context?.previousKeys);
    },
    onSettled() {
      queryClient.invalidateQueries({ queryKey: API_KEYS_QUERY_KEY });
    },
  };
});

// Regenerate an API key
const regenerateApiKeyAtom = atomWithMutation((get) => {
  const queryClient = get(queryClientAtom);
  return {
    mutationKey: ["regenerate-api-key"],
    async mutationFn({ id }: { id: number }) {
      const api = getApiInstance();
      const key = await api.invoke("apiKeysRegenerate", { id });
      if (!key.$meta.ok) {
        throw new Error(key.error);
      }
      return key as unknown as APIKey;
    },
    onSettled() {
      queryClient.invalidateQueries({ queryKey: API_KEYS_QUERY_KEY });
    },
  };
});

// Styled label component
const StyledLabel = ({ text }: { text: string }) => (
  <div
    style={{
      fontSize: '12px',
      fontWeight: 500,
      color: '#9ca3af',
      textTransform: 'uppercase',
      letterSpacing: '0.1em',
      marginBottom: '10px',
      fontFamily: 'monospace',
    }}
  >
    {text}
  </div>
);

export function ApiKeyManagement() {
  const [dialogOpened, setDialogOpened] = useState(false);
  const apiKeys = useAtomValue(apiKeysListAtom);
  const deleteApiKey = useAtomValue(deleteApiKeyAtom);
  const regenerateApiKey = useAtomValue(regenerateApiKeyAtom);
  const queryClient = useAtomValue(queryClientAtom);

  const handleDelete = useCallback(
    async (apiKey: APIKey) => {
      confirm({
        title: "Delete API Key",
        body: `Are you sure you want to delete the API key "${apiKey.name}"? Any applications using this key will no longer be able to access Synapse.`,
        okText: "Delete",
        buttonLook: "negative",
        onOk: async () => {
          await deleteApiKey.mutateAsync({ id: apiKey.id });
        },
      });
    },
    [deleteApiKey],
  );

  const handleRegenerate = useCallback(
    async (apiKey: APIKey) => {
      confirm({
        title: "Regenerate API Key",
        body: `Are you sure you want to regenerate the API key "${apiKey.name}"? The old key will be invalidated immediately.`,
        okText: "Regenerate",
        buttonLook: "negative",
        onOk: async () => {
          const result = await regenerateApiKey.mutateAsync({ id: apiKey.id });
          // Show the new key in a modal
          modal({
            visible: true,
            title: "New API Key Generated",
            style: { width: 680 },
            body: () => <ShowNewKeyModal apiKey={result} />,
            closeOnClickOutside: false,
          });
        },
      });
    },
    [regenerateApiKey],
  );

  function openCreateDialog() {
    if (dialogOpened) return;
    setDialogOpened(true);
    modal({
      visible: true,
      title: "Create New API Key",
      style: { width: 680 },
      body: CreateApiKeyForm,
      closeOnClickOutside: false,
      onHidden: () => {
        setDialogOpened(false);
        queryClient.invalidateQueries({ queryKey: API_KEYS_QUERY_KEY });
      },
    });
  }

  return (
    <div className={styles.personalAccessToken}>
      {/* Info Section */}
      <div
        style={{
          padding: '16px 20px',
          background: 'rgba(139, 92, 246, 0.05)',
          border: '1px solid rgba(139, 92, 246, 0.15)',
          marginBottom: '1.5rem',
          fontFamily: 'monospace',
          fontSize: '13px',
          color: '#9ca3af',
        }}
      >
        <strong style={{ color: '#8b5cf6' }}>SDK API Keys</strong> — API keys are used to authenticate with the Synapse SDK and API. 
        Each key provides full access to your account. Keep your API keys secure and never share them publicly.
      </div>

      {/* API Keys List */}
      {apiKeys.isLoading ? (
        <div 
          style={{ 
            padding: '20px', 
            color: '#6b7280', 
            fontFamily: 'monospace',
            background: 'rgba(255, 255, 255, 0.02)',
            border: '1px solid #1f1f1f',
          }}
        >
          Loading API keys...
        </div>
      ) : apiKeys.isSuccess && apiKeys.data && apiKeys.data.length > 0 ? (
        <div
          style={{
            padding: '20px',
            background: 'rgba(255, 255, 255, 0.02)',
            border: '1px solid #1f1f1f',
            marginBottom: '1.5rem',
          }}
        >
          <StyledLabel text="Your API Keys" />
          <div className="flex flex-col gap-3">
            {apiKeys.data.map((apiKey) => (
              <div
                key={apiKey.id}
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'minmax(0, 1fr) auto',
                  gap: '1rem',
                  alignItems: 'center',
                  padding: '16px',
                  background: apiKey.is_active 
                    ? 'rgba(139, 92, 246, 0.05)' 
                    : 'rgba(100, 100, 100, 0.05)',
                  border: apiKey.is_active 
                    ? '1px solid rgba(139, 92, 246, 0.15)' 
                    : '1px solid rgba(100, 100, 100, 0.15)',
                  opacity: apiKey.is_active ? 1 : 0.6,
                }}
              >
                <div>
                  <div
                    style={{
                      fontSize: '14px',
                      fontWeight: 600,
                      color: '#fff',
                      marginBottom: '4px',
                    }}
                  >
                    {apiKey.name}
                    {!apiKey.is_active && (
                      <span style={{ color: '#ef4444', fontSize: '12px', marginLeft: '8px' }}>
                        (Inactive)
                      </span>
                    )}
                  </div>
                  <div
                    style={{
                      fontFamily: 'monospace',
                      fontSize: '13px',
                      color: '#8b5cf6',
                      marginBottom: '4px',
                    }}
                  >
                    {apiKey.key_prefix}••••••••
                  </div>
                  <div
                    style={{
                      fontSize: '11px',
                      color: '#6b7280',
                      fontFamily: 'monospace',
                    }}
                  >
                    Created: {format(new Date(apiKey.created_at), "MMM dd, yyyy")}
                    {apiKey.last_used_at && (
                      <> • Last used: {format(new Date(apiKey.last_used_at), "MMM dd, yyyy HH:mm")}</>
                    )}
                    {apiKey.expires_at && (
                      <> • Expires: {format(new Date(apiKey.expires_at), "MMM dd, yyyy")}</>
                    )}
                  </div>
                  {apiKey.description && (
                    <div
                      style={{
                        fontSize: '12px',
                        color: '#9ca3af',
                        marginTop: '6px',
                      }}
                    >
                      {apiKey.description}
                    </div>
                  )}
                </div>
                <div className="flex gap-2">
                  <Tooltip title="Regenerate Key">
                    <Button
                      variant="neutral"
                      look="outlined"
                      onClick={() => handleRegenerate(apiKey)}
                      style={{
                        borderRadius: 0,
                        padding: '8px 12px',
                      }}
                    >
                      <IconRefresh style={{ width: 14, height: 14 }} />
                    </Button>
                  </Tooltip>
                  <Tooltip title="Delete Key">
                    <Button
                      variant="negative"
                      look="outlined"
                      onClick={() => handleDelete(apiKey)}
                      style={{
                        borderRadius: 0,
                        padding: '8px 12px',
                      }}
                    >
                      <IconTrash style={{ width: 14, height: 14 }} />
                    </Button>
                  </Tooltip>
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : apiKeys.isError ? (
        <div
          style={{
            padding: '20px',
            background: 'rgba(239, 68, 68, 0.1)',
            border: '1px solid rgba(239, 68, 68, 0.2)',
            color: '#f87171',
            fontFamily: 'monospace',
            marginBottom: '1.5rem',
          }}
        >
          Unable to load API keys
        </div>
      ) : (
        <div
          style={{
            padding: '20px',
            background: 'rgba(255, 255, 255, 0.02)',
            border: '1px solid #1f1f1f',
            marginBottom: '1.5rem',
            color: '#6b7280',
            fontFamily: 'monospace',
            textAlign: 'center',
          }}
        >
          No API keys yet. Create your first API key to get started with the SDK.
        </div>
      )}

      {/* Create API Key Button */}
      <Button
        disabled={dialogOpened}
        onClick={openCreateDialog}
        style={{
          background: '#e8e4d9',
          color: '#000',
          borderRadius: 0,
          padding: '14px 28px',
          textTransform: 'uppercase',
          letterSpacing: '0.15em',
          fontSize: '13px',
          fontWeight: 600,
          border: 'none',
        }}
      >
        <span className="flex items-center gap-2">
          <IconPlus style={{ width: 16, height: 16 }} />
          Create New API Key
        </span>
      </Button>

      {/* SDK Usage Example */}
      <div
        style={{
          marginTop: '2rem',
          padding: '20px',
          background: 'rgba(139, 92, 246, 0.05)',
          border: '1px solid rgba(139, 92, 246, 0.15)',
        }}
      >
        <StyledLabel text="SDK Usage Example" />
        <pre
          style={{
            background: 'rgba(0, 0, 0, 0.3)',
            padding: '16px',
            fontFamily: 'monospace',
            fontSize: '13px',
            color: '#e5e7eb',
            overflow: 'auto',
            margin: 0,
          }}
        >
{`from synapse_sdk import Synapse

# Initialize the client with your API key
client = Synapse(api_key="syn_your_api_key_here")

# List your projects
projects = client.projects.list()
for project in projects:
    print(project.title)`}
        </pre>
      </div>
    </div>
  );
}

function CreateApiKeyForm() {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [createdKey, setCreatedKey] = useState<APIKey | null>(null);
  const createApiKey = useAtomValue(createApiKeyAtom);
  const [copy, copied] = useCopyText({ defaultText: createdKey?.key ?? "" });

  const handleCreate = async () => {
    if (!name.trim()) return;
    
    try {
      const result = await createApiKey.mutateAsync({ 
        name: name.trim(), 
        description: description.trim() 
      });
      setCreatedKey(result);
    } catch (error) {
      console.error("Failed to create API key:", error);
    }
  };

  if (createdKey) {
    return (
      <div className="flex flex-col gap-4">
        <p style={{ color: '#10b981', fontFamily: 'monospace', fontSize: '14px', margin: 0 }}>
          ✓ API key created successfully! Copy it now - you won't be able to see the full key again.
        </p>

        <div
          style={{
            padding: '16px',
            background: 'rgba(139, 92, 246, 0.05)',
            border: '1px solid rgba(139, 92, 246, 0.15)',
          }}
        >
          <div className="flex items-end w-full gap-3">
            <div className="flex-1">
              <StyledLabel text="Your New API Key" />
              <input
                readOnly
                value={createdKey.key ?? ""}
                style={{
                  width: '100%',
                  background: 'transparent',
                  border: '1px solid #1f1f1f',
                  color: '#fff',
                  padding: '14px 16px',
                  fontSize: '13px',
                  fontFamily: 'monospace',
                }}
              />
            </div>
            <Button
              onClick={() => copy()}
              disabled={copied}
              variant="neutral"
              look="outlined"
              style={{
                borderRadius: 0,
                textTransform: 'uppercase',
                letterSpacing: '0.1em',
                fontSize: '11px',
              }}
            >
              <span className="flex items-center gap-2">
                <IconFileCopy style={{ width: 14, height: 14 }} />
                {copied ? "Copied!" : "Copy"}
              </span>
            </Button>
          </div>
        </div>

        <Callout variant="warning">
          <CalloutHeader>
            <CalloutIcon>
              <IconWarning />
            </CalloutIcon>
            <CalloutTitle>Save your API key now</CalloutTitle>
          </CalloutHeader>
          <CalloutContent>
            This is the only time you'll see the complete API key. Store it securely - 
            if you lose it, you'll need to regenerate a new key.
          </CalloutContent>
        </Callout>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-4">
      <div>
        <StyledLabel text="Key Name *" />
        <input
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="e.g., Production SDK, CI/CD Pipeline"
          style={{
            width: '100%',
            background: 'transparent',
            border: '1px solid #1f1f1f',
            color: '#fff',
            padding: '14px 16px',
            fontSize: '14px',
          }}
        />
      </div>

      <div>
        <StyledLabel text="Description (optional)" />
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="What will this API key be used for?"
          style={{
            width: '100%',
            background: 'transparent',
            border: '1px solid #1f1f1f',
            color: '#fff',
            padding: '14px 16px',
            fontSize: '14px',
            minHeight: '80px',
            resize: 'vertical',
          }}
        />
      </div>

      <Button
        onClick={handleCreate}
        disabled={!name.trim() || createApiKey.isPending}
        style={{
          background: '#e8e4d9',
          color: '#000',
          borderRadius: 0,
          padding: '14px 28px',
          textTransform: 'uppercase',
          letterSpacing: '0.15em',
          fontSize: '13px',
          fontWeight: 600,
          border: 'none',
          width: 'fit-content',
        }}
      >
        {createApiKey.isPending ? "Creating..." : "Create API Key"}
      </Button>
    </div>
  );
}

function ShowNewKeyModal({ apiKey }: { apiKey: APIKey }) {
  const [copy, copied] = useCopyText({ defaultText: apiKey.key ?? "" });

  return (
    <div className="flex flex-col gap-4">
      <p style={{ color: '#10b981', fontFamily: 'monospace', fontSize: '14px', margin: 0 }}>
        ✓ API key regenerated! Copy the new key now.
      </p>

      <div
        style={{
          padding: '16px',
          background: 'rgba(139, 92, 246, 0.05)',
          border: '1px solid rgba(139, 92, 246, 0.15)',
        }}
      >
        <div className="flex items-end w-full gap-3">
          <div className="flex-1">
            <StyledLabel text="New API Key" />
            <input
              readOnly
              value={apiKey.key ?? ""}
              style={{
                width: '100%',
                background: 'transparent',
                border: '1px solid #1f1f1f',
                color: '#fff',
                padding: '14px 16px',
                fontSize: '13px',
                fontFamily: 'monospace',
              }}
            />
          </div>
          <Button
            onClick={() => copy()}
            disabled={copied}
            variant="neutral"
            look="outlined"
            style={{
              borderRadius: 0,
              textTransform: 'uppercase',
              letterSpacing: '0.1em',
              fontSize: '11px',
            }}
          >
            <span className="flex items-center gap-2">
              <IconFileCopy style={{ width: 14, height: 14 }} />
              {copied ? "Copied!" : "Copy"}
            </span>
          </Button>
        </div>
      </div>

      <Callout variant="warning">
        <CalloutHeader>
          <CalloutIcon>
            <IconWarning />
          </CalloutIcon>
          <CalloutTitle>The old key has been invalidated</CalloutTitle>
        </CalloutHeader>
        <CalloutContent>
          Update your applications with this new key. The previous key will no longer work.
        </CalloutContent>
      </Callout>
    </div>
  );
}

export function ApiKeyDescription() {
  return (
    <span style={{ fontFamily: 'monospace', color: '#6b7280' }}>
      Create and manage API keys for SDK and programmatic access to Synapse.
    </span>
  );
}
