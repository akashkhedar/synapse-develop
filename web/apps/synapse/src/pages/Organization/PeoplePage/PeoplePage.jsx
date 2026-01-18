import { Button } from "@synapse/ui";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useUpdatePageTitle } from "@synapse/core";
import { modal } from "../../../components/Modal/Modal";
import { Space } from "../../../components/Space/Space";
import { cn } from "../../../utils/bem";
import {
  FF_AUTH_TOKENS,
  FF_LSDV_E_297,
  isFF,
} from "../../../utils/feature-flags";
import "./PeopleInvitation.scss";
import { PeopleList } from "./PeopleList";
import "./PeoplePage.scss";
import { OrganizationApiKeyModal } from "./OrganizationApiKeyModal";
import { IconPlus, IconInfoOutline } from "@synapse/icons";
import { InviteMembersDialog } from "../../../components/InviteMembersDialog/InviteMembersDialog";
import { useAuth } from "@synapse/core/providers/AuthProvider";
import { useToast } from "@synapse/ui";
import { SelectedUser } from "./SelectedUser";
import { useAPI } from "../../../providers/ApiProvider";

export const PeoplePage = () => {
  const api = useAPI();
  const peopleListRef = useRef();
  const toast = useToast();
  const [selectedUser, setSelectedUser] = useState(null);
  const [selectedUserRole, setSelectedUserRole] = useState(null);
  const [invitationOpen, setInvitationOpen] = useState(false);
  const [apiKeyModalOpen, setApiKeyModalOpen] = useState(false);
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  const [currentUserRole, setCurrentUserRole] = useState(null);
  const { user } = useAuth();
  // Ensure we get the ID correctly, handling potential object structure variations
  const organizationId = user?.active_organization?.id || user?.active_organization;

  // Check if current user is admin or owner
  const canManageApiKey = currentUserRole === 'owner' || currentUserRole === 'admin';

  useUpdatePageTitle("People");

  // Fetch current user's role in the organization
  useEffect(() => {
    const fetchUserRole = async () => {
      if (!organizationId || !user?.id) return;
      try {
        const response = await api.callApi("memberships", {
          params: { pk: organizationId }
        });
        const membership = response.results?.find(m => m.user.id === user.id);
        if (membership) {
          setCurrentUserRole(membership.role);
        }
      } catch (err) {
        console.error("Failed to fetch user role:", err);
      }
    };
    fetchUserRole();
  }, [api, organizationId, user?.id]);

  const selectUser = useCallback(
    (user, role) => {
      setSelectedUser(user);
      setSelectedUserRole(role);

      localStorage.setItem("selectedUser", user?.id);
    },
    [setSelectedUser, setSelectedUserRole]
  );

  const handleMemberRemoved = useCallback(() => {
    // Trigger refresh of the people list
    setRefreshTrigger((prev) => prev + 1);
  }, []);

  const showApiKeyModal = useCallback(() => {
    setApiKeyModalOpen(true);
    __lsa("organization.api_key");
  }, []);

  const defaultSelected = useMemo(() => {
    return localStorage.getItem("selectedUser");
  }, []);

  // Premium button style matching design system
  const buttonStyle = {
    background: 'rgba(139, 92, 246, 0.15)',
    border: '1px solid rgba(139, 92, 246, 0.3)',
    borderRadius: '10px',
    color: '#c4b5fd',
    fontWeight: 600,
    fontSize: '13px',
    fontFamily: "'Space Grotesk', system-ui, sans-serif",
    height: '34px',
    padding: '0 16px',
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '8px',
    transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
  };

  return (
    <div className={cn("people").toClassName()}>
      <div className={cn("people").elem("controls").toClassName()}>
        <Space spread>
          <Space />

          <Space>
            {/* API Key button - only for admins and owners */}
            {canManageApiKey && (
              <button
                onClick={showApiKeyModal}
                aria-label="Organization API Key"
                style={buttonStyle}
              >
                <IconInfoOutline className="!h-4 !w-4" />
                API Key
              </button>
            )}
            <button
              onClick={() => setInvitationOpen(true)}
              aria-label="Invite new member"
              style={buttonStyle}
            >
              <IconPlus className="!h-4 !w-4" />
              Add Members
            </button>
          </Space>
        </Space>
      </div>
      <div className={cn("people").elem("content").toClassName()}>
        <PeopleList
          ref={peopleListRef}
          selectedUser={selectedUser}
          defaultSelected={defaultSelected}
          onSelect={(user, role) => selectUser(user, role)}
          refreshTrigger={refreshTrigger}
        />

        <SelectedUser
          user={selectedUser}
          memberRole={selectedUserRole}
          onClose={() => selectUser(null, null)}
          onMemberRemoved={handleMemberRemoved}
        />
      </div>
      <InviteMembersDialog
        isOpen={invitationOpen}
        onClose={() => setInvitationOpen(false)}
        organizationId={organizationId}
      />
      
      {/* API Key Modal */}
      {apiKeyModalOpen && (
        <div 
          className="modal-overlay"
          onClick={(e) => {
            if (e.target === e.currentTarget) setApiKeyModalOpen(false);
          }}
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(0, 0, 0, 0.7)',
            backdropFilter: 'blur(8px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
          }}
        >
          <div style={{
            background: 'linear-gradient(135deg, #0a0a0a 0%, #111111 100%)',
            border: '1px solid rgba(139, 92, 246, 0.3)',
            borderRadius: '16px',
            boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5), 0 0 40px rgba(139, 92, 246, 0.15)',
          }}>
            <OrganizationApiKeyModal
              organizationId={organizationId}
              onClose={() => setApiKeyModalOpen(false)}
              onSaved={() => {
                toast.show({ message: "API Key updated successfully" });
              }}
            />
          </div>
        </div>
      )}
    </div>
  );
};

PeoplePage.title = "People";
PeoplePage.path = "/";
