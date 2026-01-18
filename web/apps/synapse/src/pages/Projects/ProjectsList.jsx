import chr from "chroma-js";
import { format } from "date-fns";
import { useMemo, useState, useEffect } from "react";
import { NavLink } from "react-router-dom";
import {
  IconCheck,
  IconEllipsis,
  IconMinus,
  IconSparks,
  IconFolder,
  IconPlus,
} from "@synapse/icons";
import { Userpic, Button, Dropdown, Tooltip } from "@synapse/ui";
import { Menu, Pagination } from "../../components";
import { useAuth } from "@synapse/core/providers/AuthProvider";
import { cn } from "../../utils/bem";
import { absoluteURL } from "../../utils/helpers";
import { ProjectStateChip } from "@synapse/app-common";

const DEFAULT_CARD_COLORS = ["#FFFFFF", "#FDFDFC"];

// Circular progress ring component
const CircularProgress = ({ percentage, size = 80, strokeWidth = 6 }) => {
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (percentage / 100) * circumference;

  return (
    <div style={{ position: 'relative', width: size, height: size }}>
      <svg width={size} height={size} style={{ transform: 'rotate(-90deg)' }}>
        {/* Background circle */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="rgba(139, 92, 246, 0.1)"
          strokeWidth={strokeWidth}
        />
        {/* Progress circle */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="url(#gradient)"
          strokeWidth={strokeWidth}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          style={{ transition: 'stroke-dashoffset 0.5s ease' }}
        />
        <defs>
          <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#8b5cf6" />
            <stop offset="100%" stopColor="#a78bfa" />
          </linearGradient>
        </defs>
      </svg>
      <div style={{
        position: 'absolute',
        top: '50%',
        left: '50%',
        transform: 'translate(-50%, -50%)',
        fontFamily: "'Space Grotesk', system-ui, sans-serif",
        fontSize: '18px',
        fontWeight: 700,
        color: '#a78bfa',
        textAlign: 'center',
        lineHeight: 1,
      }}>
        {Math.round(percentage)}%
      </div>
    </div>
  );
};

// Stat badge component
const StatBadge = ({ icon: Icon, value, label, color, gradient }) => {
  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      gap: '8px',
      padding: '8px 12px',
      background: gradient || `linear-gradient(135deg, ${color}15, ${color}08)`,
      border: `1px solid ${color}30`,
      borderRadius: '8px',
      transition: 'all 0.15s cubic-bezier(0.4, 0, 0.2, 1)',
      cursor: 'default',
    }}>
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        width: '24px',
        height: '24px',
        borderRadius: '6px',
        background: `${color}20`,
        color: color,
      }}>
        <Icon style={{ width: '14px', height: '14px' }} />
      </div>
      <div style={{
        display: 'flex',
        flexDirection: 'column',
        gap: '2px',
      }}>
        <span style={{
          fontFamily: "'Space Grotesk', system-ui, sans-serif",
          fontSize: '16px',
          fontWeight: 700,
          color: color,
          lineHeight: 1,
        }}>
          {value}
        </span>
        <span style={{
          fontFamily: "'Space Grotesk', system-ui, sans-serif",
          fontSize: '10px',
          fontWeight: 500,
          color: 'var(--color-neutral-content-subtle)',
          textTransform: 'uppercase',
          letterSpacing: '0.05em',
          lineHeight: 1,
        }}>
          {label}
        </span>
      </div>
    </div>
  );
};

const CreateProjectCard = ({ onClick }) => {
  return (
    <div
      onClick={onClick}
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        height: "100%",
        minHeight: "220px",
        background: "rgba(255, 255, 255, 0.02)",
        border: "1px dashed rgba(167, 139, 250, 0.3)",
        borderRadius: "12px",
        cursor: "pointer",
        transition: "all 0.2s ease",
        gap: "16px",
      }}
      className="create-project-card"
      onMouseEnter={(e) => {
        e.currentTarget.style.background = "rgba(167, 139, 250, 0.05)";
        e.currentTarget.style.borderColor = "rgba(167, 139, 250, 0.6)";
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.background = "rgba(255, 255, 255, 0.02)";
        e.currentTarget.style.borderColor = "rgba(167, 139, 250, 0.3)";
      }}
    >
      <div
        style={{
          width: "48px",
          height: "48px",
          borderRadius: "50%",
          background: "rgba(167, 139, 250, 0.1)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          color: "#a78bfa",
        }}
      >
        <IconPlus style={{ width: "24px", height: "24px" }} />
      </div>
      <span
        style={{
          fontFamily: "'Space Grotesk', system-ui, sans-serif",
          fontSize: "16px",
          fontWeight: 600,
          color: "#a78bfa",
        }}
      >
        Create New Project
      </span>
    </div>
  );
};

export const ProjectsList = ({
  projects,
  currentPage,
  totalItems,
  loadNextPage,
  pageSize,
  openModal,
}) => {
  const { user } = useAuth();
  const isAnnotator = !!user?.is_annotator;
  const isExpert = !!user?.is_expert;
  // Both annotators and experts see simplified view
  const role = isAnnotator || isExpert ? "worker" : "client";
  
  return (
    <>
      <div className={cn("projects-page").elem("list").toClassName()}>
        {openModal && <CreateProjectCard onClick={openModal} />}
        {projects.map((project) => (
          <ProjectCard key={project.id} project={project} role={role} />
        ))}
      </div>
      <div className={cn("projects-page").elem("pages").toClassName()}>
        <Pagination
          name="projects-list"
          label="Projects"
          page={currentPage}
          totalItems={totalItems}
          urlParamName="page"
          pageSize={pageSize}
          pageSizeOptions={[10, 30, 50, 100]}
          onPageLoad={(page, pageSize) => loadNextPage(page, pageSize)}
        />
      </div>
    </>
  );
};

export const EmptyProjectsList = ({ openModal, isAnnotator }) => {
  return (
    <div className={cn("empty-projects-page").toClassName()}>
      <div className={cn("empty-projects-page").elem("icon").toClassName()}>
        <IconFolder />
      </div>
      <div className={cn("empty-projects-page").elem("step-indicator").toClassName()}>
        01/
      </div>
      {isAnnotator ? (
        <>
          <h1
            className={cn("empty-projects-page").elem("header").toClassName()}
          >
            No projects assigned
          </h1>
          <p>
            You don't have any projects assigned yet. Contact your project
            manager to get started.
          </p>
        </>
      ) : (
        <>
          <h1
            className={cn("empty-projects-page").elem("header").toClassName()}
          >
            Create your first project
          </h1>
          <p>Import your data and configure the labeling interface to start annotating.</p>
          {openModal && (
            <button
              onClick={openModal}
              className="create-btn"
              aria-label="Create new project"
            >
              Create Project
            </button>
          )}
        </>
      )}
    </div>
  );
};

const ProjectCard = ({ project, role }) => {
  const color = useMemo(() => {
    return DEFAULT_CARD_COLORS.includes(project.color) ? null : project.color;
  }, [project]);

  const projectColors = useMemo(() => {
    const textColor =
      color && chr(color).luminance() > 0.3
        ? "var(--color-neutral-inverted-content)"
        : "var(--color-neutral-inverted-content)"; // Determine text color based on luminance
    return color
      ? {
          "--header-color": color,
          "--background-color": chr(color).alpha(0.2).css(),
          "--text-color": textColor,
          "--border-color": chr(color).alpha(0.5).css(),
        }
      : {};
  }, [color]);

  return (
    <NavLink
      className={cn("projects-page").elem("link").toClassName()}
      to={`/projects/${project.id}/data`}
      data-external
    >
      <div
        className={cn("project-card").mod({ colored: !!color }).toClassName()}
        style={projectColors}
      >
        <div className={cn("project-card").elem("header").toClassName()}>
          <div className={cn("project-card").elem("title").toClassName()}>
            <div
              className={cn("project-card")
                .elem("title-text-wrapper")
                .toClassName()}
            >
              <Tooltip title={project.title ?? "New project"}>
                <div
                  className={cn("project-card")
                    .elem("title-text")
                    .toClassName()}
                >
                  {project.title ?? "New project"}
                </div>
              </Tooltip>
            </div>

            {role !== "worker" && (
              <div
                className={cn("project-card").elem("menu").toClassName()}
                onClick={(e) => {
                  e.stopPropagation();
                  e.preventDefault();
                }}
              >
                <Dropdown.Trigger
                  content={
                    <Menu contextual>
                      <Menu.Item href={`/projects/${project.id}/settings`}>
                        Settings
                      </Menu.Item>
                      <Menu.Item
                        href={`/projects/${project.id}/data?labeling=1`}
                      >
                        Label
                      </Menu.Item>
                    </Menu>
                  }
                >
                  <Button
                    size="smaller"
                    look="string"
                    aria-label="Project options"
                  >
                    <IconEllipsis />
                  </Button>
                </Dropdown.Trigger>
              </div>
            )}

            {role === "worker" && project.state && (
              <ProjectStateChip
                state={project.state}
                projectId={project.id}
                interactive={false}
              />
            )}
          </div>
          <div className={cn("project-card").elem("summary").toClassName()}>
            <div
              className={cn("project-card").elem("annotation").toClassName()}
              style={{
                display: 'flex',
                gap: '20px',
                alignItems: 'center',
                padding: '16px 0',
              }}
            >
              {/* Circular Progress for Task Completion */}
              <div style={{ flexShrink: 0 }}>
                <CircularProgress
                  percentage={(() => {
                    // For annotators/experts: use their assigned/completed counts
                    if (role === "worker") {
                      const assigned = project._annotator_assigned_tasks ?? 0;
                      const completed = project._annotator_completed_tasks ?? 0;
                      return assigned > 0 ? (completed / assigned) * 100 : 0;
                    }
                    // For clients: use overall project stats
                    return project.task_number > 0 ? (project.finished_task_number / project.task_number) * 100 : 0;
                  })()}
                  size={80}
                  strokeWidth={6}
                />
                <div style={{
                  marginTop: '8px',
                  textAlign: 'center',
                  fontFamily: "'Space Grotesk', system-ui, sans-serif",
                  fontSize: '11px',
                  fontWeight: 500,
                  color: 'var(--color-neutral-content-subtle)',
                }}>
                  {role === "worker" 
                    ? `${project._annotator_completed_tasks ?? 0} / ${project._annotator_assigned_tasks ?? 0}`
                    : `${project.finished_task_number ?? 0} / ${project.task_number ?? 0}`
                  }
                  <div style={{ fontSize: '9px', textTransform: 'uppercase', letterSpacing: '0.05em', marginTop: '2px' }}>
                    Tasks Done
                  </div>
                </div>
              </div>

              {/* Stats Grid - Simplified for workers (annotators/experts) */}
              <div style={{
                flex: 1,
                display: 'grid',
                gridTemplateColumns: role === "worker" ? '1fr' : 'repeat(auto-fit, minmax(140px, 1fr))',
                gap: '8px',
              }}>
                {role === "worker" ? (
                  <StatBadge
                    icon={IconCheck}
                    value={project._annotator_completed_tasks ?? 0}
                    label="Completed"
                    color="#10b981"
                  />
                ) : (
                  <>
                    <StatBadge
                      icon={IconCheck}
                      value={project.total_annotations_number ?? 0}
                      label="Annotated"
                      color="#10b981"
                    />
                    <StatBadge
                      icon={IconMinus}
                      value={project.skipped_annotations_number ?? 0}
                      label="Skipped"
                      color="#f59e0b"
                    />
                    <StatBadge
                      icon={IconSparks}
                      value={project.total_predictions_number ?? 0}
                      label="Predictions"
                      color="#a78bfa"
                    />
                  </>
                )}
              </div>
            </div>
          </div>
        </div>
        <div className={cn("project-card").elem("description").toClassName()}>
          {project.description || <span style={{ color: 'var(--color-neutral-subtle)', fontStyle: 'italic' }}>No description</span>}
        </div>
        <div className={cn("project-card").elem("info").toClassName()}>
          <div
            className={cn("project-card").elem("created-date").toClassName()}
          >
            {format(new Date(project.created_at), "dd MMM yy, HH:mm")}
          </div>
          {role !== "worker" && project.created_by && (
            <div
              className={cn("project-card").elem("created-by").toClassName()}
            >
              <Userpic 
                src={project.created_by.avatar} 
                user={project.created_by} 
                showUsernameTooltip 
              />
              {(project.created_by.first_name || project.created_by.last_name || project.created_by.email) && (
                <span className={cn("project-card").elem("creator-name").toClassName()}>
                  {project.created_by.first_name && project.created_by.last_name
                    ? `${project.created_by.first_name} ${project.created_by.last_name}`
                    : project.created_by.first_name || project.created_by.last_name || project.created_by.email}
                </span>
              )}
            </div>
          )}
        </div>
      </div>
    </NavLink>
  );
};

