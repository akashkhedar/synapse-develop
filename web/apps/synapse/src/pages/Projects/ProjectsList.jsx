import chr from "chroma-js";
import { format } from "date-fns";
import { useMemo, useState, useEffect } from "react";
import { NavLink } from "react-router-dom";
import {
  IconCheck,
  IconEllipsis,
  IconMinus,
  IconSparks,
} from "@synapse/icons";
import { Userpic, Button, Dropdown, Tooltip } from "@synapse/ui";
import { Menu, Pagination } from "../../components";
import { useAuth } from "@synapse/core/providers/AuthProvider";
import { cn } from "../../utils/bem";
import { absoluteURL } from "../../utils/helpers";
import { ProjectStateChip } from "@synapse/app-common";

const DEFAULT_CARD_COLORS = ["#FFFFFF", "#FDFDFC"];

export const ProjectsList = ({
  projects,
  currentPage,
  totalItems,
  loadNextPage,
  pageSize,
}) => {
  const { user } = useAuth();
  const isAnnotator = !!user?.is_annotator;
  const role = isAnnotator ? "annotator" : "client";
  console.log("PROJECTS---PROJECTS---PROJECTS",role)
  console.log(projects)
  return (
    <>
      <div className={cn("projects-page").elem("list").toClassName()}>
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
      <img
        alt="Heidi looking for projects"
        className={cn("empty-projects-page").elem("heidi").toClassName()}
        src={absoluteURL("/static/images/opossum_looking.png")}
      />
      {isAnnotator ? (
        <>
          <h1
            className={cn("empty-projects-page").elem("header").toClassName()}
          >
            Heidi doesn't see any projects assigned!
          </h1>
          <p>
            You don't have any projects assigned yet. Contact your project
            manager.
          </p>
        </>
      ) : (
        <>
          <h1
            className={cn("empty-projects-page").elem("header").toClassName()}
          >
            Heidi doesn't see any projects here!
          </h1>
          <p>Create one and start labeling your data.</p>
          {openModal && (
            <Button
              onClick={openModal}
              className="my-8"
              aria-label="Create new project"
            >
              Create Project
            </Button>
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

            {role !== "annotator" && (
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

            {role !== "client" && project.state && (
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
            >
              <div className={cn("project-card").elem("total").toClassName()}>
                {role === "annotator" ? (
                  <>
                    <span style={{ fontWeight: 600 }}>{project.finished_task_number ?? 0}</span>
                    <span style={{ color: 'var(--color-neutral-content-subtler)', fontSize: '0.875rem', marginLeft: '4px' }}>
                      / {project.task_number ?? 0} tasks completed
                    </span>
                  </>
                ) : (
                  `${project.finished_task_number ?? 0} / ${project.task_number ?? 0}`
                )}
              </div>
              {(project.total_annotations_number != null || project.skipped_annotations_number != null || project.total_predictions_number != null) && (
                <div
                  className={cn("project-card").elem("detail").toClassName()}
                >
                  {role === "annotator" ? (
                    <>
                      <div
                        className={cn("project-card")
                          .elem("detail-item")
                          .mod({ type: "completed" })
                          .toClassName()}
                      >
                        <IconCheck
                          className={cn("project-card").elem("icon").toClassName()}
                        />
                        {project.total_annotations_number ?? 0}
                        <span style={{ marginLeft: '4px', fontSize: '0.75rem', color: 'var(--color-neutral-content-subtler)' }}>
                          annotations
                        </span>
                      </div>
                    </>
                  ) : (
                    <>
                      <div
                        className={cn("project-card")
                          .elem("detail-item")
                          .mod({ type: "completed" })
                          .toClassName()}
                      >
                        <IconCheck
                          className={cn("project-card").elem("icon").toClassName()}
                        />
                        {project.total_annotations_number ?? 0}
                      </div>
                      <div
                        className={cn("project-card")
                          .elem("detail-item")
                          .mod({ type: "rejected" })
                          .toClassName()}
                      >
                        <IconMinus
                          className={cn("project-card").elem("icon").toClassName()}
                        />
                        {project.skipped_annotations_number ?? 0}
                      </div>
                      <div
                        className={cn("project-card")
                          .elem("detail-item")
                          .mod({ type: "predictions" })
                          .toClassName()}
                      >
                        <IconSparks
                          className={cn("project-card").elem("icon").toClassName()}
                        />
                        {project.total_predictions_number ?? 0}
                      </div>
                    </>
                  )}
                </div>
              )}
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
          {role !== "annotator" && project.created_by && (
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

