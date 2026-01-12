import { Card, CardHeader, CardTitle, CardContent, CardDescription } from "@synapse/ui/lib/card-new/card";
import { useMemo, isValidElement, useState, useEffect } from "react";
import { Redirect, Route, Switch, useParams, useRouteMatch } from "react-router-dom";
import { useUpdatePageTitle, createTitleFromSegments, getApiInstance } from "@synapse/core";
import styles from "./AccountSettings.module.scss";
import { accountSettingsSections, ROLES } from "./sections";
import { HotkeysHeaderButtons } from "./sections/Hotkeys";
import clsx from "clsx";
import { useAtomValue } from "jotai";
import { settingsAtom } from "./atoms";
import { useAuth } from "@synapse/core/providers/AuthProvider";
import { useQuery } from "@tanstack/react-query";
import type { WrappedResponse } from "@synapse/core/lib/api-proxy/types";

/**
 * FIXME: This is legacy imports. We're not supposed to use such statements
 * each one of these eventually has to be migrated to core/ui
 */
import { SidebarMenu } from "apps/synapse/src/components/SidebarMenu/SidebarMenu";

// Hook to get user's role in the organization
const useUserRole = () => {
  const { user } = useAuth();

  const membership = useQuery({
    queryKey: [user?.active_organization, user?.id, "user-membership-role"],
    enabled: !!user,
    async queryFn() {
      if (!user) return null;
      const api = getApiInstance();
      const response = (await api.invoke("userMemberships", {
        pk: user.active_organization,
        userPk: user.id,
      })) as WrappedResponse<{
        role: string;
      }>;

      return response.role || null;
    },
  });

  return {
    role: membership.data,
    isLoading: membership.isLoading,
    isAnnotator: membership.data === ROLES.ANNOTATOR,
    isAdmin: membership.data === ROLES.ADMIN || membership.data === ROLES.OWNER,
    isManager: membership.data === ROLES.MANAGER,
    isReviewer: membership.data === ROLES.REVIEWER,
  };
};

const AccountSettingsSection = () => {
  const { user, permissions } = useAuth();
  const { sectionId } = useParams<{ sectionId: string }>();
  const settings = useAtomValue(settingsAtom);
  const { role, isLoading: roleLoading } = useUserRole();
  const contentClassName = clsx(styles.accountSettings__content, {
    [styles.accountSettingsPadding]: window.APP_SETTINGS.billing !== undefined,
  });

  const resolvedSections = useMemo(() => {
    // Get settings data, or null if there's an error (e.g., annotator without token permissions)
    const settingsData = settings.data && !("error" in settings.data) ? settings.data : null;
    return accountSettingsSections(settingsData, permissions, role || undefined);
  }, [settings.data, permissions, role]);

  const currentSection = useMemo(
    () => resolvedSections.find((section) => section.id === sectionId),
    [resolvedSections, sectionId],
  );

  // Update page title to reflect the current section
  const pageTitleText = useMemo(() => {
    if (!currentSection) return "My Account";

    // If title is a string, use it directly
    if (typeof currentSection.title === "string") {
      return createTitleFromSegments([currentSection.title, "My Account"]);
    }

    // For non-string titles (like JSX elements), derive from the section ID
    const titleFromId = currentSection.id
      .split("-")
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(" ");

    return createTitleFromSegments([titleFromId, "My Account"]);
  }, [currentSection]);

  useUpdatePageTitle(pageTitleText);

  if (!currentSection && resolvedSections.length > 0) {
    return <Redirect to={`${AccountSettingsPage.path}/${resolvedSections[0].id}`} />;
  }

  return currentSection ? (
    <div className={contentClassName}>
      <Card key={currentSection.id} className={styles.accountCard}>
        <CardHeader className={styles.cardHeader}>
          <div className="flex flex-col gap-tight">
            <div className="flex justify-between items-center">
              <div className={styles.sectionNumber}>
                {String(resolvedSections.findIndex((s) => s.id === currentSection.id) + 1).padStart(2, "0")}/
              </div>
              <CardTitle className={styles.cardTitle}>{currentSection.title}</CardTitle>
              {currentSection.id === "hotkeys" && (
                <div className="flex-shrink-0">
                  <HotkeysHeaderButtons />
                </div>
              )}
            </div>
            {currentSection.description && (
              <CardDescription className={styles.cardDescription}>
                {isValidElement(currentSection.description) ? (
                  currentSection.description
                ) : (
                  <currentSection.description />
                )}
              </CardDescription>
            )}
          </div>
        </CardHeader>
        <CardContent className={styles.cardContent}>
          <currentSection.component />
        </CardContent>
      </Card>
    </div>
  ) : null;
};

const AccountSettingsPage = () => {
  const settings = useAtomValue(settingsAtom);
  const match = useRouteMatch();
  const { sectionId } = useParams<{ sectionId: string }>();
  const { user, permissions } = useAuth();
  const { role, isAnnotator, isLoading: roleLoading } = useUserRole();

  const resolvedSections = useMemo(() => {
    // Get settings data, or null if there's an error (e.g., annotator without token permissions)
    const settingsData = settings.data && !("error" in settings.data) ? settings.data : null;
    return accountSettingsSections(settingsData, permissions, role || undefined);
  }, [settings.data, permissions, role]);

  const menuItems = useMemo(
    () =>
      resolvedSections.map(({ title, id }, index) => ({
        title,
        path: `/${id}`,
        active: sectionId === id,
        exact: true,
        icon: (
          <span className={styles.menuItemNumber}>
            {String(index + 1).padStart(2, "0")}
          </span>
        ),
      })),
    [resolvedSections, sectionId],
  );

  return (
    <div className={styles.accountSettings}>
      <div className={styles.pageHeader}>
        <div className={styles.pageHeaderContent}>
          <h1 className={styles.pageTitle}>Account Settings</h1>
          {isAnnotator && (
            <span className={styles.roleBadge}>Annotator</span>
          )}
        </div>
      </div>
      <SidebarMenu menuItems={menuItems} path={AccountSettingsPage.path}>
        <Switch>
          <Route path={`${match.path}/:sectionId`} component={AccountSettingsSection} />
          <Route exact path={match.path}>
            {resolvedSections.length > 0 && <Redirect to={`${match.path}/${resolvedSections[0].id}`} />}
          </Route>
        </Switch>
      </SidebarMenu>
    </div>
  );
};

AccountSettingsPage.title = "My Account";
AccountSettingsPage.path = "/user/account";
AccountSettingsPage.exact = false;
AccountSettingsPage.routes = () => [
  {
    title: () => "My Account",
    path: "/account",
    component: () => <Redirect to={AccountSettingsPage.path} />,
  },
  {
    path: `${AccountSettingsPage.path}/:sectionId?`,
    component: AccountSettingsPage,
  },
];

export { AccountSettingsPage };

