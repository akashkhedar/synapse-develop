import { useState, useEffect, useCallback } from "react";
import { Spinner } from "@synapse/ui";
import { IconCopy, IconRefresh, IconCheck, IconCross, IconEyeOpened, IconEyeClosed } from "@synapse/icons";
import { useAPI } from "../../../providers/ApiProvider";
import "./OrganizationApiKeyModal.scss";

export const OrganizationApiKeyModal = ({ organizationId, onClose, onSaved }) => {
  const api = useAPI();
  const [apiKey, setApiKey] = useState(null);
  const [createdAt, setCreatedAt] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isResetting, setIsResetting] = useState(false);
  const [isCopied, setIsCopied] = useState(false);
  const [isRevealed, setIsRevealed] = useState(false);
  const [error, setError] = useState(null);
  const [showResetConfirm, setShowResetConfirm] = useState(false);

  const fetchApiKey = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const response = await api.callApi("organizationApiKey", {
        params: { pk: organizationId }
      });
      setApiKey(response.api_key);
      setCreatedAt(response.created_at);
    } catch (err) {
      setError(err.message || "Failed to fetch API key");
    } finally {
      setIsLoading(false);
    }
  }, [api, organizationId]);

  const handleReset = async () => {
    try {
      setIsResetting(true);
      setError(null);
      const response = await api.callApi("organizationApiKeyReset", {
        params: { pk: organizationId },
        body: {}
      });
      setApiKey(response.api_key);
      setCreatedAt(response.created_at);
      setShowResetConfirm(false);
      setIsRevealed(true);
      onSaved?.();
    } catch (err) {
      setError(err.message || "Failed to reset API key");
    } finally {
      setIsResetting(false);
    }
  };

  const handleCopy = () => {
    if (apiKey) {
      navigator.clipboard.writeText(apiKey);
      setIsCopied(true);
      setTimeout(() => setIsCopied(false), 2500);
    }
  };

  useEffect(() => {
    fetchApiKey();
  }, [fetchApiKey]);

  // Create masked version of key
  const maskedKey = apiKey 
    ? `${apiKey.slice(0, 6)}${"•".repeat(20)}${apiKey.slice(-6)}` 
    : "";

  // Styles
  const overlayStyle = {
    position: "fixed",
    top: 0,
    left: 0,
    width: "100%",
    height: "100%",
    background: "rgba(0, 0, 0, 0.8)",
    backdropFilter: "blur(4px)",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    zIndex: 1000,
  };

  const modalStyle = {
    width: "560px",
    maxWidth: "90vw",
    background: "#000000",
    border: "1px solid #22262dff",
    borderRadius: "0",
    boxShadow: "none",
    display: "flex",
    flexDirection: "column",
    position: "relative",
    fontFamily: "'Space Grotesk', system-ui, sans-serif",
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

  const contentStyle = {
    padding: "24px",
    display: "flex",
    flexDirection: "column",
    gap: "20px",
  };

  const labelStyle = {
    display: "block",
    fontSize: "12px",
    fontWeight: 600,
    color: "#9ca3af",
    textTransform: "uppercase",
    letterSpacing: "0.05em",
    marginBottom: "8px",
  };

  const keyContainerStyle = {
    display: "flex",
    gap: "8px",
    alignItems: "center",
  };

  const keyValueStyle = {
    flex: 1,
    padding: "0 14px",
    background: "rgba(0, 0, 0, 0.3)",
    border: "1px solid rgba(55, 65, 81, 0.5)",
    color: "#ffffff",
    fontFamily: "ui-monospace, 'SF Mono', 'Cascadia Code', Consolas, monospace",
    fontSize: "13px",
    overflowX: "auto",
    overflowY: "hidden",
    whiteSpace: "nowrap",
    lineHeight: "42px",
    height: "42px",
    cursor: "pointer",
    transition: "border-color 0.2s, background 0.2s",
  };

  const primaryButtonStyle = {
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    gap: "6px",
    padding: "0 16px",
    height: "40px",
    minWidth: "90px",
    background: "#8b5cf6",
    border: "1px solid #8b5cf6",
    color: "#ffffff",
    fontSize: "13px",
    fontWeight: 600,
    fontFamily: "'Space Grotesk', system-ui, sans-serif",
    cursor: "pointer",
    transition: "all 0.2s ease",
  };

  const secondaryButtonStyle = {
    ...primaryButtonStyle,
    background: "black",
    borderColor: "rgba(55, 65, 81, 0.5)",
    color: "#9ca3af",
  };

  const dangerButtonStyle = {
    ...primaryButtonStyle,
    background: "rgba(239, 68, 68, 0.12)",
    border: "1px solid rgba(239, 68, 68, 0.3)",
    color: "#fca5a5",
  };

  const successButtonStyle = {
    ...primaryButtonStyle,
    background: "#10b981",
    borderColor: "#10b981",
    color: "#ffffff",
  };

  const metaStyle = {
    display: "flex",
    alignItems: "center",
    gap: "8px",
    fontSize: "13px",
    padding: "12px 14px",
    background: "rgba(255, 255, 255, 0.02)",
    border: "1px solid rgba(55, 65, 81, 0.3)",
  };

  const codeBlockStyle = {
    padding: "16px",
    background: "rgba(255, 255, 255, 0.02)",
    border: "1px solid rgba(55, 65, 81, 0.3)",
  };

  const errorStyle = {
    padding: "12px 14px",
    background: "rgba(239, 68, 68, 0.1)",
    border: "1px solid rgba(239, 68, 68, 0.2)",
    color: "#f87171",
    fontSize: "13px",
    display: "flex",
    alignItems: "center",
    gap: "8px",
  };

  const warningBoxStyle = {
    padding: "16px",
    background: "rgba(239, 68, 68, 0.06)",
    border: "1px solid rgba(239, 68, 68, 0.2)",
    display: "flex",
    flexDirection: "column",
    gap: "14px",
  };

  const footerStyle = {
    padding: "16px 24px 20px",
    borderTop: "1px solid rgba(55, 65, 81, 0.5)",
  };

  return (
    <>
      <style>{`
        .api-key-modal-scrollbar {
          scrollbar-width: none !important;
          -ms-overflow-style: none !important;
        }
        .api-key-modal-scrollbar::-webkit-scrollbar {
          display: none !important;
          height: 0 !important;
          width: 0 !important;
        }
      `}</style>
      <div style={overlayStyle} onClick={(e) => e.target === e.currentTarget && onClose()}>
        <div style={modalStyle}>
        {/* Corner Borders */}
        <div style={{...cornerBorderStyle, top: 0, left: 0, borderTopWidth: "2px", borderLeftWidth: "2px", borderRightWidth: 0, borderBottomWidth: 0}} />
        <div style={{...cornerBorderStyle, bottom: 0, right: 0, borderBottomWidth: "2px", borderRightWidth: "2px", borderTopWidth: 0, borderLeftWidth: 0}} />

        {/* Header */}
        <div style={headerStyle}>
          <h2 style={titleStyle}>Organization API Key</h2>
          <button 
            style={closeButtonStyle}
            onClick={onClose}
            onMouseEnter={(e) => { e.currentTarget.style.color = "#ffffff"; e.currentTarget.style.background = "rgba(255,255,255,0.1)"; }}
            onMouseLeave={(e) => { e.currentTarget.style.color = "#6b7280"; e.currentTarget.style.background = "transparent"; }}
            aria-label="Close modal"
          >
            <IconCross style={{ width: 20, height: 20 }} />
          </button>
        </div>

        {/* Content */}
        <div style={contentStyle}>
          {isLoading ? (
            <div style={{ textAlign: "center", padding: "40px 0", color: "#9ca3af", fontSize: "13px", display: "flex", alignItems: "center", justifyContent: "center", gap: "12px" }}>
              <Spinner size={20} />
              <span>Loading API key...</span>
            </div>
          ) : error ? (
            <div style={{ display: "flex", flexDirection: "column", gap: "16px", alignItems: "center", padding: "20px" }}>
              <div style={errorStyle}>
                <span>{error}</span>
              </div>
              <button 
                style={primaryButtonStyle}
                onClick={fetchApiKey}
                onMouseEnter={(e) => { e.currentTarget.style.background = "#7c3aed"; }}
                onMouseLeave={(e) => { e.currentTarget.style.background = "#8b5cf6"; }}
              >
                Retry
              </button>
            </div>
          ) : (
            <>
              {/* API Key Display */}
              <div>
                <label style={labelStyle}>API Key</label>
                <div style={keyContainerStyle}>
                  <div 
                    className="api-key-modal-scrollbar"
                    style={keyValueStyle}
                    onClick={() => setIsRevealed(!isRevealed)}
                    onMouseEnter={(e) => { e.currentTarget.style.borderColor = "#8b5cf6"; e.currentTarget.style.background = "rgba(0, 0, 0, 0.5)"; }}
                    onMouseLeave={(e) => { e.currentTarget.style.borderColor = "rgba(55, 65, 81, 0.5)"; e.currentTarget.style.background = "rgba(0, 0, 0, 0.3)"; }}
                    title="Click to toggle visibility"
                  >
                    {isRevealed ? apiKey : maskedKey}
                  </div>
                  <button 
                    style={secondaryButtonStyle}
                    onClick={() => setIsRevealed(!isRevealed)}
                    onMouseEnter={(e) => { e.currentTarget.style.borderColor = "#8b5cf6"; e.currentTarget.style.color = "#c4b5fd"; }}
                    onMouseLeave={(e) => { e.currentTarget.style.borderColor = "rgba(55, 65, 81, 0.5)"; e.currentTarget.style.color = "#9ca3af"; }}
                    title={isRevealed ? "Hide key" : "Reveal key"}
                    aria-label={isRevealed ? "Hide API key" : "Reveal API key"}
                  >
                    {isRevealed ? <IconEyeClosed style={{ width: 16, height: 16 }} /> : <IconEyeOpened style={{ width: 16, height: 16 }} />}
                  </button>
                  <button 
                    style={isCopied ? successButtonStyle : primaryButtonStyle}
                    onClick={handleCopy}
                    onMouseEnter={(e) => { if (!isCopied) e.currentTarget.style.background = "#7c3aed"; }}
                    onMouseLeave={(e) => { if (!isCopied) e.currentTarget.style.background = "#8b5cf6"; }}
                    aria-label="Copy API key"
                  >
                    {isCopied ? (
                      <>
                        <IconCheck style={{ width: 14, height: 14 }} />
                        Copied!
                      </>
                    ) : (
                      <>
                        <IconCopy style={{ width: 14, height: 14 }} />
                        Copy
                      </>
                    )}
                  </button>
                </div>
              </div>

              {/* Created At Info */}
              {createdAt && (
                <div style={metaStyle}>
                  <span style={{ color: "#6b7280", fontWeight: 500 }}>Created:</span>
                  <span style={{ color: "#d1d5db", fontFamily: "ui-monospace, 'SF Mono', Consolas, monospace", fontSize: "12px" }}>
                    {new Date(createdAt).toLocaleString()}
                  </span>
                </div>
              )}

              {/* Usage Info */}
              <div style={codeBlockStyle}>
                <label style={{ ...labelStyle, marginBottom: "12px" }}>SDK Usage</label>
                <div 
                  className="api-key-modal-scrollbar"
                  style={{ 
                    padding: "12px 14px", 
                    background: "rgba(0, 0, 0, 0.4)", 
                    border: "1px solid rgba(55, 65, 81, 0.3)",
                    overflowX: "auto",
                    overflowY: "hidden",
                  }}
                >
                  <code style={{ 
                    fontFamily: "ui-monospace, 'SF Mono', 'Cascadia Code', Consolas, monospace", 
                    fontSize: "12px", 
                    color: "#c4b5fd",
                    whiteSpace: "nowrap",
                  }}>
                    synapse.init(api_key="{isRevealed ? apiKey : 'YOUR_API_KEY'}")
                  </code>
                </div>
              </div>

              {/* Reset Section */}
              <div style={{ paddingTop: "12px", borderTop: "1px solid rgba(55, 65, 81, 0.3)" }}>
                {showResetConfirm ? (
                  <div style={warningBoxStyle}>
                    <span style={{ fontSize: "14px", color: "#fca5a5", fontWeight: 500 }}>
                      ⚠️ This will invalidate the current key. Are you sure?
                    </span>
                    <div style={{ display: "flex", gap: "12px" }}>
                      <button 
                        style={{ ...dangerButtonStyle, opacity: isResetting ? 0.5 : 1, cursor: isResetting ? "not-allowed" : "pointer" }}
                        onClick={handleReset}
                        disabled={isResetting}
                        onMouseEnter={(e) => { if (!isResetting) { e.currentTarget.style.background = "rgba(239, 68, 68, 0.2)"; e.currentTarget.style.borderColor = "rgba(239, 68, 68, 0.5)"; } }}
                        onMouseLeave={(e) => { e.currentTarget.style.background = "rgba(239, 68, 68, 0.12)"; e.currentTarget.style.borderColor = "rgba(239, 68, 68, 0.3)"; }}
                      >
                        {isResetting ? <Spinner size={14} /> : <IconRefresh style={{ width: 14, height: 14 }} />}
                        Yes, Reset Key
                      </button>
                      <button 
                        style={secondaryButtonStyle}
                        onClick={() => setShowResetConfirm(false)}
                        onMouseEnter={(e) => { e.currentTarget.style.borderColor = "#8b5cf6"; e.currentTarget.style.color = "#c4b5fd"; }}
                        onMouseLeave={(e) => { e.currentTarget.style.borderColor = "rgba(55, 65, 81, 0.5)"; e.currentTarget.style.color = "#9ca3af"; }}
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                ) : (
                  <button 
                    style={dangerButtonStyle}
                    onClick={() => setShowResetConfirm(true)}
                    onMouseEnter={(e) => { e.currentTarget.style.background = "rgba(239, 68, 68, 0.2)"; e.currentTarget.style.borderColor = "rgba(239, 68, 68, 0.5)"; }}
                    onMouseLeave={(e) => { e.currentTarget.style.background = "rgba(239, 68, 68, 0.12)"; e.currentTarget.style.borderColor = "rgba(239, 68, 68, 0.3)"; }}
                  >
                    <IconRefresh style={{ width: 14, height: 14 }} />
                    Reset API Key
                  </button>
                )}
              </div>
            </>
          )}
        </div>

        {/* Footer */}
        <div style={footerStyle}>
          <div style={{ display: "flex", justifyContent: "flex-end" }}>
            <button
              onClick={onClose}
              style={secondaryButtonStyle}
              onMouseEnter={(e) => { e.currentTarget.style.borderColor = "#8b5cf6"; e.currentTarget.style.color = "#c4b5fd"; }}
              onMouseLeave={(e) => { e.currentTarget.style.borderColor = "rgba(55, 65, 81, 0.5)"; e.currentTarget.style.color = "#9ca3af"; }}
            >
              Close
            </button>
          </div>
        </div>
      </div>
      </div>
    </>
  );
};
