import { format } from "date-fns";
import { NavLink } from "react-router-dom";
import { useState, useCallback, useEffect } from "react";
import {
  IconCross,
  IconTrash,
  IconCheck,
  IconUserAdd,
} from "@synapse/icons";
import { Userpic } from "@synapse/ui";
import { Modal } from "../../../components/Modal/ModalPopup";
import { useAPI } from "../../../providers/ApiProvider";
import { cn } from "../../../utils/bem";
import "./SelectedUser.scss";

const UserProjectsLinks = ({ projects }) => {
  return (
    <div className={cn("user-info").elem("links-list").toClassName()}>
      {projects.map((project) => (
        <NavLink
          className={cn("user-info").elem("project-link").toClassName()}
          key={`project-${project.id}`}
          to={`/projects/${project.id}`}
          data-external
        >
          {project.title}
        </NavLink>
      ))}
    </div>
  );
};

export const SelectedUser = ({
  user,
  memberRole,
  onClose,
  onMemberRemoved,
}) => {
  const api = useAPI();
  const [showRemoveDialog, setShowRemoveDialog] = useState(false);
  const [showPromoteDialog, setShowPromoteDialog] = useState(false);
  const [showDemoteDialog, setShowDemoteDialog] = useState(false);
  const [isRemoving, setIsRemoving] = useState(false);
  const [isPromoting, setIsPromoting] = useState(false);
  const [isDemoting, setIsDemoting] = useState(false);
  const [currentUser, setCurrentUser] = useState(null);
  const [activeOrg, setActiveOrg] = useState(null);
  const [currentUserRole, setCurrentUserRole] = useState(null);

  // Load current user and active organization
  useEffect(() => {
    api.callApi("me").then((userData) => {
      setCurrentUser(userData);
      // Fetch active organization details and current user's membership
      fetch(`/api/organizations/${userData.active_organization}/`, {
        credentials: "include",
      })
        .then((res) => res.json())
        .then((orgData) => {
          setActiveOrg(orgData);
          // Fetch current user's role
          return fetch(
            `/api/organizations/${userData.active_organization}/memberships/`,
            {
              credentials: "include",
            }
          );
        })
        .then((res) => res.json())
        .then((membersData) => {
          const currentMember = membersData.results?.find(
            (m) => m.user.id === userData.id
          );
          if (currentMember) {
            setCurrentUserRole(currentMember.role);
          }
        })
        .catch((err) => console.error("Failed to load org data:", err));
    });
  }, []);

  const canRemoveMember = useCallback(() => {
    if (!currentUser || !activeOrg || !user) return false;
    // Owner and admins can remove members, but not the owner, and not themselves
    if (user.id === currentUser.id) return false;
    if (memberRole === "owner") return false;
    return currentUserRole === "owner" || currentUserRole === "admin";
  }, [currentUser, activeOrg, user, currentUserRole, memberRole]);

  const canPromoteMember = useCallback(() => {
    // Only owner can promote regular members to admin
    return currentUserRole === "owner" && memberRole === "member" && user?.id !== currentUser?.id;
  }, [currentUserRole, memberRole, user, currentUser]);

  const canDemoteMember = useCallback(() => {
    // Only owner can demote admins to regular members
    return currentUserRole === "owner" && memberRole === "admin" && user?.id !== currentUser?.id;
  }, [currentUserRole, memberRole, user, currentUser]);

  const removeMember = useCallback(async () => {
    if (isRemoving || !activeOrg || !user) return;

    setIsRemoving(true);
    try {
      const response = await fetch(
        `/api/organizations/${activeOrg.id}/memberships/${user.id}/`,
        {
          method: "DELETE",
          credentials: "include",
        }
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(
          errorData.detail || `Failed to remove member: ${response.status}`
        );
      }

      setShowRemoveDialog(false);
      // Notify parent to refresh the list and close this panel
      if (onMemberRemoved) {
        onMemberRemoved();
      }
      onClose();
    } catch (error) {
      console.error("Failed to remove member:", error);
      alert(error.message || "Failed to remove member. Please try again.");
      setIsRemoving(false);
    }
  }, [user, activeOrg, isRemoving, onClose, onMemberRemoved]);

  const promoteMember = useCallback(async () => {
    if (isPromoting || !activeOrg || !user) return;

    setIsPromoting(true);
    try {
      const response = await fetch(
        `/api/organizations/${activeOrg.id}/memberships/${user.id}/promote`,
        {
          method: "POST",
          credentials: "include",
        }
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(
          errorData.error || `Failed to promote member: ${response.status}`
        );
      }

      setShowPromoteDialog(false);
      // Notify parent to refresh the list
      if (onMemberRemoved) {
        onMemberRemoved();
      }
    } catch (error) {
      console.error("Failed to promote member:", error);
      alert(error.message || "Failed to promote member. Please try again.");
      setIsPromoting(false);
    }
  }, [user, activeOrg, isPromoting, onMemberRemoved]);

  const demoteMember = useCallback(async () => {
    if (isDemoting || !activeOrg || !user) return;

    setIsDemoting(true);
    try {
      const response = await fetch(
        `/api/organizations/${activeOrg.id}/memberships/${user.id}/demote`,
        {
          method: "POST",
          credentials: "include",
        }
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(
          errorData.error || `Failed to demote admin: ${response.status}`
        );
      }

      setShowDemoteDialog(false);
      // Notify parent to refresh the list
      if (onMemberRemoved) {
        onMemberRemoved();
      }
    } catch (error) {
      console.error("Failed to demote admin:", error);
      alert(error.message || "Failed to demote admin. Please try again.");
      setIsDemoting(false);
    }
  }, [user, activeOrg, isDemoting, onMemberRemoved]);

  // Guard against null user - moved after ALL hooks
  if (!user) {
    return null;
  }

  const fullName = [user.first_name, user.last_name]
    .filter((n) => !!n)
    .join(" ")
    .trim();

  const isOwner = currentUserRole === "owner";
  const isTargetOwner = memberRole === "owner";
  const isTargetAdmin = memberRole === "admin";
  const isTargetMember = memberRole === "member";

  const getRoleBadge = () => {
    if (isTargetOwner) {
      return (
        <span
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: "6px",
            padding: "6px 14px",
            borderRadius: "0",
            background: "linear-gradient(135deg, rgba(139, 92, 246, 0.25), rgba(168, 85, 247, 0.15))",
            border: "1px solid rgba(139, 92, 246, 0.5)",
            color: "#c4b5fd",
            fontSize: "11px",
            fontWeight: "600",
            letterSpacing: "0.08em",
            textTransform: "uppercase",
            fontFamily: "'Space Grotesk', system-ui, sans-serif",
          }}
        >
          Owner
        </span>
      );
    }
    if (isTargetAdmin) {
      return (
        <span
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: "6px",
            padding: "6px 14px",
            borderRadius: "0",
            background: "linear-gradient(135deg, rgba(59, 130, 246, 0.2), rgba(96, 165, 250, 0.1))",
            border: "1px solid rgba(59, 130, 246, 0.4)",
            color: "#93c5fd",
            fontSize: "11px",
            fontWeight: "600",
            letterSpacing: "0.08em",
            textTransform: "uppercase",
            fontFamily: "'Space Grotesk', system-ui, sans-serif",
          }}
        >
          Admin
        </span>
      );
    }
    return (
      <span
        style={{
          display: "inline-flex",
          alignItems: "center",
          gap: "6px",
          padding: "6px 14px",
          borderRadius: "0",
          background: "rgba(55, 65, 81, 0.3)",
          border: "1px solid rgba(75, 85, 99, 0.5)",
          color: "#9ca3af",
          fontSize: "11px",
          fontWeight: "600",
          letterSpacing: "0.08em",
          textTransform: "uppercase",
          fontFamily: "'Space Grotesk', system-ui, sans-serif",
        }}
      >
        Member
      </span>
    );
  };

  return (
    <div className={cn("user-info").toClassName()}>
      {/* Corner Borders */}
      <div style={{ position: "absolute", width: "12px", height: "12px", top: 0, left: 0, borderColor: "#8b5cf6", borderStyle: "solid", borderTopWidth: "2px", borderLeftWidth: "2px", borderRightWidth: 0, borderBottomWidth: 0, pointerEvents: "none", zIndex: 10 }} />
      <div style={{ position: "absolute", width: "12px", height: "12px", bottom: 0, right: 0, borderColor: "#8b5cf6", borderStyle: "solid", borderBottomWidth: "2px", borderRightWidth: "2px", borderTopWidth: 0, borderLeftWidth: 0, pointerEvents: "none", zIndex: 10 }} />

      <button
        onClick={onClose}
        style={{
          position: "absolute",
          top: "20px",
          right: "24px",
          background: "transparent",
          border: "none",
          padding: "4px",
          borderRadius: "4px",
          color: "#6b7280",
          cursor: "pointer",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          transition: "all 0.2s",
        }}
        onMouseEnter={(e) => { e.currentTarget.style.color = "#ffffff"; e.currentTarget.style.background = "rgba(255,255,255,0.1)"; }}
        onMouseLeave={(e) => { e.currentTarget.style.color = "#6b7280"; e.currentTarget.style.background = "transparent"; }}
        aria-label="Close user details"
      >
        <IconCross style={{ width: 20, height: 20 }} />
      </button>

      <div className={cn("user-info").elem("header").toClassName()}>
        <Userpic user={user} style={{ width: 64, height: 64, fontSize: 28 }} />
        <div className={cn("user-info").elem("info-wrapper").toClassName()}>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "12px",
              marginBottom: "4px",
            }}
          >
            {fullName && (
              <div className={cn("user-info").elem("full-name").toClassName()}>
                {fullName}
              </div>
            )}
            {getRoleBadge()}
          </div>
          <p className={cn("user-info").elem("email").toClassName()}>
            {user.email}
          </p>
        </div>
      </div>

      {user.phone && (
        <div className={cn("user-info").elem("section").toClassName()}>
          <a href={`tel:${user.phone}`}>{user.phone}</a>
        </div>
      )}

      {!!user.created_projects.length && (
        <div className={cn("user-info").elem("section").toClassName()}>
          <div className={cn("user-info").elem("section-title").toClassName()}>
            Created Projects
          </div>

          <UserProjectsLinks projects={user.created_projects} />
        </div>
      )}

      {!!user.contributed_to_projects.length && (
        <div className={cn("user-info").elem("section").toClassName()}>
          <div className={cn("user-info").elem("section-title").toClassName()}>
            Contributed to
          </div>

          <UserProjectsLinks projects={user.contributed_to_projects} />
        </div>
      )}

      <p className={cn("user-info").elem("last-active").toClassName()}>
        Last activity on:{" "}
        {format(new Date(user.last_activity), "dd MMM yyyy, KK:mm a")}
      </p>

      {(canRemoveMember() || canPromoteMember() || canDemoteMember()) && (
        <div
          className={cn("user-info").elem("actions").toClassName()}
          style={{
            marginTop: "24px",
            paddingTop: "24px",
            borderTop: "1px solid rgba(139, 92, 246, 0.15)",
            display: "flex",
            flexDirection: "column",
            gap: "12px",
          }}
        >
          {canPromoteMember() && (
            <button
              onClick={() => setShowPromoteDialog(true)}
              aria-label="Promote to admin"
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                gap: "10px",
                width: "100%",
                padding: "14px 20px",
                background: "linear-gradient(135deg, rgba(139, 92, 246, 0.2), rgba(168, 85, 247, 0.12))",
                border: "1px solid rgba(139, 92, 246, 0.4)",
                borderRadius: "0",
                color: "#c4b5fd",
                fontSize: "13px",
                fontWeight: "600",
                letterSpacing: "0.04em",
                textTransform: "uppercase",
                fontFamily: "'Space Grotesk', system-ui, sans-serif",
                cursor: "pointer",
                transition: "all 0.2s ease",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.background = "linear-gradient(135deg, rgba(139, 92, 246, 0.3), rgba(168, 85, 247, 0.18))";
                e.currentTarget.style.borderColor = "rgba(139, 92, 246, 0.6)";
                e.currentTarget.style.color = "#ffffff";
                e.currentTarget.style.boxShadow = "0 4px 16px rgba(139, 92, 246, 0.25)";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = "linear-gradient(135deg, rgba(139, 92, 246, 0.2), rgba(168, 85, 247, 0.12))";
                e.currentTarget.style.borderColor = "rgba(139, 92, 246, 0.4)";
                e.currentTarget.style.color = "#c4b5fd";
                e.currentTarget.style.boxShadow = "none";
              }}
            >
              <IconCheck style={{ width: 16, height: 16 }} />
              Make Admin
            </button>
          )}
          {canDemoteMember() && (
            <button
              onClick={() => setShowDemoteDialog(true)}
              aria-label="Demote to member"
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                gap: "10px",
                width: "100%",
                padding: "14px 20px",
                background: "transparent",
                border: "1px solid rgba(75, 85, 99, 0.5)",
                borderRadius: "0",
                color: "#9ca3af",
                fontSize: "13px",
                fontWeight: "600",
                letterSpacing: "0.04em",
                textTransform: "uppercase",
                fontFamily: "'Space Grotesk', system-ui, sans-serif",
                cursor: "pointer",
                transition: "all 0.2s ease",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.borderColor = "rgba(139, 92, 246, 0.5)";
                e.currentTarget.style.color = "#c4b5fd";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.borderColor = "rgba(75, 85, 99, 0.5)";
                e.currentTarget.style.color = "#9ca3af";
              }}
            >
              <IconUserAdd style={{ width: 16, height: 16 }} />
              Remove Admin Role
            </button>
          )}
          {canRemoveMember() && (
            <button
              onClick={() => setShowRemoveDialog(true)}
              aria-label="Remove member from organization"
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                gap: "10px",
                width: "100%",
                padding: "14px 20px",
                background: "rgba(239, 68, 68, 0.1)",
                border: "1px solid rgba(239, 68, 68, 0.3)",
                borderRadius: "0",
                color: "#fca5a5",
                fontSize: "13px",
                fontWeight: "600",
                letterSpacing: "0.04em",
                textTransform: "uppercase",
                fontFamily: "'Space Grotesk', system-ui, sans-serif",
                cursor: "pointer",
                transition: "all 0.2s ease",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.background = "rgba(239, 68, 68, 0.18)";
                e.currentTarget.style.borderColor = "rgba(239, 68, 68, 0.5)";
                e.currentTarget.style.color = "#f87171";
                e.currentTarget.style.boxShadow = "0 4px 16px rgba(239, 68, 68, 0.2)";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = "rgba(239, 68, 68, 0.1)";
                e.currentTarget.style.borderColor = "rgba(239, 68, 68, 0.3)";
                e.currentTarget.style.color = "#fca5a5";
                e.currentTarget.style.boxShadow = "none";
              }}
            >
              <IconTrash style={{ width: 16, height: 16 }} />
              Remove from Organization
            </button>
          )}
        </div>
      )}

      <Modal
        visible={showPromoteDialog}
        title="Promote to Admin"
        onHide={() => !isPromoting && setShowPromoteDialog(false)}
        footer={
          <>
            <button
              className="ls-button ls-button_look_secondary"
              onClick={() => setShowPromoteDialog(false)}
              disabled={isPromoting}
            >
              Cancel
            </button>
            <button
              className="ls-button ls-button_look_primary"
              onClick={promoteMember}
              disabled={isPromoting}
            >
              {isPromoting ? "Promoting..." : "Make Admin"}
            </button>
          </>
        }
      >
        <p style={{ marginBottom: "16px" }}>
          Are you sure you want to promote{" "}
          <strong>{fullName || user.email}</strong> to Admin?
        </p>
        <p style={{ marginBottom: "0", color: "#718096" }}>
          Admins can remove other members (but not you as the owner). You can
          demote them back to regular member anytime.
        </p>
      </Modal>

      <Modal
        visible={showDemoteDialog}
        title="Remove Admin Role"
        onHide={() => !isDemoting && setShowDemoteDialog(false)}
        footer={
          <>
            <button
              className="ls-button ls-button_look_secondary"
              onClick={() => setShowDemoteDialog(false)}
              disabled={isDemoting}
            >
              Cancel
            </button>
            <button
              className="ls-button ls-button_look_primary"
              onClick={demoteMember}
              disabled={isDemoting}
            >
              {isDemoting ? "Demoting..." : "Remove Admin Role"}
            </button>
          </>
        }
      >
        <p style={{ marginBottom: "16px" }}>
          Are you sure you want to demote{" "}
          <strong>{fullName || user.email}</strong> to regular member?
        </p>
        <p style={{ marginBottom: "0", color: "#718096" }}>
          They will no longer be able to manage other members. You can promote
          them back to admin anytime.
        </p>
      </Modal>

      <Modal
        visible={showRemoveDialog}
        title="Remove Member"
        onHide={() => !isRemoving && setShowRemoveDialog(false)}
        footer={
          <>
            <button
              className="ls-button ls-button_look_secondary"
              onClick={() => setShowRemoveDialog(false)}
              disabled={isRemoving}
            >
              Cancel
            </button>
            <button
              className="ls-button ls-button_look_danger"
              onClick={removeMember}
              disabled={isRemoving}
            >
              {isRemoving ? "Removing..." : "Remove Member"}
            </button>
          </>
        }
      >
        <p style={{ marginBottom: "16px" }}>
          Are you sure you want to remove{" "}
          <strong>{fullName || user.email}</strong> from this organization?
        </p>
        <p style={{ marginBottom: "0", color: "#718096" }}>
          They will lose access to all projects and data. They can rejoin if you
          send them another invite link.
        </p>
      </Modal>
    </div>
  );
};

