import { useCopyText } from "@synapse/core";
import { Button, IconFileCopy, IconLaunch, Label, Typography } from "@synapse/ui";
/**
 * FIXME: This is legacy imports. We're not supposed to use such statements
 * each one of these eventually has to be migrated to core/ui
 */
import { Input, TextArea } from "apps/synapse/src/components/Form";
import { atom, useAtomValue } from "jotai";
import { atomWithMutation, atomWithQuery } from "jotai-tanstack-query";
import styles from "./PersonalAccessToken.module.scss";

const tokenAtom = atomWithQuery(() => ({
  queryKey: ["access-token"],
  queryFn: async () => {
    const result = await fetch("/api/current-user/token");
    return result.json();
  },
}));

const resetTokenAtom = atomWithMutation(() => ({
  mutationKey: ["reset-token"],
  mutationFn: async () => {
    const result = await fetch("/api/current-user/reset-token", {
      method: "post",
    });
    return result.json();
  },
}));

const currentTokenAtom = atom((get) => {
  const initialToken = get(tokenAtom).data?.token;
  const resetToken = get(resetTokenAtom).data?.token;

  return resetToken ?? initialToken;
});

const curlStringAtom = atom((get) => {
  const currentToken = get(currentTokenAtom);
  const curlString = `curl -X GET ${location.origin}/api/projects/ -H 'Authorization: Token ${currentToken}'`;
  return curlString;
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

// Styled button matching landing page
const ActionButton = ({ 
  children, 
  onClick, 
  disabled, 
  variant = 'primary' 
}: { 
  children: React.ReactNode; 
  onClick: () => void; 
  disabled?: boolean;
  variant?: 'primary' | 'negative';
}) => (
  <Button
    onClick={onClick}
    disabled={disabled}
    variant={variant === 'negative' ? 'negative' : 'neutral'}
    look="outlined"
    style={{
      borderRadius: 0,
      textTransform: 'uppercase',
      letterSpacing: '0.1em',
      fontSize: '11px',
      padding: '12px 20px',
      border: variant === 'negative' ? '1px solid rgba(239, 68, 68, 0.3)' : '1px solid #1f1f1f',
    }}
  >
    {children}
  </Button>
);

export const PersonalAccessToken = () => {
  const token = useAtomValue(currentTokenAtom);
  const reset = useAtomValue(resetTokenAtom);
  const curl = useAtomValue(curlStringAtom);
  const [copyToken, tokenCopied] = useCopyText({ defaultText: token });
  const [copyCurl, curlCopied] = useCopyText({ defaultText: curl });

  return (
    <div id="personal-access-token">
      <div className="flex flex-col gap-6">
        {/* Access Token Section */}
        <div
          style={{
            padding: '20px',
            background: 'rgba(255, 255, 255, 0.02)',
            border: '1px solid #1f1f1f',
          }}
        >
          <StyledLabel text="Access Token" />
          <div className="flex gap-3 w-full items-center">
            <input
              name="token"
              readOnly
              value={token ?? ""}
              style={{
                flex: 1,
                background: 'transparent',
                border: '1px solid #1f1f1f',
                color: '#fff',
                padding: '14px 16px',
                fontSize: '14px',
                fontFamily: 'monospace',
              }}
            />
            <ActionButton onClick={() => copyToken()} disabled={tokenCopied}>
              <span className="flex items-center gap-2">
                <IconFileCopy style={{ width: 14, height: 14 }} />
                {tokenCopied ? "Copied!" : "Copy"}
              </span>
            </ActionButton>
            <ActionButton onClick={() => reset.mutate()} variant="negative">
              Reset
            </ActionButton>
          </div>
        </div>

        {/* CURL Example Section */}
        <div
          style={{
            padding: '20px',
            background: 'rgba(139, 92, 246, 0.05)',
            border: '1px solid rgba(139, 92, 246, 0.15)',
          }}
        >
          <StyledLabel text="Example CURL Request" />
          <div className="flex gap-3 w-full items-start">
            <textarea
              name="example-curl"
              readOnly
              value={curl ?? ""}
              style={{
                flex: 1,
                background: 'transparent',
                border: '1px solid #1f1f1f',
                color: '#fff',
                padding: '14px 16px',
                fontSize: '13px',
                fontFamily: 'monospace',
                minHeight: '80px',
                resize: 'none',
              }}
            />
            <ActionButton onClick={() => copyCurl()} disabled={curlCopied}>
              <span className="flex items-center gap-2">
                <IconFileCopy style={{ width: 14, height: 14 }} />
                {curlCopied ? "Copied!" : "Copy"}
              </span>
            </ActionButton>
          </div>
        </div>
      </div>
    </div>
  );
};

export function PersonalAccessTokenDescription() {
  return (
    <span style={{ fontFamily: 'monospace', color: '#6b7280' }}>
      Authenticate with our API using your personal access token.
      {!window.APP_SETTINGS?.whitelabel_is_active && (
        <>
          {" "}
          See{" "}
          <a 
            href="https://synapse.io/guide/api.html" 
            target="_blank" 
            rel="noreferrer" 
            style={{ 
              color: '#8b5cf6', 
              textDecoration: 'none',
              display: 'inline-flex',
              alignItems: 'center',
              gap: '4px',
            }}
          >
            Documentation
            <IconLaunch style={{ width: 14, height: 14 }} />
          </a>
        </>
      )}
    </span>
  );
}

