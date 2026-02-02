import React, { useState } from "react";
import { useParams as useRouterParams } from "react-router";
import { Redirect } from "react-router-dom";
import { Button } from "@synapse/ui";
import { Oneof } from "../../components/Oneof/Oneof";
import { Spinner } from "../../components/Spinner/Spinner";
import { ApiContext } from "../../providers/ApiProvider";
import { useContextProps } from "../../providers/RoutesProvider";
import { useAuth } from "@synapse/core/providers/AuthProvider";
import { cn } from "../../utils/bem";
import { CreateProject } from "../CreateProject/CreateProject";
import { DataManagerPage } from "../DataManager/DataManager";
import { SettingsPage } from "../Settings";
import { EmptyProjectsList, ProjectsList } from "./ProjectsList";
import { useAbortController, useUpdatePageTitle } from "@synapse/core";
import "./Projects.scss";

const getCurrentPage = () => {
  const pageNumberFromURL = new URLSearchParams(location.search).get("page");

  return pageNumberFromURL ? Number.parseInt(pageNumberFromURL) : 1;
};

export const ProjectsPage = () => {
  const api = React.useContext(ApiContext);
  const abortController = useAbortController();
  const { user } = useAuth();
  const [projectsList, setProjectsList] = React.useState([]);
  const [networkState, setNetworkState] = React.useState(null);
  const [currentPage, setCurrentPage] = useState(getCurrentPage());
  const [totalItems, setTotalItems] = useState(1);
  const setContextProps = useContextProps();

  useUpdatePageTitle("Projects");
  const defaultPageSize = Number.parseInt(
    localStorage.getItem("pages:projects-list") ?? 30
  );

  // Check user role - annotators and experts cannot create projects
  const isAnnotator = !!user?.is_annotator;
  const isClient = !!user?.is_client;
  const isExpert = !!user?.is_expert;

  const [modal, setModal] = React.useState(false);

  const openModal = () => {
    // Only clients can create projects (not annotators or experts)
    if (isClient && !isAnnotator && !isExpert) {
      setModal(true);
    }
  };

  const closeModal = () => setModal(false);

  const fetchProjects = async (
    page = currentPage,
    pageSize = defaultPageSize
  ) => {
    setNetworkState("loading");
    abortController.renew(); // Cancel any in flight requests

    const requestParams = { page, page_size: pageSize };

    const includeFields = [
      "id",
      "title",
      "created_by",
      "created_at",
      "color",
      "is_published",
      "assignment_settings",
      "state",
    ];

    // Add annotator/expert-specific fields if user is an annotator or expert
    if (isAnnotator || isExpert) {
      includeFields.push(
        "_annotator_assigned_tasks",
        "_annotator_completed_tasks"
      );
    }

    // Use 'fields' parameter for FlexFieldsModelSerializer (what fields to include in response)
    requestParams.fields = includeFields.join(",");
    
    // Also use 'include' for the database-level counts
    requestParams.include = includeFields.join(",");

    const data = await api.callApi("projects", {
      params: requestParams,
      signal: abortController.controller.current.signal,
      errorFilter: (e) => e.error.includes("aborted"),
    });

    if (data && Array.isArray(data.results)) {
      setTotalItems(data.count ?? 1);
      setProjectsList(data.results);
    } else {
      setTotalItems(0);
      setProjectsList([]);
    }

    if (data?.results?.length) {
      const additionalFields = [
        "id",
        "description",
        "num_tasks_with_annotations",
        "task_number",
        "skipped_annotations_number",
        "total_annotations_number",
        "total_predictions_number",
        "ground_truth_number",
        "finished_task_number",
      ];

      // Add annotator/expert-specific fields to additional data fetch as well
      if (isAnnotator || isExpert) {
        additionalFields.push(
          "_annotator_assigned_tasks",
          "_annotator_completed_tasks"
        );
      }

      const additionalData = await api.callApi("projects", {
        params: {
          ids: data?.results?.map(({ id }) => id).join(","),
          fields: additionalFields.join(","),  // For FlexFieldsModelSerializer
          include: additionalFields.join(","),  // For database annotations
          page_size: pageSize,
        },
        signal: abortController.controller.current.signal,
        errorFilter: (e) => e.error.includes("aborted"),
      });

      if (additionalData?.results?.length) {
        setProjectsList((prev) =>
          additionalData.results.map((project) => {
            const prevProject = prev.find(({ id }) => id === project.id);

            return {
              ...prevProject,
              ...project,
            };
          })
        );
      }
    }

    setNetworkState("loaded");
  };

  const loadNextPage = async (page, pageSize) => {
    setCurrentPage(page);
    await fetchProjects(page, pageSize);
  };

  React.useEffect(() => {
    fetchProjects();
  }, []);

  React.useEffect(() => {
    // We handle the create project UI within the ProjectsList now
    // Passing openModal to context props just in case other components need it, but disabling showButton
    const showButton = false;
    setContextProps({ openModal, showButton, isAnnotator, isExpert });
  }, [projectsList.length, isClient, isAnnotator, isExpert]);

  return (
    <div className={cn("projects-page").toClassName()}>
      <Oneof value={networkState}>
        <div
          className={cn("projects-page").elem("loading").toClassName()}
          case="loading"
        >
          <Spinner size={64} />
        </div>
        <div
          className={cn("projects-page").elem("content").toClassName()}
          case="loaded"
        >
          {projectsList.length ? (
            <ProjectsList
              projects={projectsList}
              currentPage={currentPage}
              totalItems={totalItems}
              loadNextPage={loadNextPage}
              pageSize={defaultPageSize}
              openModal={isClient ? openModal : null}
            />
          ) : (
            <EmptyProjectsList
              openModal={isClient ? openModal : null}
              isAnnotator={isAnnotator}
              isExpert={isExpert}
            />
          )}
          {modal && isClient && <CreateProject onClose={closeModal} />}
        </div>
      </Oneof>
    </div>
  );
};

ProjectsPage.title = "Projects";
ProjectsPage.path = "/projects";
ProjectsPage.exact = true;
ProjectsPage.routes = ({ store }) => [
  {
    title: () => store.project?.title,
    path: "/:id(\\d+)",
    exact: true,
    component: () => {
      const params = useRouterParams();

      return <Redirect to={`/projects/${params.id}/data`} />;
    },
    pages: {
      DataManagerPage,
      SettingsPage,
    },
  },
];
ProjectsPage.context = () => null;

