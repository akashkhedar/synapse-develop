import { format } from "date-fns";
import { NavLink } from "react-router-dom";
import { useState, useCallback, useEffect } from "react";
import {
  IconCross,
  IconTrash,
  IconCheck,
  IconUserAdd,
} from "@synapse/icons";
import { Userpic, Button } from "@synapse/ui";
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
            gap: "4px",
            padding: "4px 12px",
            borderRadius: "12px",
            backgroundColor: "#FFD700",
            color: "#000",
            fontSize: "12px",
            fontWeight: "600",
          }}
        >
          👑 Owner
        </span>
      );
    }
    if (isTargetAdmin) {
      return (
        <span
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: "4px",
            padding: "4px 12px",
            borderRadius: "12px",
            backgroundColor: "#3B82F6",
            color: "#fff",
            fontSize: "12px",
            fontWeight: "600",
          }}
        >
          ⭐ Admin
        </span>
      );
    }
    return (
      <span
        style={{
          display: "inline-flex",
          alignItems: "center",
          gap: "4px",
          padding: "4px 12px",
          borderRadius: "12px",
          backgroundColor: "#E5E7EB",
          color: "#4B5563",
          fontSize: "12px",
          fontWeight: "500",
        }}
      >
        👤 Member
      </span>
    );
  };

  return (
    <div className={cn("user-info").toClassName()}>
      <Button
        look="string"
        onClick={onClose}
        className="absolute top-[20px] right-[24px]"
        aria-label="Close user details"
      >
        <IconCross />
      </Button>

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
            borderTop: "1px solid #e2e8f0",
            display: "flex",
            flexDirection: "column",
            gap: "12px",
          }}
        >
          {canPromoteMember() && (
            <Button
              look="primary"
              icon={<IconCheck />}
              onClick={() => setShowPromoteDialog(true)}
              aria-label="Promote to admin"
            >
              Make Admin
            </Button>
          )}
          {canDemoteMember() && (
            <Button
              look="secondary"
              icon={<IconUserAdd />}
              onClick={() => setShowDemoteDialog(true)}
              aria-label="Demote to member"
            >
              Remove Admin Role
            </Button>
          )}
          {canRemoveMember() && (
            <Button
              look="destructive"
              icon={<IconTrash />}
              onClick={() => setShowRemoveDialog(true)}
              aria-label="Remove member from organization"
            >
              Remove from Organization
            </Button>
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

