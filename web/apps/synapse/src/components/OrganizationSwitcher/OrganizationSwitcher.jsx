import { useCallback, useEffect, useState } from "react";
import { Dropdown, Spinner } from "@synapse/ui";
import {
  IconPeople,
  IconCheck,
  IconPlus,
  IconUserAdd,
  IconRemove,
  IconCross,
} from "@synapse/icons";
import { useAPI } from "../../providers/ApiProvider";
import { cn } from "../../utils/bem";
import { Modal } from "../Modal/ModalPopup";
import { CreateOrganizationDialog } from "../CreateOrganizationDialog/CreateOrganizationDialog";
import { InviteMembersDialog } from "../InviteMembersDialog/InviteMembersDialog";
import "./OrganizationSwitcher.scss";

export const OrganizationSwitcher = ({ className }) => {
  const api = useAPI();
  const [organizations, setOrganizations] = useState([]);
  const [activeOrganization, setActiveOrganization] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSwitching, setIsSwitching] = useState(false);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showInviteDialog, setShowInviteDialog] = useState(false);
  const [showLeaveDialog, setShowLeaveDialog] = useState(false);
  const [currentUser, setCurrentUser] = useState(null);
  const [isLeaving, setIsLeaving] = useState(false);

  const rootClass = cn("organization-switcher");

  // Load organizations
  useEffect(() => {
    loadOrganizations();
  }, []);

  const loadOrganizations = async () => {
    setIsLoading(true);
    try {
      // Fetch user data to get active organization
      const userResponse = await api.callApi("me");
      setCurrentUser(userResponse);
      const activeOrgId = userResponse?.active_organization;

      // Fetch organizations list
      const response = await fetch("/api/organizations/", {
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include",
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch organizations: ${response.status}`);
      }

      const data = await response.json();
      const orgs = data?.results || data || [];
      setOrganizations(orgs);

      // Find active organization by ID from user data
      const active = orgs.find((org) => org.id === activeOrgId) || orgs[0];
      setActiveOrganization(active);
    } catch (error) {
      console.error("Failed to load organizations:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const switchOrganization = useCallback(
    async (orgId) => {
      if (isSwitching || activeOrganization?.id === orgId) return;

      setIsSwitching(true);
      try {
        const response = await fetch("/api/organizations/switch", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          credentials: "include",
          body: JSON.stringify({
            organization_id: orgId,
          }),
        });

        if (!response.ok) {
          throw new Error(`Failed to switch organization: ${response.status}`);
        }

        // Force navigation to projects page to ensure fresh data load with new organization context
        // Use replace to avoid browser cache issues
        window.location.replace("/projects");
      } catch (error) {
        console.error("Failed to switch organization:", error);
        setIsSwitching(false);
      }
    },
    [activeOrganization, isSwitching]
  );

  const leaveOrganization = useCallback(async () => {
    if (isLeaving) return;

    setIsLeaving(true);
    try {
      const response = await fetch("/api/organizations/leave", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include",
        body: JSON.stringify({
          organization_id: activeOrganization.id,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(
          errorData.error || `Failed to leave organization: ${response.status}`
        );
      }

      setShowLeaveDialog(false);

      // Redirect to projects page to see the new active organization
      window.location.replace("/projects");
    } catch (error) {
      console.error("Failed to leave organization:", error);
      alert(error.message || "Failed to leave organization. Please try again.");
      setIsLeaving(false);
    }
  }, [activeOrganization, isLeaving]);

  const canLeaveOrganization = useCallback(() => {
    if (!activeOrganization || !currentUser) return false;
    // User cannot leave if they are the creator
    return (
      activeOrganization.created_by !== currentUser.id &&
      organizations.length > 1
    );
  }, [activeOrganization, currentUser, organizations]);

  if (isLoading) {
    return (
      <div className={rootClass.mod({ loading: true }).toString()}>
        <Spinner size={16} />
      </div>
    );
  }

  if (!activeOrganization) {
    return null;
  }

  const dropdownStyle = {
    background: "#000000",
    border: "1px solid #1f2937",
    borderRadius: "8px",
    width: "280px",
    display: "flex",
    flexDirection: "column",
    overflow: "hidden",
    boxShadow: "0 10px 15px -3px rgba(0, 0, 0, 0.5)",
  };

  const itemStyle = {
    display: "flex",
    alignItems: "center",
    height: "36px",
    padding: "0 12px",
    fontSize: "13px",
    color: "#9ca3af",
    cursor: "pointer",
    transition: "all 0.2s ease",
    borderRadius: "4px",
    margin: "0 4px 2px",
    textDecoration: "none",
  };

  const activeItemStyle = {
    ...itemStyle,
    background: "rgba(139, 92, 246, 0.1)",
    color: "#ffffff",
    border: "1px solid rgba(139, 92, 246, 0.2)",
  };

  return (
    <>
      <Dropdown.Trigger
        align="right"
        className="organization-switcher-popover"
        content={
          <div style={dropdownStyle} className="organization-switcher-dropdown">
            {/* Header */}
            <div
              style={{
                padding: "12px 16px 8px",
                fontSize: "11px",
                color: "#6b7280",
                fontFamily: "monospace",
                letterSpacing: "0.1em",
                textTransform: "uppercase",
              }}
            >
              // Switch Organization
            </div>

            {/* Scrollable List */}
            <div
              className="organization-scroll-list"
              style={{
                maxHeight: "240px",
                overflowY: "auto",
                padding: "4px 0",
              }}
            >
              {organizations.map((org) => {
                const isActive = org.id === activeOrganization?.id;
                return (
                  <div
                    key={org.id}
                    className="org-item"
                    style={isActive ? activeItemStyle : itemStyle}
                    onClick={() => !isActive && switchOrganization(org.id)}
                  >
                    <div style={{ width: "20px", display: "flex" }}>
                      {isActive ? (
                        <IconCheck
                          style={{
                            width: "14px",
                            height: "14px",
                            color: "#8b5cf6",
                          }}
                        />
                      ) : (
                        <IconPeople
                          style={{
                            width: "14px",
                            height: "14px",
                            opacity: 0.5,
                          }}
                        />
                      )}
                    </div>
                    <span
                      style={{
                        whiteSpace: "nowrap",
                        overflow: "hidden",
                        textOverflow: "ellipsis",
                      }}
                    >
                      {org.title}
                    </span>
                  </div>
                );
              })}
            </div>

            {/* Footer Actions */}
            <div
              style={{
                borderTop: "1px solid #1f2937",
                padding: "8px 4px",
                marginTop: "4px",
                background: "#0a0a0a",
              }}
            >
              <div
                className="org-item"
                style={itemStyle}
                onClick={() => setShowInviteDialog(true)}
              >
                <div style={{ width: "20px", display: "flex" }}>
                  <IconUserAdd style={{ width: "14px", height: "14px" }} />
                </div>
                Invite Members
              </div>
              <div
                className="org-item"
                style={itemStyle}
                onClick={() => setShowCreateDialog(true)}
              >
                <div style={{ width: "20px", display: "flex" }}>
                  <IconPlus style={{ width: "14px", height: "14px" }} />
                </div>
                Create Organization
              </div>
              {canLeaveOrganization() && (
                <div
                  className="org-item danger"
                  style={{ ...itemStyle, color: "#ef4444" }}
                  onClick={() => setShowLeaveDialog(true)}
                >
                  <div style={{ width: "20px", display: "flex" }}>
                    <IconRemove style={{ width: "14px", height: "14px" }} />
                  </div>
                  Leave Organization
                </div>
              )}
            </div>
          </div>
        }
      >
        <div className={rootClass.elem("trigger").mix(className)}>
          <IconPeople className={rootClass.elem("icon")} />
          <span className={rootClass.elem("name")}>
            {activeOrganization?.title}
          </span>
          {isSwitching && (
            <Spinner size={12} className={rootClass.elem("spinner")} />
          )}
        </div>
      </Dropdown.Trigger>

      <CreateOrganizationDialog
        isOpen={showCreateDialog}
        onClose={() => setShowCreateDialog(false)}
        onSuccess={() => {
          setShowCreateDialog(false);
          loadOrganizations();
        }}
      />
      <InviteMembersDialog
        isOpen={showInviteDialog}
        onClose={() => setShowInviteDialog(false)}
        organizationId={activeOrganization?.id}
      />

      {/* Leave Organization Custom Modal */}
      {showLeaveDialog && (
        <div style={{
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
        }} onClick={(e) => e.target === e.currentTarget && !isLeaving && setShowLeaveDialog(false)}>
          <div style={{
            width: "480px",
            background: "#000000",
            border: "none", // Removed full border
            borderRadius: "0", // Removed radius
            boxShadow: "none", // Removed shadow
            display: "flex",
            flexDirection: "column",
            position: "relative",
          }}>
            {/* Corner Borders */}
            <div style={{
              position: "absolute",
              width: "12px",
              height: "12px",
              borderColor: "#8b5cf6",
              borderStyle: "solid",
              pointerEvents: "none",
              zIndex: 10,
              top: 0, 
              left: 0, 
              borderTopWidth: "2px", 
              borderLeftWidth: "2px", 
              borderRightWidth: 0, 
              borderBottomWidth: 0
            }} />
            <div style={{
              position: "absolute",
              width: "12px",
              height: "12px",
              borderColor: "#8b5cf6",
              borderStyle: "solid",
              pointerEvents: "none",
              zIndex: 10,
              bottom: 0, 
              right: 0, 
              borderBottomWidth: "2px", 
              borderRightWidth: "2px", 
              borderTopWidth: 0, 
              borderLeftWidth: 0
            }} />

            <div style={{
              padding: "20px 24px",
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              borderBottom: "1px solid #1f2937",
              position: "relative", // For header container properties if needed
            }}>
              <h2 style={{
                fontSize: "18px",
                fontWeight: 600,
                color: "#ffffff",
                fontFamily: "'Space Grotesk', sans-serif",
                letterSpacing: "-0.02em",
              }}>Leave Organization</h2>
              <button 
                onClick={() => !isLeaving && setShowLeaveDialog(false)}
                style={{
                  background: "transparent",
                  border: "none",
                  cursor: isLeaving ? "not-allowed" : "pointer",
                  padding: "4px",
                  borderRadius: "4px",
                  color: "#6b7280",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  transition: "all 0.2s",
                }}
                onMouseEnter={(e) => { if(!isLeaving) { e.currentTarget.style.color = "#ffffff"; e.currentTarget.style.background = "rgba(255,255,255,0.1)"; }}}
                onMouseLeave={(e) => { if(!isLeaving) { e.currentTarget.style.color = "#6b7280"; e.currentTarget.style.background = "transparent"; }}}
              >
                <IconCross style={{ width: 20, height: 20 }} />
              </button>
            </div>

            <div style={{ padding: "24px" }}>
              <p style={{ color: "#ffffff", fontSize: "14px", marginBottom: "8px", lineHeight: "1.5" }}>
                Are you sure you want to leave <strong style={{color: "#ef4444"}}>{activeOrganization?.title}</strong>?
              </p>
              <p style={{ color: "#9ca3af", fontSize: "13px", lineHeight: "1.5", margin: 0 }}>
                You will lose access to all projects and data in this organization.
                You can rejoin if someone sends you another invite link.
              </p>
            </div>

            <div style={{ padding: "16px 24px 24px", display: "flex", justifyContent: "flex-end", gap: "12px" }}>
              <button
                onClick={() => setShowLeaveDialog(false)}
                disabled={isLeaving}
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
                onClick={leaveOrganization}
                disabled={isLeaving}
                style={{
                  padding: "8px 16px",
                  background: isLeaving ? "rgba(220, 38, 38, 0.5)" : "linear-gradient(135deg, rgba(239, 68, 68, 0.15), rgba(220, 38, 38, 0.1))", // Red Gradient for Danger (matching Purple Gradient pattern)
                  border: "1px solid rgba(239, 68, 68, 0.5)",
                  borderRadius: "4px",
                  color: "#ef4444", // Text matches border
                  fontSize: "13px",
                  cursor: isLeaving ? "not-allowed" : "pointer",
                  fontFamily: "'Space Grotesk', sans-serif",
                  fontWeight: 600,
                  textTransform: "uppercase",
                  letterSpacing: "0.05em",
                  display: "flex",
                  alignItems: "center",
                  gap: "8px",
                  transition: "all 0.2s",
                  boxShadow: "0 0 10px rgba(239, 68, 68, 0.1)",
                }}
                onMouseEnter={(e) => { 
                  if(!isLeaving) {
                    e.currentTarget.style.background = "linear-gradient(135deg, rgba(239, 68, 68, 0.25), rgba(220, 38, 38, 0.2))";
                    e.currentTarget.style.boxShadow = "0 0 15px rgba(239, 68, 68, 0.2)";
                  }
                }}
                onMouseLeave={(e) => { 
                  if(!isLeaving) {
                    e.currentTarget.style.background = "linear-gradient(135deg, rgba(239, 68, 68, 0.15), rgba(220, 38, 38, 0.1))";
                    e.currentTarget.style.boxShadow = "0 0 10px rgba(239, 68, 68, 0.1)";
                  }
                }}
              >
                {isLeaving && <Spinner size={12} color="#ef4444" />}
                {isLeaving ? "Leaving..." : "Leave Organization"}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};
