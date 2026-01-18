import { Button, Typography } from "@synapse/ui";
import { Space } from "@synapse/ui/lib/space/space";
import { cn } from "apps/synapse/src/utils/bem";
import { Modal } from "apps/synapse/src/components/Modal/ModalPopup";
import { API } from "apps/synapse/src/providers/ApiProvider";
import { useAtomValue } from "jotai";
import { atomWithQuery } from "jotai-tanstack-query";
import { useCallback, useEffect, useRef, useState } from "react";
import { Input } from "../../../components/Form";
import "./PeopleInvitation.scss";

const linkAtom = atomWithQuery(() => ({
  queryKey: ["invite-link"],
  async queryFn() {
    // called only once when the component is rendered on page reload
    // will also be reset when called `refetch()` on the Reset button
    const result = await API.invoke("resetInviteLink");
    return location.origin + result.response.invite_url;
  },
}));

export function InviteLink({
  opened,
  onOpened,
  onClosed,
}: {
  opened: boolean;
  onOpened?: () => void;
  onClosed?: () => void;
}) {
  const modalRef = useRef<Modal>(null);
  useEffect(() => {
    if (modalRef.current && opened) {
      modalRef.current?.show?.();
    } else if (modalRef.current && modalRef.current.visible) {
      modalRef.current?.hide?.();
    }
  }, [opened]);

  return (
    <Modal
      ref={modalRef}
      title="Invite Members"
      bareFooter={true}
      body={<InvitationModal />}
      footer={<InvitationFooter />}
      style={{ width: 560, height: 380 }}
      onHide={onClosed}
      onShow={onOpened}
    />
  );
}

const InvitationModal = () => {
  const { data: link, isPending, isError } = useAtomValue(linkAtom);
  
  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      fontFamily: "'Space Grotesk', system-ui, sans-serif",
    }}>
      <div style={{
        fontSize: '11px',
        fontWeight: 600,
        color: '#6b7280',
        textTransform: 'uppercase',
        letterSpacing: '0.05em',
        marginBottom: '16px',
      }}>
        Share this link with your team
      </div>
      <div style={{ marginBottom: '24px', position: 'relative' }}>
        <input
          type="text"
          value={link || ''}
          placeholder={isPending ? "Generating invite link..." : isError ? "Error generating link" : "No link available"}
          readOnly
          style={{
            width: '100%',
            padding: '14px 16px',
            background: 'rgba(0, 0, 0, 0.3)',
            border: '1px solid rgba(55, 65, 81, 0.5)',
            borderRadius: '8px',
            color: link ? '#ffffff' : '#9ca3af',
            fontSize: '13px',
            fontFamily: "'Space Grotesk', system-ui, sans-serif",
            outline: 'none',
            transition: 'all 0.2s ease',
            cursor: isPending ? 'wait' : 'default',
          }}
          onFocus={(e) => {
            if (!isPending && !isError) {
              e.currentTarget.style.borderColor = '#8b5cf6';
              e.currentTarget.style.backgroundColor = 'rgba(0, 0, 0, 0.5)';
              e.currentTarget.style.boxShadow = '0 0 0 4px rgba(139, 92, 246, 0.1)';
            }
          }}
          onBlur={(e) => {
            e.currentTarget.style.borderColor = 'rgba(55, 65, 81, 0.5)';
            e.currentTarget.style.backgroundColor = 'rgba(0, 0, 0, 0.3)';
            e.currentTarget.style.boxShadow = 'none';
          }}
        />
      </div>
      <p style={{
        fontSize: '13px',
        color: '#9ca3af',
        lineHeight: 1.6,
        margin: 0,
      }}>
        Invite members to join your Synapse instance. People that you invite have full access to all of your
        projects.{" "}
        <a
          href="https://synapse.io/guide/signup.html"
          target="_blank"
          rel="noreferrer"
          style={{
            color: '#c4b5fd',
            textDecoration: 'none',
            fontWeight: 500,
            transition: 'color 0.2s',
          }}
          onMouseEnter={(e) => e.currentTarget.style.color = '#a78bfa'}
          onMouseLeave={(e) => e.currentTarget.style.color = '#c4b5fd'}
          onClick={() =>
            __lsa("docs.organization.add_people.learn_more", {
              href: "https://synapse.io/guide/signup.html",
            })
          }
        >
          Learn more →
        </a>
      </p>
    </div>
  );
};

const InvitationFooter = () => {
  const { copyText, copied } = useTextCopy();
  const { refetch, data: link, isPending } = useAtomValue(linkAtom);

  return (
    <div style={{
      display: 'flex',
      justifyContent: 'flex-end',
      gap: '12px',
      paddingTop: '24px',
      borderTop: '1px solid rgba(55, 65, 81, 0.5)',
      marginTop: 'auto',
    }}>
      <button
        onClick={() => refetch()}
        disabled={isPending}
        aria-label="Refresh invite link"
        style={{
          background: 'black',
          border: '1px solid rgba(55, 65, 81, 0.5)',
          color: isPending ? '#4b5563' : '#9ca3af',
          padding: '0 16px',
          height: '36px',
          fontSize: '13px',
          fontWeight: 600,
          fontFamily: "'Space Grotesk', system-ui, sans-serif",
          borderRadius: '8px',
          cursor: isPending ? 'not-allowed' : 'pointer',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          transition: 'all 0.2s ease',
          opacity: isPending ? 0.7 : 1,
        }}
        onMouseEnter={(e) => {
          if (!isPending) {
            e.currentTarget.style.borderColor = '#8b5cf6';
            e.currentTarget.style.color = '#c4b5fd';
            e.currentTarget.style.background = 'rgba(139, 92, 246, 0.05)';
          }
        }}
        onMouseLeave={(e) => {
          if (!isPending) {
            e.currentTarget.style.borderColor = 'rgba(55, 65, 81, 0.5)';
            e.currentTarget.style.color = '#9ca3af';
            e.currentTarget.style.background = 'black';
          }
        }}
      >
        {isPending ? "Generating..." : "Reset Link"}
      </button>
      <button
        onClick={() => link && copyText(link)}
        disabled={!link || isPending}
        aria-label="Copy invite link"
        style={{
          background: copied ? '#10b981' : (link ? '#8b5cf6' : 'rgba(139, 92, 246, 0.2)'),
          border: `1px solid ${copied ? '#10b981' : (link ? '#8b5cf6' : 'transparent')}`,
          color: link ? '#ffffff' : 'rgba(255,255,255,0.4)',
          padding: '0 16px',
          height: '36px',
          fontSize: '13px',
          fontWeight: 600,
          fontFamily: "'Space Grotesk', system-ui, sans-serif",
          borderRadius: '8px',
          cursor: link ? 'pointer' : 'not-allowed',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          transition: 'all 0.2s ease',
          boxShadow: link ? '0 4px 12px rgba(139, 92, 246, 0.1)' : 'none',
        }}
        onMouseEnter={(e) => {
          if (link && !copied) {
            e.currentTarget.style.background = '#7c3aed';
            e.currentTarget.style.borderColor = '#7c3aed';
            e.currentTarget.style.transform = 'translateY(-1px)';
            e.currentTarget.style.boxShadow = '0 6px 16px rgba(139, 92, 246, 0.25)';
          }
        }}
        onMouseLeave={(e) => {
          if (link && !copied) {
            e.currentTarget.style.background = '#8b5cf6';
            e.currentTarget.style.borderColor = '#8b5cf6';
            e.currentTarget.style.transform = 'translateY(0)';
            e.currentTarget.style.boxShadow = '0 4px 12px rgba(139, 92, 246, 0.1)';
          }
        }}
      >
        {copied ? "Copied!" : "Copy Link"}
      </button>
    </div>
  );
};

function useTextCopy() {
  const [copied, setCopied] = useState(false);

  const copyText = useCallback((value: string) => {
    setCopied(true);
    navigator.clipboard.writeText(value ?? "");
    setTimeout(() => setCopied(false), 1500);
  }, []);

  return { copied, copyText };
}

