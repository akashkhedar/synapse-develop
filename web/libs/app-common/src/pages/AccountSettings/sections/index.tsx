import { PersonalInfo } from "./PersonalInfo";
import { PersonalAccessToken, PersonalAccessTokenDescription } from "./PersonalAccessToken";
import { MembershipInfo } from "./MembershipInfo";
import { HotkeysManager } from "./Hotkeys";
import type React from "react";
import { PersonalJWTToken } from "./PersonalJWTToken";
import type { AuthTokenSettings } from "../types";
import { ABILITY, type AuthPermissions } from "@synapse/core/providers/AuthProvider";
import { ff } from "@synapse/core";
import { Badge } from "@synapse/ui";

export type SectionType = {
  title: string | React.ReactNode;
  id: string;
  component: React.FC;
  description?: React.FC | React.ReactNode;
  roles?: string[]; // Optional: restrict to specific roles
};

// Role codes from MembershipInfo
export const ROLES = {
  OWNER: "OW",
  ADMIN: "AD",
  MANAGER: "MA",
  ANNOTATOR: "AN",
  REVIEWER: "RE",
  PENDING: "NO",
  DEACTIVATED: "DI",
} as const;

// Sections available to all users
const commonSections = (): SectionType[] => [
  {
    title: "Personal Info",
    id: "personal-info",
    component: PersonalInfo,
    description: () => "Manage your profile information and avatar.",
  },
  {
    title: (
      <div className="flex items-center gap-tight">
        <span>Hotkeys</span>
        <Badge variant="beta">Beta</Badge>
      </div>
    ),
    id: "hotkeys",
    component: HotkeysManager,
    description: () =>
      "Customize your keyboard shortcuts to speed up your workflow. Click on any hotkey below to assign a new key combination that works best for you.",
  },
];

// Sections only for non-annotator roles (Owner, Admin, Manager)
const adminSections = (): SectionType[] => [
  {
    title: "Membership Info",
    id: "membership-info",
    component: MembershipInfo,
    description: () => "View your organization membership details and statistics.",
    roles: [ROLES.OWNER, ROLES.ADMIN, ROLES.MANAGER, ROLES.REVIEWER],
  },
];

// Annotator-specific sections
const annotatorSections = (): SectionType[] => [
  {
    title: "My Activity",
    id: "membership-info",
    component: MembershipInfo,
    description: () => "View your annotation statistics and contributions.",
    roles: [ROLES.ANNOTATOR],
  },
];

export const accountSettingsSections = (
  settings: AuthTokenSettings | null,
  permissions: AuthPermissions,
  userRole?: string
): SectionType[] => {
  const canCreateTokens = permissions.can(ABILITY.can_create_tokens);
  const isAnnotator = userRole === ROLES.ANNOTATOR;

  // Base sections available to all
  const sections: SectionType[] = [...commonSections()];

  // Add role-specific sections
  if (isAnnotator) {
    sections.push(...annotatorSections());
  } else {
    sections.push(...adminSections());
  }

  // Token sections - only for users with permission (typically not annotators)
  // Settings might be null if the user doesn't have permission to access token settings
  if (settings?.api_tokens_enabled && canCreateTokens && ff.isActive(ff.FF_AUTH_TOKENS)) {
    sections.push({
      title: "Personal Access Token",
      id: "personal-access-token",
      component: PersonalJWTToken,
      description: PersonalAccessTokenDescription,
    });
  }

  if (settings?.legacy_api_tokens_enabled && canCreateTokens) {
    sections.push({
      title: ff.isActive(ff.FF_AUTH_TOKENS) ? "Legacy Token" : "Access Token",
      id: "legacy-token",
      component: PersonalAccessToken,
      description: PersonalAccessTokenDescription,
    });
  }

  return sections;
};

