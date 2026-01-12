import { Callout, CalloutContent, CalloutHeader, CalloutIcon, CalloutTitle } from "@synapse/ui/lib/callout/callout";
import { IconWarning } from "@synapse/icons";
import { atomWithMutation, atomWithQuery, queryClientAtom } from "jotai-tanstack-query";
import { useAtomValue } from "jotai";
import clsx from "clsx";
import { useCallback, useEffect, useMemo, useState } from "react";
import { format } from "date-fns";
import { useCopyText } from "@synapse/core";
import styles from "./PersonalJWTToken.module.scss";
import { Button } from "@synapse/ui";

/**
 * FIXME: This is legacy imports. We're not supposed to use such statements
 * each one of these eventually has to be migrated to core/ui
 */
import { getApiInstance } from "@synapse/core";
import { modal, confirm } from "@synapse/ui/lib/modal";
import { Input, Label } from "apps/synapse/src/components/Form/Elements";
import { Tooltip } from "@synapse/ui";

type Token = {
  token: string;
  expires_at: string;
};

const ACCESS_TOKENS_QUERY_KEY = ["access-tokens"];

// list all existing API tokens
const tokensListAtom = atomWithQuery(() => ({
  queryKey: ACCESS_TOKENS_QUERY_KEY,
  async queryFn() {
    const api = getApiInstance();
    const tokens = await api.invoke("accessTokenList");
    if (!tokens.$meta.ok) {
      console.error(token.error);
      return [];
    }

    return tokens as Token[];
  },
}));

// despite the name, gets user's access token
const refreshTokenAtom = atomWithMutation((get) => {
  const queryClient = get(queryClientAtom);
  return {
    mutationKey: ["refresh-token"],
    async mutationFn() {
      const api = getApiInstance();
      const token = await api.invoke("accessTokenGetRefreshToken");
      if (!token.$meta.ok) {
        console.error(token.error);
        return "";
      }
      return token.token;
    },
    onSettled() {
      queryClient.invalidateQueries({ queryKey: ACCESS_TOKENS_QUERY_KEY });
    },
  };
});

const revokeTokenAtom = atomWithMutation((get) => {
  const queryClient = get(queryClientAtom);
  return {
    mutationKey: ["revoke"],
    async mutationFn({ token }: { token: string }) {
      const api = getApiInstance();
      await api.invoke("accessTokenRevoke", null, {
        params: {},
        body: {
          refresh: token,
        },
      });
    },
    // Optimistic update
    async onMutate({ token }: { token: string }) {
      // Cancel all ongoing queries so we can override the data they hold
      await queryClient.cancelQueries({ queryKey: ACCESS_TOKENS_QUERY_KEY });
      // Getting currently cached data of a specific query
      const previousTokens = queryClient.getQueryData(ACCESS_TOKENS_QUERY_KEY) as Token[];
      // We need to keep everything but one token that we just deleted
      const filtered = previousTokens.filter((t) => t.token !== token);
      // We now optimistically override data inside the query
      queryClient.setQueryData(ACCESS_TOKENS_QUERY_KEY, (old: Token[]) => filtered as Token[]);
      return { previousTokens };
    },
    onError: (err, newTodo, context) => {
      // If error, reset query to its previous state (without changes from `onMutate`)
      queryClient.setQueryData(ACCESS_TOKENS_QUERY_KEY, context?.previousTokens);
    },
    onSettled() {
      // Reload query from remote if deletion went ok
      queryClient.invalidateQueries({
        queryKey: ACCESS_TOKENS_QUERY_KEY,
      });
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

export function PersonalJWTToken() {
  const [dialogOpened, setDialogOpened] = useState(false);
  const tokens = useAtomValue(tokensListAtom);
  const revokeToken = useAtomValue(revokeTokenAtom);
  const createToken = useAtomValue(refreshTokenAtom);
  const queryClient = useAtomValue(queryClientAtom);

  const revoke = useCallback(
    async (token: string) => {
      confirm({
        title: "Revoke Token",
        body: `Are you sure you want to delete this access token? Any application using this token will need a new token to be able to access ${
          window?.APP_SETTINGS?.app_name || "Synapse"
        }`,
        okText: "Revoke",
        buttonLook: "negative",
        onOk: async () => {
          await revokeToken.mutateAsync({ token });
        },
      });
    },
    [revokeToken],
  );

  const disallowAddingTokens = useMemo(() => {
    return createToken.isPending || tokens.isLoading || (tokens.data?.length ?? 0) > 0;
  }, [createToken.isPending, tokens.isLoading, tokens.data]);

  function openDialog() {
    if (dialogOpened) return;
    setDialogOpened(true);
    modal({
      visible: true,
      title: "New Auth Token",
      style: { width: 680 },
      body: CreateTokenForm,
      closeOnClickOutside: false,
      onHidden: () => {
        setDialogOpened(false);
        queryClient.invalidateQueries({ queryKey: ACCESS_TOKENS_QUERY_KEY });
      },
    });
  }

  return (
    <div className={styles.personalAccessToken}>
      {/* Tokens List */}
      {tokens.isLoading ? (
        <div 
          style={{ 
            padding: '20px', 
            color: '#6b7280', 
            fontFamily: 'monospace',
            background: 'rgba(255, 255, 255, 0.02)',
            border: '1px solid #1f1f1f',
          }}
        >
          Loading tokens...
        </div>
      ) : tokens.isSuccess && tokens.data && tokens.data.length ? (
        <div
          style={{
            padding: '20px',
            background: 'rgba(255, 255, 255, 0.02)',
            border: '1px solid #1f1f1f',
            marginBottom: '1.5rem',
          }}
        >
          <StyledLabel text="Active Tokens" />
          <div className="flex flex-col gap-3">
            {tokens.data.map((token, index) => (
              <div
                key={`${token.expires_at}${index}`}
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'minmax(0, 1fr) auto',
                  gap: '1rem',
                  alignItems: 'center',
                  padding: '16px',
                  background: 'rgba(139, 92, 246, 0.05)',
                  border: '1px solid rgba(139, 92, 246, 0.15)',
                }}
              >
                <div>
                  <div
                    style={{
                      fontSize: '12px',
                      color: '#8b5cf6',
                      marginBottom: '6px',
                      fontFamily: 'monospace',
                    }}
                  >
                    {token.expires_at
                      ? `Expires on ${format(new Date(token.expires_at), "MMM dd, yyyy HH:mm")}`
                      : "Personal access token"}
                  </div>
                  <div
                    style={{
                      fontFamily: 'monospace',
                      fontSize: '13px',
                      color: '#fff',
                      opacity: 0.6,
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap',
                    }}
                  >
                    {token.token}
                  </div>
                </div>
                <Button
                  variant="negative"
                  look="outlined"
                  onClick={() => revoke(token.token)}
                  style={{
                    borderRadius: 0,
                    textTransform: 'uppercase',
                    letterSpacing: '0.1em',
                    fontSize: '11px',
                  }}
                >
                  Revoke
                </Button>
              </div>
            ))}
          </div>
        </div>
      ) : tokens.isError ? (
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
          Unable to load tokens list
        </div>
      ) : null}

      {/* Create Token Button */}
      <Tooltip title="You can only have one active token" disabled={!disallowAddingTokens}>
        <div style={{ width: "max-content" }}>
          <Button
            disabled={disallowAddingTokens || dialogOpened}
            onClick={openDialog}
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
            Create New Token
          </Button>
        </div>
      </Tooltip>
    </div>
  );
}

function CreateTokenForm() {
  const { data, mutate: createToken } = useAtomValue(refreshTokenAtom);
  const [copy, copied] = useCopyText({ defaultText: data ?? "" });

  useEffect(() => {
    createToken();
  }, []);

  return (
    <div className="flex flex-col gap-4">
      <p style={{ color: '#6b7280', fontFamily: 'monospace', fontSize: '14px', margin: 0 }}>
        Copy your new access token from below and keep it secure.
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
            <StyledLabel text="Access Token" />
            <input
              readOnly
              value={data ?? ""}
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
            {copied ? "Copied!" : "Copy"}
          </Button>
        </div>
      </div>

      {data?.expires_at && (
        <div style={{ fontFamily: 'monospace', fontSize: '13px', color: '#6b7280' }}>
          <span style={{ color: '#9ca3af' }}>Expires: </span>
          {format(new Date(data?.expires_at), "MMM dd, yyyy HH:mm z")}
        </div>
      )}

      <Callout variant="warning">
        <CalloutHeader>
          <CalloutIcon>
            <IconWarning />
          </CalloutIcon>
          <CalloutTitle>Manage your access tokens securely</CalloutTitle>
        </CalloutHeader>
        <CalloutContent>
          Do not share this key with anyone. If you suspect any keys have been compromised, you should revoke them and
          create new ones.
        </CalloutContent>
      </Callout>
    </div>
  );
}

