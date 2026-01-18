import { useState } from "react";
import { Button, Spinner } from "@synapse/ui"; // Keeping Spinner/Button for utility, but might style button manually if needed
import { IconCross } from "@synapse/icons";
import { cn } from "../../utils/bem";
import "./CreateOrganizationDialog.scss";

export const CreateOrganizationDialog = ({ isOpen, onClose, onSuccess }) => {
  const [organizationName, setOrganizationName] = useState("");
  const [isCreating, setIsCreating] = useState(false);
  const [error, setError] = useState(null);

  const rootClass = cn("create-organization-dialog");

  const handleCreate = async () => {
    if (!organizationName.trim()) {
      setError("Organization name is required");
      return;
    }

    setIsCreating(true);
    setError(null);

    try {
      const response = await fetch('/api/organizations/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          title: organizationName.trim(),
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to create organization');
      }

      const newOrg = await response.json();
      
      // Switch to the new organization
      const switchResponse = await fetch('/api/organizations/switch', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          organization_id: newOrg.id,
        }),
      });

      if (!switchResponse.ok) {
        throw new Error('Failed to switch to new organization');
      }

      onSuccess?.(newOrg);
      // Redirect to projects page with new organization context
      window.location.href = '/projects';
    } catch (err) {
      console.error("Failed to create organization:", err);
      setError(err.message || "Failed to create organization");
      setIsCreating(false);
    }
  };

  const handleClose = () => {
    if (!isCreating) {
      setOrganizationName("");
      setError(null);
      onClose();
    }
  };

  if (!isOpen) return null;

  const overlayStyle = {
    position: "fixed",
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    background: "rgba(0, 0, 0, 0.8)",
    backdropFilter: "blur(4px)",
    zIndex: 1000,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    opacity: 1, // Simple visibility for now, animation could be added
  };

  const modalStyle = {
    width: "480px",
    background: "#000000",
    border: "1px solid #22262dff", // Added subtle grey border requested by user
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
    zIndex: 10, // Ensure it sits above the main border
  };

  const headerStyle = {
    padding: "20px 24px",
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    borderBottom: "1px solid #1f2937",
    position: "relative", // For containing corner
  };

  const titleStyle = {
    fontSize: "18px",
    fontWeight: 600,
    color: "#ffffff",
    fontFamily: "'Space Grotesk', sans-serif", // Explicit quotes
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

  const inputStyle = {
    width: "100%",
    background: "transparent",
    border: "none",
    borderBottom: "1px solid #374151",
    padding: "12px 0",
    fontSize: "16px",
    color: "#ffffff",
    borderRadius: 0,
    outline: "none",
    fontFamily: "monospace",
    transition: "border-color 0.2s",
  };

  return (
    <div style={overlayStyle} onClick={(e) => e.target === e.currentTarget && handleClose()}>
      <div style={modalStyle}>
        {/* Corner Borders */}
        <div style={{...cornerBorderStyle, top: 0, left: 0, borderTopWidth: "2px", borderLeftWidth: "2px", borderRightWidth: 0, borderBottomWidth: 0}} />
        <div style={{...cornerBorderStyle, bottom: 0, right: 0, borderBottomWidth: "2px", borderRightWidth: "2px", borderTopWidth: 0, borderLeftWidth: 0}} />

        <div style={headerStyle}>
          <h2 style={titleStyle}>Create Organization</h2>
          <button 
            style={closeButtonStyle}
            onClick={handleClose}
            onMouseEnter={(e) => { e.currentTarget.style.color = "#ffffff"; e.currentTarget.style.background = "rgba(255,255,255,0.1)"; }}
            onMouseLeave={(e) => { e.currentTarget.style.color = "#6b7280"; e.currentTarget.style.background = "transparent"; }}
          >
            <IconCross style={{ width: 20, height: 20 }} />
          </button>
        </div>

        <div style={{ padding: "24px" }}>
          <p style={{ color: "#9ca3af", fontSize: "14px", marginBottom: "24px", lineHeight: "1.5" }}>
            Create a new organization to manage projects and collaborate with team members.
          </p>

          <div style={{ marginBottom: "8px" }}>
            <label style={{ display: "block", fontSize: "12px", textTransform: "uppercase", color: "#6b7280", letterSpacing: "0.05em", marginBottom: "8px", fontFamily: "monospace" }}>
              Organization Name
            </label>
            <input
              style={inputStyle}
              value={organizationName}
              onChange={(e) => {
                setOrganizationName(e.target.value);
                setError(null);
              }}
              onFocus={(e) => e.target.style.borderColor = "#8b5cf6"} // --dm-primary
              onBlur={(e) => e.target.style.borderColor = "#374151"}
              placeholder="Enter organization name"
              disabled={isCreating}
              autoFocus
              onKeyPress={(e) => {
                if (e.key === 'Enter' && !isCreating) {
                  handleCreate();
                }
              }}
            />
          </div>
          
          {error && (
            <div style={{ marginTop: "12px", color: "#ef4444", fontSize: "13px", padding: "8px 12px", background: "rgba(239,68,68,0.1)", borderRadius: "4px", border: "1px solid rgba(239,68,68,0.2)" }}>
              {error}
            </div>
          )}
        </div>

        <div style={{ padding: "16px 24px 24px", display: "flex", justifyContent: "flex-end", gap: "12px" }}>
          <button
            onClick={handleClose}
            disabled={isCreating}
            style={{
              padding: "8px 16px",
              background: "rgba(139, 92, 246, 0.08)", // Secondary tint
              border: "1px solid rgba(139, 92, 246, 0.3)",
              borderRadius: "4px",
              color: "#ffffff",
              fontSize: "13px",
              cursor: "pointer",
              fontFamily: "'Space Grotesk', sans-serif",
              textTransform: "uppercase",
              letterSpacing: "0.05em",
              transition: "all 0.2s"
            }}
            onMouseEnter={(e) => e.currentTarget.style.background = "rgba(139, 92, 246, 0.15)"}
            onMouseLeave={(e) => e.currentTarget.style.background = "rgba(139, 92, 246, 0.08)"}
          >
            Cancel
          </button>
          <button
            onClick={handleCreate}
            disabled={isCreating || !organizationName.trim()}
            style={{
              padding: "8px 16px",
              background: "linear-gradient(135deg, rgba(139, 92, 246, 0.15), rgba(168, 85, 247, 0.1))", // Primary Gradient
              border: "1px solid rgba(139, 92, 246, 0.5)",
              borderRadius: "4px",
              color: "#ffffff",
              fontSize: "13px",
              cursor: isCreating || !organizationName.trim() ? "not-allowed" : "pointer",
              fontFamily: "'Space Grotesk', sans-serif",
              fontWeight: 600,
              textTransform: "uppercase",
              letterSpacing: "0.05em",
              display: "flex",
              alignItems: "center",
              gap: "8px",
              opacity: isCreating || !organizationName.trim() ? 0.5 : 1,
              boxShadow: "0 0 10px rgba(139, 92, 246, 0.2)"
            }}
            onMouseEnter={(e) => { if(!isCreating && organizationName.trim()) e.currentTarget.style.boxShadow = "0 0 15px rgba(139, 92, 246, 0.4)"; }}
            onMouseLeave={(e) => { if(!isCreating && organizationName.trim()) e.currentTarget.style.boxShadow = "0 0 10px rgba(139, 92, 246, 0.2)"; }}
          >
            {isCreating && <Spinner size={12} color="#ffffff" />}
            {isCreating ? "Creating..." : "Create Organization"}
          </button>
        </div>
      </div>
    </div>
  );
};

