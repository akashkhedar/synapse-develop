import { useCallback, useEffect, useState } from "react";
import { Dropdown, Spinner } from "@synapse/ui";
import { IconPeople, IconCheck, IconPlus, IconUserAdd, IconRemove } from "@synapse/icons";
import { useAPI } from "../../providers/ApiProvider";
import { cn } from "../../utils/bem";
import { Menu } from "../Menu/Menu";
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
      const response = await fetch('/api/organizations/', {
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
      });
      
      if (!response.ok) {
        throw new Error(`Failed to fetch organizations: ${response.status}`);
      }
      
      const data = await response.json();
      const orgs = data?.results || data || [];
      setOrganizations(orgs);
      
      // Find active organization by ID from user data
      const active = orgs.find(org => org.id === activeOrgId) || orgs[0];
      setActiveOrganization(active);
    } catch (error) {
      console.error("Failed to load organizations:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const switchOrganization = useCallback(async (orgId) => {
    if (isSwitching || activeOrganization?.id === orgId) return;

    setIsSwitching(true);
    try {
      const response = await fetch('/api/organizations/switch', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          organization_id: orgId,
        }),
      });

      if (!response.ok) {
        throw new Error(`Failed to switch organization: ${response.status}`);
      }

      // Force navigation to projects page to ensure fresh data load with new organization context
      // Use replace to avoid browser cache issues
      window.location.replace('/projects');
    } catch (error) {
      console.error("Failed to switch organization:", error);
      setIsSwitching(false);
    }
  }, [activeOrganization, isSwitching]);

  const leaveOrganization = useCallback(async () => {
    if (isLeaving) return;

    setIsLeaving(true);
    try {
      const response = await fetch('/api/organizations/leave', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          organization_id: activeOrganization.id,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.error || `Failed to leave organization: ${response.status}`);
      }

      const result = await response.json();
      setShowLeaveDialog(false);
      
      // Redirect to projects page to see the new active organization
      window.location.replace('/projects');
    } catch (error) {
      console.error("Failed to leave organization:", error);
      alert(error.message || "Failed to leave organization. Please try again.");
      setIsLeaving(false);
    }
  }, [activeOrganization, isLeaving]);

  const canLeaveOrganization = useCallback(() => {
    if (!activeOrganization || !currentUser) return false;
    // User cannot leave if they are the creator
    return activeOrganization.created_by !== currentUser.id && organizations.length > 1;
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

  return (
    <>
      <Dropdown.Trigger
        align="right"
        className={rootClass.toString()}
        content={
          <Menu>
            <Menu.Group title="Switch Organization">
              {organizations.map((org) => {
                const isActive = org.id === activeOrganization?.id;
                return (
                  <Menu.Item
                    key={org.id}
                    icon={isActive ? <IconCheck /> : <IconPeople />}
                    label={org.title}
                    onClick={() => !isActive && switchOrganization(org.id)}
                    active={isActive}
                    disabled={isSwitching}
                  />
                );
              })}
            </Menu.Group>
            <Menu.Divider />
            <Menu.Item
              icon={<IconUserAdd />}
              label="Invite Members"
              onClick={() => setShowInviteDialog(true)}
            />
            <Menu.Item
              icon={<IconPlus />}
              label="Create Organization"
              onClick={() => setShowCreateDialog(true)}
            />
            {canLeaveOrganization() && (
              <>
                <Menu.Divider />
                <Menu.Item
                  icon={<IconRemove />}
                  label="Leave Organization"
                  onClick={() => setShowLeaveDialog(true)}
                  danger
                />
              </>
            )}
          </Menu>
        }
      >
        <div className={rootClass.elem("trigger")}>
          <IconPeople className={rootClass.elem("icon")} />
          <span className={rootClass.elem("name")}>{activeOrganization?.title}</span>
          {isSwitching && <Spinner size={12} className={rootClass.elem("spinner")} />}
        </div>
      </Dropdown.Trigger>
      <CreateOrganizationDialog
        isOpen={showCreateDialog}
        onClose={() => setShowCreateDialog(false)}
        onSuccess={(newOrg) => {
          setShowCreateDialog(false);
          loadOrganizations();
        }}
      />
      <InviteMembersDialog
        isOpen={showInviteDialog}
        onClose={() => setShowInviteDialog(false)}
        organizationId={activeOrganization?.id}
      />
      <Modal
        visible={showLeaveDialog}
        title="Leave Organization"
        onHide={() => !isLeaving && setShowLeaveDialog(false)}
        footer={
          <>
            <button
              className="ls-button ls-button_look_secondary"
              onClick={() => setShowLeaveDialog(false)}
              disabled={isLeaving}
            >
              Cancel
            </button>
            <button
              className="ls-button ls-button_look_danger"
              onClick={leaveOrganization}
              disabled={isLeaving}
            >
              {isLeaving ? "Leaving..." : "Leave Organization"}
            </button>
          </>
        }
      >
        <p style={{ marginBottom: '16px' }}>
          Are you sure you want to leave <strong>{activeOrganization?.title}</strong>?
        </p>
        <p style={{ marginBottom: '0', color: '#718096' }}>
          You will lose access to all projects and data in this organization.
          You can rejoin if someone sends you another invite link.
        </p>
      </Modal>
    </>
  );
};

