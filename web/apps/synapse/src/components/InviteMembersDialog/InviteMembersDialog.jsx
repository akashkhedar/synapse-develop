import { useState, useEffect } from "react";
import { Button } from "@synapse/ui";
import { IconCopy, IconCheck } from "@synapse/icons";
import { Modal } from "../Modal/ModalPopup";
import { Input } from "../Form";
import { useAPI } from "../../providers/ApiProvider";
import { cn } from "../../utils/bem";
import "./InviteMembersDialog.scss";

export const InviteMembersDialog = ({ isOpen, onClose, organizationId }) => {
  const api = useAPI();
  const [inviteUrl, setInviteUrl] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isCopied, setIsCopied] = useState(false);
  const [error, setError] = useState(null);
  const [inviteMode, setInviteMode] = useState("link"); // "link" or "email"
  const [emailAddress, setEmailAddress] = useState("");
  const [isSendingEmail, setIsSendingEmail] = useState(false);
  const [emailSent, setEmailSent] = useState(false);

  const rootClass = cn("invite-members-dialog");

  useEffect(() => {
    if (isOpen && organizationId) {
      loadInviteUrl();
    }
  }, [isOpen, organizationId]);

  const loadInviteUrl = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await api.callApi("resetInviteLink");
      const fullUrl = window.location.origin + response.invite_url;
      setInviteUrl(fullUrl);
    } catch (err) {
      console.error("Failed to load invite URL:", err);
      setError("Failed to load invite link. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  const copyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(inviteUrl);
      setIsCopied(true);
      setTimeout(() => setIsCopied(false), 2000);
    } catch (err) {
      console.error("Failed to copy:", err);
      setError("Failed to copy to clipboard");
    }
  };

  const sendEmailInvite = async () => {
    if (!emailAddress || !emailAddress.includes("@")) {
      setError("Please enter a valid email address");
      return;
    }

    setIsSendingEmail(true);
    setError(null);
    setEmailSent(false);

    try {
      await api.callApi("sendInviteEmail", {
        params: {
          pk: organizationId,
        },
        body: {
          email: emailAddress,
        },
      });
      setEmailSent(true);
      setEmailAddress("");
      setTimeout(() => setEmailSent(false), 3000);
    } catch (err) {
      console.error("Failed to send email invite:", err);
      setError(err.response?.data?.error || "Failed to send invite email. Please try again.");
    } finally {
      setIsSendingEmail(false);
    }
  };

  const handleClose = () => {
    setIsCopied(false);
    setError(null);
    setEmailAddress("");
    setEmailSent(false);
    setInviteMode("link");
    onClose();
  };

  return (
    <Modal
      visible={isOpen}
      onHide={handleClose}
      title="Invite Members"
      style={{ width: 560 }}
      body={
        <div className={rootClass.toString()}>
          {isLoading ? (
            <div className={rootClass.elem("loading")}>Loading invite link...</div>
          ) : (
            <>
              <p className={rootClass.elem("description")}>
                Invite people to join your organization by sharing a link or sending an email invitation.
              </p>

              {/* Mode Toggle */}
              <div className={rootClass.elem("mode-toggle")}>
                <Button
                  onClick={() => setInviteMode("link")}
                  look={inviteMode === "link" ? "primary" : "secondary"}
                  className={rootClass.elem("toggle-button")}
                >
                  Share Link
                </Button>
                <Button
                  onClick={() => setInviteMode("email")}
                  look={inviteMode === "email" ? "primary" : "secondary"}
                  className={rootClass.elem("toggle-button")}
                >
                  Send via Email
                </Button>
              </div>

              {/* Link Mode */}
              {inviteMode === "link" && (
                <>
                  <div className={rootClass.elem("link-section")}>
                    <label className={rootClass.elem("label")}>Invite Link</label>
                    <div className={rootClass.elem("input-group")}>
                      <Input
                        value={inviteUrl}
                        readOnly
                        className={rootClass.elem("input")}
                        onClick={(e) => e.target.select()}
                      />
                      <Button
                        onClick={copyToClipboard}
                        look="primary"
                        icon={isCopied ? <IconCheck /> : <IconCopy />}
                        className={rootClass.elem("copy-button")}
                      >
                        {isCopied ? "Copied!" : "Copy"}
                      </Button>
                    </div>
                  </div>
                </>
              )}

              {/* Email Mode */}
              {inviteMode === "email" && (
                <div className={rootClass.elem("email-section")}>
                  <label className={rootClass.elem("label")}>Email Address</label>
                  <div className={rootClass.elem("input-group")}>
                    <Input
                      value={emailAddress}
                      onChange={(e) => setEmailAddress(e.target.value)}
                      placeholder="colleague@example.com"
                      className={rootClass.elem("input")}
                      type="email"
                      disabled={isSendingEmail}
                    />
                    <Button
                      onClick={sendEmailInvite}
                      look="primary"
                      disabled={isSendingEmail || !emailAddress}
                      className={rootClass.elem("send-button")}
                    >
                      {isSendingEmail ? "Sending..." : emailSent ? "Sent!" : "Send Invite"}
                    </Button>
                  </div>
                  {emailSent && (
                    <div className={rootClass.elem("success")}>
                      ✓ Invitation sent successfully!
                    </div>
                  )}
                </div>
              )}

              {error && (
                <div className={rootClass.elem("error")}>
                  {error}
                </div>
              )}

              <div className={rootClass.elem("info")}>
                <p className={rootClass.elem("info-title")}>What happens when someone joins?</p>
                <ul className={rootClass.elem("info-list")}>
                  <li>They become a member of your organization</li>
                  <li>They can access all projects in this organization</li>
                  <li>They can create and manage tasks</li>
                  <li>They can view and edit annotations</li>
                </ul>
              </div>
            </>
          )}
        </div>
      }
      footer={
        <div className={rootClass.elem("actions")}>
          <Button onClick={handleClose}>
            Close
          </Button>
        </div>
      }
    />
  );
};

