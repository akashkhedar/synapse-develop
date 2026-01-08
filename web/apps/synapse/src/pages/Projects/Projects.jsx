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
      const additionalData = await api.callApi("projects", {
        params: {
          ids: data?.results?.map(({ id }) => id).join(","),
          include: [
            "id",
            "description",
            "num_tasks_with_annotations",
            "task_number",
            "skipped_annotations_number",
            "total_annotations_number",
            "total_predictions_number",
            "ground_truth_number",
            "finished_task_number",
          ].join(","),
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
    // Only show create button for clients (not annotators or experts)
    // Also hide if projects list is empty (we show a nice empty state with button)
    const showButton =
      isClient && !isAnnotator && !isExpert && projectsList.length > 0;
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
            />
          ) : (
            <EmptyProjectsList
              openModal={isClient ? openModal : null}
              isAnnotator={isAnnotator}
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
ProjectsPage.context = ({ openModal, showButton, isAnnotator }) => {
  // Don't show create button for annotators
  if (!showButton || isAnnotator) return null;
  return (
    <Button onClick={openModal} size="small" aria-label="Create new project">
      Create
    </Button>
  );
};

