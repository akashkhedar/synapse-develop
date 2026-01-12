import React, { useState, useEffect, useCallback } from "react";
import { useHistory } from "react-router-dom";
import { Button, useToast, ToastType } from "@synapse/ui";
import { ExpertProjectCard } from "./ExpertProjectCard";
import { Footer } from "../../components/Footer/Footer";
import { Spinner } from "../../components";
import "./ExpertProjects.scss";

interface ExpertProject {
  id: number;
  title: string;
  pending: number;
  in_progress: number;
  completed: number;
  earned: number;
  pending_earnings: number;
}

interface ProjectsResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: ExpertProject[];
}

export const ExpertProjects: React.FC = () => {
  const history = useHistory();
  const toast = useToast();
  const [projects, setProjects] = useState<ExpertProject[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(false);
  const [totalCount, setTotalCount] = useState(0);

  const fetchProjects = useCallback(
    async (pageNum: number = 1) => {
      try {
        setLoading(true);
        const response = await fetch(
          `/api/annotators/expert/projects?page=${pageNum}&page_size=12`,
          { credentials: "include" }
        );

        if (response.status === 403) {
          toast?.show({
            message: "Access denied. Not an expert account.",
            type: ToastType.error,
          });
          history.push("/annotators/login");
          return;
        }

        if (response.status === 401) {
          history.push("/annotators/login");
          return;
        }

        if (response.ok) {
          const data: ProjectsResponse = await response.json();
          setProjects(data.results);
          setTotalCount(data.count);
          setHasMore(data.next !== null);
          setPage(pageNum);
        }
      } catch (error) {
        console.error("Failed to fetch projects:", error);
        toast?.show({
          message: "Failed to load projects",
          type: ToastType.error,
        });
      } finally {
        setLoading(false);
      }
    },
    [history, toast]
  );

  useEffect(() => {
    fetchProjects();
  }, [fetchProjects]);

  const handleNextPage = () => {
    if (hasMore) {
      fetchProjects(page + 1);
    }
  };

  const handlePrevPage = () => {
    if (page > 1) {
      fetchProjects(page - 1);
    }
  };

  // Calculate summary stats
  const summaryStats = {
    totalPending: projects.reduce(
      (sum, p) => sum + p.pending + p.in_progress,
      0
    ),
    totalCompleted: projects.reduce((sum, p) => sum + p.completed, 0),
    totalEarned: projects.reduce((sum, p) => sum + p.earned, 0),
    totalPendingEarnings: projects.reduce(
      (sum, p) => sum + p.pending_earnings,
      0
    ),
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  if (loading && projects.length === 0) {
    return (
      <div className="expert-projects">
        <div className="expert-projects__loading">
          <Spinner size={48} className="" style={{}} />
          <p>Loading projects...</p>
        </div>
        <Footer />
      </div>
    );
  }

  return (
    <div className="expert-projects">

      <div className="expert-projects__content">
        <div className="expert-projects__header">
          <div className="header-left">
            <h1>My Review Projects</h1>
            <span className="project-count">{totalCount} projects</span>
          </div>
          <div className="header-right">
            <Button
              onClick={() => history.push("/expert/dashboard")}
              style={{ backgroundColor: "#6366f1" }}
            >
              Dashboard
            </Button>
          </div>
        </div>

        {/* Summary Stats */}
        <div className="expert-projects__summary">
          <div className="summary-card">
            <span className="summary-value">{summaryStats.totalPending}</span>
            <span className="summary-label">Pending Reviews</span>
          </div>
          <div className="summary-card">
            <span className="summary-value">{summaryStats.totalCompleted}</span>
            <span className="summary-label">Completed</span>
          </div>
          <div className="summary-card earnings">
            <span className="summary-value">
              {formatCurrency(summaryStats.totalEarned)}
            </span>
            <span className="summary-label">Total Earned</span>
          </div>
          <div className="summary-card pending-earnings">
            <span className="summary-value">
              {formatCurrency(summaryStats.totalPendingEarnings)}
            </span>
            <span className="summary-label">Pending Earnings</span>
          </div>
        </div>

        {/* Projects Grid */}
        {projects.length === 0 ? (
          <div className="expert-projects-empty">
            <div className="empty-icon">📋</div>
            <h3 className="empty-title">No Projects Assigned</h3>
            <p className="empty-description">
              You don't have any review tasks assigned yet. Check back later!
            </p>
          </div>
        ) : (
          <>
            <div className="expert-projects-grid">
              {projects.map((project) => (
                <ExpertProjectCard key={project.id} project={project} />
              ))}
            </div>

            {/* Pagination */}
            {(hasMore || page > 1) && (
              <div className="expert-projects__pagination">
                <Button
                  onClick={handlePrevPage}
                  disabled={page <= 1}
                  style={{
                    backgroundColor: page > 1 ? "#6366f1" : "#d1d5db",
                  }}
                >
                  Previous
                </Button>
                <span className="page-info">Page {page}</span>
                <Button
                  onClick={handleNextPage}
                  disabled={!hasMore}
                  style={{
                    backgroundColor: hasMore ? "#6366f1" : "#d1d5db",
                  }}
                >
                  Next
                </Button>
              </div>
            )}
          </>
        )}
      </div>

      <Footer />
    </div>
  );
};

// Page configuration
ExpertProjects.displayName = "ExpertProjects";

export default ExpertProjects;

