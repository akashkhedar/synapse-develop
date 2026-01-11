import {
  IconExternal,
  IconFolderAdd,
  IconSynapse,
  IconUserAdd,
  IconFolderOpen,
} from "@synapse/icons";
import {
  Button,
  SimpleCard,
  Spinner,
  Tooltip,
  Typography,
} from "@synapse/ui";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { Link } from "react-router-dom";
import { useUpdatePageTitle } from "@synapse/core";
import { motion } from "framer-motion";
import { HeidiTips } from "../../components/HeidiTips/HeidiTips";
import { useAPI } from "../../providers/ApiProvider";
import { CreateProject } from "../CreateProject/CreateProject";
import { InviteLink } from "../Organization/PeoplePage/InviteLink";
import type { Page } from "../types/Page";
import styles from "./HomePage.module.css";

const PROJECTS_TO_SHOW = 10;

const resources = [
  {
    title: "Documentation",
    url: "https://synapse.io/guide/",
  },
  {
    title: "API Reference",
    url: "https://api.synapse.io/api-reference/introduction/getting-started",
  },
  {
    title: "Release Notes",
    url: "https://synapse.io/learn/categories/release-notes/",
  },
  {
    title: "Blog",
    url: "https://synapse.io/blog/",
  },
  {
    title: "Community",
    url: "https://slack.synapse.io",
  },
];

const actions = [
  {
    title: "Create Project",
    icon: IconFolderAdd,
    type: "createProject",
  },
  {
    title: "Invite Members",
    icon: IconUserAdd,
    type: "inviteMembers",
  },
] as const;

type Action = (typeof actions)[number]["type"];

// Animation variants
const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
    },
  },
};

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: {
      duration: 0.5,
      ease: [0.25, 0.1, 0.25, 1] as [number, number, number, number],
    },
  },
};

export const HomePage: Page = () => {
  const api = useAPI();
  const [creationDialogOpen, setCreationDialogOpen] = useState(false);
  const [invitationOpen, setInvitationOpen] = useState(false);

  useUpdatePageTitle("Home");
  const { data, isFetching, isSuccess, isError } = useQuery({
    queryKey: ["projects", { page_size: 10 }],
    async queryFn() {
      return api.callApi<{ results: APIProject[]; count: number }>("projects", {
        params: { page_size: PROJECTS_TO_SHOW },
      });
    },
  });

  const handleActions = (action: Action) => {
    return () => {
      switch (action) {
        case "createProject":
          setCreationDialogOpen(true);
          break;
        case "inviteMembers":
          setInvitationOpen(true);
          break;
      }
    };
  };

  return (
    <main className={styles.homePage}>
      <motion.div
        className={styles.container}
        variants={containerVariants}
        initial="hidden"
        animate="visible"
      >
        <motion.div className={styles.header} variants={itemVariants}>
          <h1 className={styles.welcomeTitle}>Dashboard</h1>
          <p className={styles.welcomeSubtitle}>
            Manage your annotation projects and team
          </p>
        </motion.div>

        <motion.div className={styles.actionsGrid} variants={itemVariants}>
          {actions.map((action) => {
            return (
              <motion.button
                key={action.title}
                className={styles.actionButton}
                onClick={handleActions(action.type)}
                whileHover={{ y: -2 }}
                whileTap={{ scale: 0.98 }}
              >
                <action.icon />
                {action.title}
              </motion.button>
            );
          })}
        </motion.div>

        <div className={styles.mainGrid}>
          <motion.section className={styles.mainSection} variants={itemVariants}>
            <div className={styles.card}>
              {data && data?.count > 0 && (
                <div className={styles.cardHeader}>
                  <h2 className={styles.cardTitle}>Recent Projects</h2>
                  <a href="/projects" className={styles.cardViewAll}>
                    View All
                  </a>
                </div>
              )}

              {isFetching ? (
                <div className={styles.loadingContainer}>
                  <Spinner />
                </div>
              ) : isError ? (
                <div className={styles.errorContainer}>
                  // ERROR: Failed to load projects
                </div>
              ) : isSuccess && data && data.results.length === 0 ? (
                <motion.div
                  className={styles.emptyState}
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ duration: 0.5 }}
                >
                  <div className={styles.emptyStateIcon}>
                    <IconFolderOpen />
                  </div>
                  <h3 className={styles.emptyStateTitle}>
                    Create your first project
                  </h3>
                  <p className={styles.emptyStateDescription}>
                    Import your data and configure the labeling interface to begin annotation
                  </p>
                  <motion.button
                    className={styles.createButton}
                    onClick={() => setCreationDialogOpen(true)}
                    aria-label="Create new project"
                    whileHover={{ y: -2, boxShadow: "0 8px 24px rgba(139, 92, 246, 0.3)" }}
                    whileTap={{ scale: 0.98 }}
                  >
                    Create Project
                  </motion.button>
                </motion.div>
              ) : isSuccess && data && data.results.length > 0 ? (
                <div className={styles.projectsList}>
                  {data.results.map((project, index) => {
                    return (
                      <ProjectCard key={project.id} project={project} index={index} />
                    );
                  })}
                </div>
              ) : null}
            </div>
          </motion.section>

          <motion.aside className={styles.sidebarSection} variants={itemVariants}>
            <HeidiTips collection="projectSettings" />
            
            <div className={styles.card}>
              <div className={styles.cardHeader}>
                <h2 className={styles.cardTitle}>Resources</h2>
              </div>
              <p className={styles.cardDescription}>
                Learn, explore and get help
              </p>
              <div className={styles.resourcesList}>
                {resources.map((link) => {
                  return (
                    <a
                      key={link.title}
                      href={link.url}
                      className={styles.resourceLink}
                      target="_blank"
                      rel="noreferrer"
                    >
                      {link.title}
                      <IconExternal />
                    </a>
                  );
                })}
              </div>
            </div>

            
          </motion.aside>
        </div>
      </motion.div>

      {creationDialogOpen && (
        <CreateProject onClose={() => setCreationDialogOpen(false)} />
      )}
      <InviteLink
        opened={invitationOpen}
        onClosed={() => setInvitationOpen(false)}
      />
    </main>
  );
};

HomePage.title = "Dashboard";
HomePage.path = "/dashboard";
HomePage.exact = true;

function ProjectCard({ project, index }: { project: APIProject; index: number }) {
  const finished = project.finished_task_number ?? 0;
  const total = project.task_number ?? 0;
  const progress = (total > 0 ? finished / total : 0) * 100;
  const white = "#FFFFFF";
  const color =
    project.color && project.color !== white ? project.color : "#8b5cf6";

  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.3, delay: index * 0.05 }}
    >
      <Link
        to={`/projects/${project.id}`}
        className={styles.projectCard}
        style={{ "--project-color": color } as React.CSSProperties}
        data-external
      >
        <div className={styles.projectCardContent}>
          <div className={styles.projectInfo}>
            <Tooltip title={project.title}>
              <span className={styles.projectTitle}>{project.title}</span>
            </Tooltip>
            <div className={styles.projectStats}>
              {finished} / {total} tasks completed
            </div>
          </div>
          <div className={styles.projectProgress}>
            <span className={styles.projectProgressLabel}>
              {total > 0 ? Math.round((finished / total) * 100) : 0}%
            </span>
            <div className={styles.projectProgressBar}>
              <div
                className={styles.projectProgressFill}
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>
        </div>
      </Link>
    </motion.div>
  );
}

