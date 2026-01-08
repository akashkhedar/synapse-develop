import { Button } from "@synapse/ui";
import { useCallback, useMemo, useRef, useState } from "react";
import { useUpdatePageTitle } from "@synapse/core";
import { HeidiTips } from "../../../components/HeidiTips/HeidiTips";
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
import { TokenSettingsModal } from "@synapse/app-common/blocks/TokenSettingsModal";
import { IconPlus } from "@synapse/icons";
import { useToast } from "@synapse/ui";
import { InviteLink } from "./InviteLink";
import { SelectedUser } from "./SelectedUser";

export const PeoplePage = () => {
  const apiSettingsModal = useRef();
  const peopleListRef = useRef();
  const toast = useToast();
  const [selectedUser, setSelectedUser] = useState(null);
  const [selectedUserRole, setSelectedUserRole] = useState(null);
  const [invitationOpen, setInvitationOpen] = useState(false);
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  useUpdatePageTitle("People");

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

  const apiTokensSettingsModalProps = useMemo(
    () => ({
      title: "API Token Settings",
      style: { width: 480 },
      body: () => (
        <TokenSettingsModal
          onSaved={() => {
            toast.show({ message: "API Token settings saved" });
            apiSettingsModal.current?.close();
          }}
        />
      ),
    }),
    []
  );

  const showApiTokenSettingsModal = useCallback(() => {
    apiSettingsModal.current = modal(apiTokensSettingsModalProps);
    __lsa("organization.token_settings");
  }, [apiTokensSettingsModalProps]);

  const defaultSelected = useMemo(() => {
    return localStorage.getItem("selectedUser");
  }, []);

  return (
    <div className={cn("people").toClassName()}>
      <div className={cn("people").elem("controls").toClassName()}>
        <Space spread>
          <Space />

          <Space>
            {isFF(FF_AUTH_TOKENS) && (
              <Button
                look="outlined"
                onClick={showApiTokenSettingsModal}
                aria-label="Show API token settings"
              >
                API Tokens Settings
              </Button>
            )}
            <Button
              leading={<IconPlus className="!h-4" />}
              onClick={() => setInvitationOpen(true)}
              aria-label="Invite new member"
            >
              Add Members
            </Button>
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
      <InviteLink
        opened={invitationOpen}
        onClosed={() => {
          console.log("hidden");
          setInvitationOpen(false);
        }}
      />
    </div>
  );
};

PeoplePage.title = "People";
PeoplePage.path = "/";

