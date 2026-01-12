import React, { useState, useEffect, useCallback } from "react";
import { useHistory, useParams } from "react-router-dom";
import { Button, useToast, ToastType } from "@synapse/ui";
import { Footer } from "../../components/Footer/Footer";
import { Spinner } from "../../components";
import "./ExpertProjectReview.scss";

interface ReviewTask {
  id: number;
  task_id: number;
  status: string;
  assignment_reason: string;
  disagreement_score: number;
  assigned_at: string;
  is_overdue: boolean;
}

interface ProjectReviewData {
  project_id: number;
  project_title: string;
  total_pending: number;
  tasks: ReviewTask[];
}

export const ExpertProjectReview: React.FC = () => {
  const history = useHistory();
  const toast = useToast();
  const { projectId } = useParams<{ projectId: string }>();

  const [data, setData] = useState<ProjectReviewData | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchProjectTasks = useCallback(async () => {
    try {
      const response = await fetch(
        `/api/annotators/expert/pending-reviews?project_id=${projectId}`,
        { credentials: "include" }
      );

      if (response.ok) {
        const result = await response.json();
        setData({
          project_id: parseInt(projectId),
          project_title: result.project_title || `Project ${projectId}`,
          total_pending: result.count || 0,
          tasks: result.tasks || [],
        });
      } else if (response.status === 403) {
        toast?.show({
          message: "Access denied. Expert privileges required.",
          type: ToastType.error,
        });
        history.push("/expert/dashboard");
      } else if (response.status === 401) {
        history.push("/annotators/login");
      }
    } catch (error) {
      console.error("Failed to fetch project tasks:", error);
      toast?.show({
        message: "Failed to load project tasks",
        type: ToastType.error,
      });
    } finally {
      setLoading(false);
    }
  }, [projectId, history, toast]);

  useEffect(() => {
    fetchProjectTasks();
  }, [fetchProjectTasks]);

  const startReview = (taskId: number) => {
    history.push(`/expert/task/${taskId}`);
  };

  const getPriorityClass = (score: number): string => {
    if (score >= 50) return "critical";
    if (score >= 30) return "high";
    if (score >= 15) return "moderate";
    return "low";
  };

  const getPriorityLabel = (score: number): string => {
    if (score >= 50) return "Critical";
    if (score >= 30) return "High";
    if (score >= 15) return "Moderate";
    return "Low";
  };

  if (loading) {
    return (
      <div className="expert-project-review">
        <div className="expert-project-review__loading">
          <Spinner size={48} className="" style={{}} />
          <p>Loading review tasks...</p>
        </div>
        <Footer />
      </div>
    );
  }

  if (!data) {
    return (
      <div className="expert-project-review">
        <div className="expert-project-review__error">
          <h2>Unable to Load Project</h2>
          <Button onClick={() => history.push("/expert/projects")}>
            Back to Projects
          </Button>
        </div>
        <Footer />
      </div>
    );
  }

  return (
    <div className="expert-project-review">

      <div className="expert-project-review__content">
        {/* Header */}
        <div className="expert-project-review__header">
          <Button
            variant="neutral"
            onClick={() => history.push("/expert/projects")}
          >
            ← Back to Projects
          </Button>
          <div className="header-info">
            <h1>{data.project_title}</h1>
            <span className="task-count">
              {data.total_pending} tasks pending
            </span>
          </div>
        </div>

        {/* Task List */}
        {data.tasks.length === 0 ? (
          <div className="expert-project-review__empty">
            <div className="empty-icon">✅</div>
            <h3>All Caught Up!</h3>
            <p>No pending review tasks for this project.</p>
            <Button onClick={() => history.push("/expert/projects")}>
              View Other Projects
            </Button>
          </div>
        ) : (
          <div className="expert-project-review__task-list">
            {data.tasks.map((task) => (
              <div
                key={task.id}
                className={`task-card ${task.is_overdue ? "overdue" : ""}`}
              >
                <div className="task-main">
                  <div className="task-id">Task #{task.task_id}</div>
                  <div className="task-meta">
                    <span
                      className={`priority ${getPriorityClass(
                        task.disagreement_score
                      )}`}
                    >
                      {getPriorityLabel(task.disagreement_score)} Priority
                    </span>
                    <span className="disagreement">
                      {task.disagreement_score.toFixed(0)}% disagreement
                    </span>
                    {task.is_overdue && (
                      <span className="overdue-tag">Overdue</span>
                    )}
                  </div>
                  <div className="task-reason">{task.assignment_reason}</div>
                  <div className="task-date">
                    Assigned: {new Date(task.assigned_at).toLocaleDateString()}
                  </div>
                </div>

                <div className="task-actions">
                  <Button
                    onClick={() => startReview(task.task_id)}
                    style={{ backgroundColor: "#3b82f6" }}
                  >
                    Review
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <Footer />
    </div>
  );
};

export default ExpertProjectReview;

