import { useState, useEffect } from "react";
import { IconCopy, IconCheck, IconCross } from "@synapse/icons";
// import { Modal } from "../Modal/ModalPopup";
import { API } from "../../providers/ApiProvider";

export const InviteMembersDialog = ({ isOpen, onClose, organizationId }) => {
  // api not needed if we use API static instance
  const [inviteUrl, setInviteUrl] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isCopied, setIsCopied] = useState(false);
  const [error, setError] = useState(null);
  const [inviteMode, setInviteMode] = useState("link"); // "link" or "email"
  const [emailAddress, setEmailAddress] = useState("");
  const [isSendingEmail, setIsSendingEmail] = useState(false);
  const [emailSent, setEmailSent] = useState(false);

  useEffect(() => {
    if (isOpen && organizationId && !inviteUrl) {
      loadInviteUrl();
    }
  }, [isOpen, organizationId, inviteUrl]);

  const loadInviteUrl = async () => {
    setIsLoading(true);
    setError(null);
    try {
      // Use API.invoke consistent with previous implementation
      const result = await API.invoke("resetInviteLink");
      console.log("resetInviteLink result:", result);
      
      // Handle both WrappedResponse (result.response.invite_url) and direct response (result.invite_url)
      const invitePath = result.response?.invite_url || result.invite_url;
      
      if (!invitePath) {
        throw new Error("Invalid response format: invite_url not found");
      }
      
      const fullUrl = window.location.origin + invitePath;
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
      await API.invoke(
        "sendInviteEmail",
        { pk: organizationId },
        {
          body: {
            email: emailAddress,
          },
        }
      );
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

  const commonButtonStyle = {
    fontFamily: "'Space Grotesk', system-ui, sans-serif",
    fontSize: '13px',
    fontWeight: 600,
    cursor: 'pointer',
    transition: 'all 0.2s ease',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    height: '36px',
    padding: '0 16px',
    border: '1px solid',
  };

  const primaryButtonStyle = {
    ...commonButtonStyle,
    background: '#8b5cf6',
    borderColor: '#8b5cf6',
    color: '#ffffff',
  };

  const secondaryButtonStyle = {
    ...commonButtonStyle,
    background: 'black',
    borderColor: 'rgba(55, 65, 81, 0.5)',
    color: '#9ca3af',
  };

  // Custom Modal Styles
  const overlayStyle = {
    position: "fixed",
    top: 0,
    left: 0,
    width: "100%",
    height: "100%",
    background: "rgba(0, 0, 0, 0.7)",
    backdropFilter: "blur(4px)",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    zIndex: 1000,
  };

  const modalStyle = {
    width: "560px",
    background: "#000000",
    border: "1px solid #22262dff", // Grey border
    borderRadius: "0",
    boxShadow: "none",
    display: "flex",
    flexDirection: "column",
    position: "relative",
  };

  const cornerBorderStyle = {
    position: "absolute",
    width: "12px",
    height: "12px",
    borderColor: "#8b5cf6",
    borderStyle: "solid",
    pointerEvents: "none",
    zIndex: 10,
  };

  const headerStyle = {
    padding: "20px 24px",
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    borderBottom: "1px solid #1f2937",
    position: "relative",
  };

  const titleStyle = {
    fontSize: "18px",
    fontWeight: 600,
    color: "#ffffff",
    fontFamily: "'Space Grotesk', system-ui, sans-serif",
    letterSpacing: "-0.02em",
  };

  const closeButtonStyle = {
    background: "transparent",
    border: "none",
    cursor: "pointer",
    padding: "4px",
    borderRadius: "4px",
    color: "#6b7280",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    transition: "all 0.2s",
  };

  if (!isOpen) return null;

  return (
    <div style={overlayStyle} onClick={(e) => e.target === e.currentTarget && handleClose()}>
      <div style={modalStyle}>
        {/* Corner Borders */}
        <div style={{...cornerBorderStyle, top: 0, left: 0, borderTopWidth: "2px", borderLeftWidth: "2px", borderRightWidth: 0, borderBottomWidth: 0}} />
        <div style={{...cornerBorderStyle, bottom: 0, right: 0, borderBottomWidth: "2px", borderRightWidth: "2px", borderTopWidth: 0, borderLeftWidth: 0}} />

        <div style={headerStyle}>
          <h2 style={titleStyle}>Invite Members</h2>
          <button 
            style={closeButtonStyle}
            onClick={handleClose}
            onMouseEnter={(e) => { e.currentTarget.style.color = "#ffffff"; e.currentTarget.style.background = "rgba(255,255,255,0.1)"; }}
            onMouseLeave={(e) => { e.currentTarget.style.color = "#6b7280"; e.currentTarget.style.background = "transparent"; }}
          >
            <IconCross style={{ width: 20, height: 20 }} />
          </button>
        </div>

        <div style={{ padding: "24px", fontFamily: "'Space Grotesk', system-ui, sans-serif" }}>
          {isLoading ? (
            <div style={{ textAlign: 'center', padding: '40px 0', color: '#9ca3af', fontSize: '13px' }}>
              Generating invite link...
            </div>
          ) : (
            <>
              <p style={{ fontSize: '14px', color: '#d1d5db', margin: '0 0 24px 0', lineHeight: 1.5 }}>
                Invite people to join your organization by sharing a link or sending an email invitation.
              </p>

              {/* Mode Toggle */}
              <div style={{ display: 'flex', gap: '8px', marginBottom: '24px', background: 'rgba(0,0,0,0.3)', padding: '4px', border: '1px solid rgba(55, 65, 81, 0.5)' }}>
                {['link', 'email'].map((mode) => (
                  <button
                    key={mode}
                    onClick={() => setInviteMode(mode)}
                    style={{
                      flex: 1,
                      border: 'none',
                      background: inviteMode === mode ? '#8b5cf6' : 'transparent',
                      color: inviteMode === mode ? '#ffffff' : '#9ca3af',
                      padding: '8px',
                      fontSize: '13px',
                      fontWeight: 600,
                      cursor: 'pointer',
                      transition: 'all 0.2s ease',
                    }}
                  >
                    {mode === 'link' ? 'Share Link' : 'Send via Email'}
                  </button>
                ))}
              </div>

              {/* Link Mode */}
              {inviteMode === "link" && (
                <div style={{ marginBottom: '24px' }}>
                  <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: '#9ca3af', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '8px' }}>
                    Invite Link
                  </label>
                  <div style={{ display: 'flex', gap: '8px' }}>
                    <input
                      value={inviteUrl}
                      readOnly
                      style={{
                        flex: 1,
                        background: 'rgba(0, 0, 0, 0.3)',
                        border: '1px solid rgba(55, 65, 81, 0.5)',
                        color: '#ffffff',
                        padding: '0 12px',
                        fontSize: '13px',
                        fontFamily: "'Space Grotesk', system-ui, sans-serif",
                        outline: 'none',
                      }}
                      onFocus={(e) => {
                         e.target.style.borderColor = '#8b5cf6';
                         e.target.style.background = 'rgba(0,0,0,0.5)';
                      }}
                       onBlur={(e) => {
                         e.target.style.borderColor = 'rgba(55, 65, 81, 0.5)';
                         e.target.style.background = 'rgba(0,0,0,0.3)';
                      }}
                    />
                    <button
                      onClick={copyToClipboard}
                      style={{
                        ...primaryButtonStyle,
                        background: isCopied ? '#10b981' : '#8b5cf6',
                        borderColor: isCopied ? '#10b981' : '#8b5cf6',
                        minWidth: '100px',
                      }}
                    >
                      {isCopied ? "Copied!" : "Copy"}
                    </button>
                  </div>
                </div>
              )}

              {/* Email Mode */}
              {inviteMode === "email" && (
                <div style={{ marginBottom: '24px' }}>
                  <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: '#9ca3af', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '8px' }}>
                    Email Address
                  </label>
                  <div style={{ display: 'flex', gap: '8px' }}>
                    <input
                      value={emailAddress}
                      onChange={(e) => setEmailAddress(e.target.value)}
                      placeholder="colleague@example.com"
                      type="email"
                      disabled={isSendingEmail}
                      style={{
                        flex: 1,
                        background: 'rgba(0, 0, 0, 0.3)',
                        border: '1px solid rgba(55, 65, 81, 0.5)',
                        color: '#ffffff',
                        padding: '0 12px',
                        fontSize: '13px',
                        fontFamily: "'Space Grotesk', system-ui, sans-serif",
                        outline: 'none',
                      }}
                      onFocus={(e) => {
                         e.target.style.borderColor = '#8b5cf6';
                         e.target.style.background = 'rgba(0,0,0,0.5)';
                      }}
                       onBlur={(e) => {
                         e.target.style.borderColor = 'rgba(55, 65, 81, 0.5)';
                         e.target.style.background = 'rgba(0,0,0,0.3)';
                      }}
                    />
                    <button
                      onClick={sendEmailInvite}
                      disabled={isSendingEmail || !emailAddress}
                      style={{
                        ...primaryButtonStyle,
                        opacity: (isSendingEmail || !emailAddress) ? 0.6 : 1,
                        cursor: (isSendingEmail || !emailAddress) ? 'not-allowed' : 'pointer',
                        minWidth: '110px',
                      }}
                    >
                      {isSendingEmail ? "Sending..." : "Send Invite"}
                    </button>
                  </div>
                  {emailSent && (
                    <div style={{ marginTop: '12px', padding: '8px 12px', background: 'rgba(16, 185, 129, 0.1)', border: '1px solid rgba(16, 185, 129, 0.2)', color: '#34d399', fontSize: '13px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <IconCheck style={{ width: 14, height: 14 }} /> Invitation sent successfully!
                    </div>
                  )}
                </div>
              )}

              {error && (
                <div style={{ marginBottom: '20px', padding: '8px 12px', background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.2)', color: '#f87171', fontSize: '13px' }}>
                  {error}
                </div>
              )}

              <div style={{ padding: '16px', background: 'rgba(255, 255, 255, 0.02)', border: '1px solid rgba(55, 65, 81, 0.3)' }}>
                <p style={{ margin: '0 0 12px 0', fontSize: '13px', fontWeight: 600, color: '#e5e7eb' }}>What happens when someone joins?</p>
                <ul style={{ margin: 0, paddingLeft: '20px', color: '#9ca3af', fontSize: '13px', lineHeight: 1.6 }}>
                  <li>They become a member of your organization</li>
                  <li>They can access all projects in this organization</li>
                  <li>They can create and manage tasks</li>
                  <li>They can view and edit annotations</li>
                </ul>
              </div>
            </>
          )}
        </div>
        
        <div style={{ display: 'flex', justifyContent: 'flex-end', padding: '20px 24px', borderTop: '1px solid rgba(55, 65, 81, 0.5)' }}>
          <button
            onClick={handleClose}
            style={secondaryButtonStyle}
            onMouseEnter={(e) => {
              e.currentTarget.style.borderColor = '#8b5cf6';
              e.currentTarget.style.color = '#c4b5fd';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.borderColor = 'rgba(55, 65, 81, 0.5)';
              e.currentTarget.style.color = '#9ca3af';
            }}
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

