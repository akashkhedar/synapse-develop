import React from "react";
import { useHistory } from "react-router-dom";
import { Button } from "@synapse/ui";
import "./ExpertProjectCard.scss";

interface ExpertProject {
  id: number;
  title: string;
  pending: number;
  in_progress: number;
  completed: number;
  earned: number;
  pending_earnings: number;
}

interface ExpertProjectCardProps {
  project: ExpertProject;
}

export const ExpertProjectCard: React.FC<ExpertProjectCardProps> = ({
  project,
}) => {
  const history = useHistory();

  const handleReviewClick = () => {
    // Navigate to project review page to see all pending tasks
    history.push(`/expert/review/${project.id}`);
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const hasPendingReviews = project.pending > 0 || project.in_progress > 0;

  return (
    <div className="expert-project-card">
      <div className="expert-project-card__header">
        <h3 className="project-title">{project.title}</h3>
        {hasPendingReviews && (
          <span className="pending-badge">
            {project.pending + project.in_progress} pending
          </span>
        )}
      </div>

      <div className="expert-project-card__stats">
        <div className="stat">
          <span className="stat-value">{project.pending}</span>
          <span className="stat-label">Pending</span>
        </div>
        <div className="stat">
          <span className="stat-value">{project.in_progress}</span>
          <span className="stat-label">In Progress</span>
        </div>
        <div className="stat">
          <span className="stat-value">{project.completed}</span>
          <span className="stat-label">Completed</span>
        </div>
      </div>

      <div className="expert-project-card__earnings">
        <div className="earnings-row">
          <span className="earnings-label">Earned</span>
          <span className="earnings-value earned">
            {formatCurrency(project.earned)}
          </span>
        </div>
        {project.pending_earnings > 0 && (
          <div className="earnings-row">
            <span className="earnings-label">Pending</span>
            <span className="earnings-value pending">
              +{formatCurrency(project.pending_earnings)}
            </span>
          </div>
        )}
      </div>

      <div className="expert-project-card__actions">
        <Button
          onClick={handleReviewClick}
          disabled={!hasPendingReviews}
          style={{
            backgroundColor: hasPendingReviews ? "#3b82f6" : "#9ca3af",
            width: "100%",
          }}
        >
          {hasPendingReviews ? "Review Tasks" : "No Pending Reviews"}
        </Button>
      </div>
    </div>
  );
};

export default ExpertProjectCard;

