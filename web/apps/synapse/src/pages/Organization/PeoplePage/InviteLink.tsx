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
  const { data: link } = useAtomValue(linkAtom);
  return (
    <div className={cn("invite").toClassName()}>
      <div className="invite__label">Share this link with your team</div>
      <div className="invite__input-wrapper">
        <input type="text" value={link} style={{ width: "100%" }} readOnly />
      </div>
      <p className="invite__hint">
        Invite members to join your Synapse instance. People that you invite have full access to all of your
        projects.{" "}
        <a
          href="https://synapse.io/guide/signup.html"
          target="_blank"
          rel="noreferrer"
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
  const { refetch, data: link } = useAtomValue(linkAtom);

  return (
    <div className="invite__actions">
      <button
        className="invite__btn invite__btn--secondary"
        onClick={() => refetch()}
        aria-label="Refresh invite link"
      >
        Reset Link
      </button>
      <button
        className={`invite__btn invite__btn--primary ${copied ? 'invite__btn--success' : ''}`}
        onClick={() => copyText(link!)}
        aria-label="Copy invite link"
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

