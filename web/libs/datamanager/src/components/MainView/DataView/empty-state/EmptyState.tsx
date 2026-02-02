import React, { type FC, type ReactNode } from "react";
import {
  IconUpload,
  IconLsLabeling,
  IconCheck,
  IconSearch,
  IconInbox,
  IconCloudProviderS3,
  IconCloudProviderGCS,
  IconCloudProviderAzure,
  IconCloudProviderRedis,
} from "@synapse/icons";
import { Button, IconExternal, Typography, Tooltip } from "@synapse/ui";
import { getDocsUrl } from "../../../../../../editor/src/utils/docs";
import { ABILITY, useAuth } from "@synapse/core/providers/AuthProvider";

declare global {
  interface Window {
    APP_SETTINGS?: {
      whitelabel_is_active?: boolean;
      user?: {
        is_annotator?: boolean;
        is_expert?: boolean;
      };
    };
  }
}

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

const outlineButtonStyle = {
  ...primaryButtonStyle,
  background: "transparent",
  color: "#8b5cf6",
};

// TypeScript interfaces for props
interface EmptyStateProps {
  canImport: boolean;
  onOpenSourceStorageModal?: () => void;
  onOpenImportModal?: () => void;
  // Role-based props (optional)
  userRole?: string;
  project?: {
    assignment_settings?: {
      label_stream_task_distribution?: "auto_distribution" | "assigned_only" | string;
    };
  };
  hasData?: boolean;
  hasFilters?: boolean;
  canLabel?: boolean;
  canAnnotate?: boolean;
  onLabelAllTasks?: () => void;
  onClearFilters?: () => void;
}

// Internal helper interfaces and types
interface EmptyStateLayoutProps {
  icon: ReactNode;
  iconBackground?: string;
  iconColor?: string;
  title: string;
  description: string;
  actions?: ReactNode;
  additionalContent?: ReactNode;
  footer?: ReactNode;
  testId?: string;
  ariaLabelledBy?: string;
  ariaDescribedBy?: string;
  wrapperClassName?: string;
}

// Internal helper function to render common empty state structure
const renderEmptyStateLayout = ({
  icon,
  iconBackground = "bg-primary-emphasis",
  iconColor = "text-primary-icon",
  title,
  description,
  actions,
  additionalContent,
  footer,
  testId,
  ariaLabelledBy,
  ariaDescribedBy,
  wrapperClassName = "w-full h-full flex flex-col items-center justify-center text-center p-wide",
}: EmptyStateLayoutProps) => {
  // Clone the icon and ensure it has consistent 40x40 size
  const iconWithSize = React.cloneElement(icon as React.ReactElement, {
    width: 40,
    height: 40,
  });

  const content = (
    <div className={wrapperClassName}>
      <div className={`flex items-center justify-center ${iconBackground} ${iconColor} rounded-full p-tight mb-4`}>
        {iconWithSize}
      </div>

      <Typography variant="headline" size="medium" className="mb-tight" id={ariaLabelledBy}>
        {title}
      </Typography>

      <Typography
        size="medium"
        className={`text-neutral-content-subtler max-w-xl ${actions || additionalContent ? "mb-tight" : ""}`}
        id={ariaDescribedBy}
      >
        {description}
      </Typography>

      {additionalContent}

      {actions &&
        (() => {
          // Flatten children and filter out null/false values to count actual rendered elements
          const flattenedActions = React.Children.toArray(actions).flat().filter(Boolean);
          const actualActionCount = flattenedActions.length;
          const isSingleAction = actualActionCount === 1;

          return (
            <div className={`flex ${isSingleAction ? "justify-center" : ""} gap-base w-full max-w-md mt-base`}>
              {actions}
            </div>
          );
        })()}

      {footer && <div className="mt-6">{footer}</div>}
    </div>
  );

  // For import state, we need special wrapper structure
  if (testId === "empty-state-label") {
    return (
      <div
        data-testid={testId}
        aria-labelledby={ariaLabelledBy}
        aria-describedby={ariaDescribedBy}
        className="w-full flex items-center justify-center m-0"
      >
        <div className="w-full h-full">{content}</div>
      </div>
    );
  }

  // For all other states
  return content;
};

// Storage provider icons component
const StorageProviderIcons = () => (
  <div className="flex items-center justify-center gap-base mb-wide" data-testid="dm-storage-provider-icons">
    <Tooltip title="Amazon S3">
      <div className="flex items-center justify-center p-2" aria-label="Amazon S3">
        <IconCloudProviderS3 width={32} height={32} className="text-neutral-content-subtler" />
      </div>
    </Tooltip>
    <Tooltip title="Google Cloud Storage">
      <div className="flex items-center justify-center p-2" aria-label="Google Cloud Storage">
        <IconCloudProviderGCS width={32} height={32} className="text-neutral-content-subtler" />
      </div>
    </Tooltip>
    <Tooltip title="Azure Blob Storage">
      <div className="flex items-center justify-center p-2" aria-label="Azure Blob Storage">
        <IconCloudProviderAzure width={32} height={32} className="text-neutral-content-subtler" />
      </div>
    </Tooltip>
    <Tooltip title="Redis Storage">
      <div className="flex items-center justify-center p-2" aria-label="Redis Storage">
        <IconCloudProviderRedis width={32} height={32} className="text-neutral-content-subtler" />
      </div>
    </Tooltip>
  </div>
);


export const EmptyState: FC<EmptyStateProps> = ({
  canImport,
  onOpenSourceStorageModal,
  onOpenImportModal,
  // Role-based props (optional)
  userRole,
  project,
  hasData: _hasData,
  hasFilters,
  canLabel: _canLabel,
  canAnnotate = true,
  onLabelAllTasks,
  onClearFilters,
}) => {
  const isImportEnabled = Boolean(canImport);
  const { permissions } = useAuth();

  // PRIORITY CHECK: Role-based empty state for annotators/experts
  // Check this FIRST to prevent any flash of import screen
  // Fallback to APP_SETTINGS.user flags if userRole is not yet loaded
  const isAnnotator = userRole === "ANNOTATOR" || window.APP_SETTINGS?.user?.is_annotator === true;
  const isReviewer = userRole === "REVIEWER" || window.APP_SETTINGS?.user?.is_expert === true;
  
  if (isReviewer || isAnnotator) {
    // Reviewer empty state
    if (isReviewer) {
      return renderEmptyStateLayout({
        icon: <IconCheck />,
        title: "No tasks available for review or labeling",
        description: "Tasks imported to this project will appear here",
      });
    }

    // Annotator empty state
    if (isAnnotator) {
      const isAutoDistribution = project?.assignment_settings?.label_stream_task_distribution === "auto_distribution";
      const isManualDistribution = project?.assignment_settings?.label_stream_task_distribution === "assigned_only";

      if (isAutoDistribution) {
        return renderEmptyStateLayout({
          icon: <IconLsLabeling />,
          title: "Start labeling tasks",
          description: "Tasks you've labeled will appear here",
          actions: canAnnotate && onLabelAllTasks ? (
            <Button
              variant="primary"
              look="filled"
              disabled={false}
              onClick={onLabelAllTasks}
              data-testid="dm-label-all-tasks-button"
            >
              Label All Tasks
            </Button>
          ) : null,
        });
      }

      if (isManualDistribution) {
        return renderEmptyStateLayout({
          icon: <IconInbox />,
          title: "No tasks available",
          description: "Tasks assigned to you will appear here",
        });
      }

      // Fallback for annotators with unknown distribution setting
      return renderEmptyStateLayout({
        icon: <IconInbox width={40} height={40} />,
        title: "No tasks available",
        description: "Tasks will appear here when they become available",
      });
    }
  }

  // If user cannot annotate (organization member), show view-only message
  if (!canAnnotate && _hasData) {
    return renderEmptyStateLayout({
      icon: <IconCheck />,
      iconBackground: "bg-warning-background",
      iconColor: "text-warning-icon",
      title: "View Only Mode",
      description: "You can view annotation results but cannot create or edit annotations. Our annotation team handles the labeling work.",
      actions: null,
    });
  }

  // If filters are applied, show the filter-specific empty state (regardless of user role)
  if (hasFilters) {
    return renderEmptyStateLayout({
      icon: <IconSearch />,
      iconBackground: "bg-warning-background",
      iconColor: "text-warning-icon",
      title: "No tasks found",
      description: "Try adjusting or clearing the filters to see more results",
      actions: (
        <Button variant="primary" look="outlined" onClick={onClearFilters} data-testid="dm-clear-filters-button">
          Clear Filters
        </Button>
      ),
    });
  }

  // Default case: show import functionality (existing behavior for Owners/Admins/Managers)
  return renderEmptyStateLayout({
    icon: <IconUpload />,
    title: "Import data to get your project started",
    description: "Connect your cloud storage or upload files from your computer",
    testId: "empty-state-label",
    ariaLabelledBy: "dm-empty-title",
    ariaDescribedBy: "dm-empty-desc",
    additionalContent: <StorageProviderIcons />,
    actions: (
      <>
        {permissions.can(ABILITY.can_manage_storage) && (
          <button
            style={primaryButtonStyle}
            onClick={onOpenSourceStorageModal}
            data-testid="dm-connect-source-storage-button"
          >
            Connect Cloud Storage
          </button>
        )}

        {isImportEnabled && (
          <button
            style={outlineButtonStyle}
            onClick={onOpenImportModal}
            data-testid="dm-import-button"
          >
            Import
          </button>
        )}
      </>
    ),
  });
};

