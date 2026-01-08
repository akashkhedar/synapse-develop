import React, { useState, useEffect } from "react";
import { useHistory } from "react-router-dom";
import { Button, useToast, ToastType } from "@synapse/ui";
import { Navbar } from "../../components/Navbar/Navbar";
import { Footer } from "../../components/Footer/Footer";
import { Spinner } from "../../components";
import "./ExpertDashboard.scss";

interface ExpertDashboardData {
  expert_id: number;
  status: string;
  expertise_level: string;
  expertise_areas: string[];
  pending_reviews: number;
  pending_tasks: Array<{
    id: number;
    task_id: number;
    project_id: number;
    project_title: string;
    assignment_reason: string;
    disagreement_score: number;
    assigned_at: string;
    is_overdue: boolean;
  }>;
  recent_completed: Array<{
    id: number;
    task_id: number;
    status: string;
    payment: number;
    completed_at: string;
  }>;
  stats: {
    total_reviews: number;
    total_approvals: number;
    total_rejections: number;
    total_corrections: number;
    approval_rate: number;
    average_review_time: number;
  };
  today: {
    reviews_completed: number;
    earnings: number;
  };
  earnings: {
    total_earned: number;
    pending_payout: number;
    available_balance: number;
    monthly_earnings: number;
  };
}

export const ExpertDashboard: React.FC = () => {
  const history = useHistory();
  const toast = useToast();
  const [dashboard, setDashboard] = useState<ExpertDashboardData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboard();
  }, []);

  const fetchDashboard = async () => {
    try {
      const response = await fetch("/api/annotators/expert/dashboard", {
        credentials: "include",
      });

      if (response.ok) {
        const data = await response.json();
        setDashboard(data);
      } else if (response.status === 403) {
        toast?.show({
          message: "Access denied. Not an expert account.",
          type: ToastType.error,
        });
        history.push("/annotators/login");
      } else if (response.status === 401) {
        history.push("/annotators/login");
      }
    } catch (error) {
      console.error("Failed to fetch dashboard:", error);
      toast?.show({
        message: "Failed to load dashboard",
        type: ToastType.error,
      });
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  if (loading) {
    return (
      <div className="expert-dashboard">
        <Navbar />
        <div className="expert-dashboard__loading">
          <Spinner size={48} className="" style={{}} />
          <p>Loading dashboard...</p>
        </div>
        <Footer />
      </div>
    );
  }

  if (!dashboard) {
    return (
      <div className="expert-dashboard">
        <Navbar />
        <div className="expert-dashboard__error">
          <p>Failed to load dashboard data</p>
          <Button onClick={() => fetchDashboard()}>Retry</Button>
        </div>
        <Footer />
      </div>
    );
  }

  return (
    <div className="expert-dashboard">
      <Navbar />

      <div className="expert-dashboard__content">
        {/* Header - Simplified */}
        <div className="expert-dashboard__header">
          <div className="header-left">
            <h1>Expert Dashboard</h1>
            <span className={`status-badge ${dashboard.status}`}>
              {dashboard.expertise_level.replace("_", " ")}
            </span>
          </div>
        </div>

        {/* Quick Stats - 4 essential cards */}
        <div className="expert-dashboard__quick-stats">
          <div
            className="quick-stat-card clickable"
            onClick={() => history.push("/expert/projects")}
          >
            <div className="stat-icon">📋</div>
            <div className="stat-info">
              <span className="stat-value">{dashboard.pending_reviews}</span>
              <span className="stat-label">Pending Reviews</span>
            </div>
          </div>
          <div className="quick-stat-card">
            <div className="stat-icon">✅</div>
            <div className="stat-info">
              <span className="stat-value">
                {dashboard.stats.total_reviews}
              </span>
              <span className="stat-label">Total Completed</span>
            </div>
          </div>
          <div className="quick-stat-card">
            <div className="stat-icon">📊</div>
            <div className="stat-info">
              <span className="stat-value">
                {dashboard.stats.approval_rate.toFixed(0)}%
              </span>
              <span className="stat-label">Approval Rate</span>
            </div>
          </div>
          <div className="quick-stat-card earnings">
            <div className="stat-icon">💰</div>
            <div className="stat-info">
              <span className="stat-value">
                {formatCurrency(dashboard.earnings.available_balance)}
              </span>
              <span className="stat-label">Available</span>
            </div>
          </div>
        </div>

        {/* Today's Activity */}
        <div className="expert-dashboard__today">
          <h3>Today</h3>
          <div className="today-stats">
            <div className="today-stat">
              <span className="value">{dashboard.today.reviews_completed}</span>
              <span className="label">Reviews</span>
            </div>
            <div className="today-stat">
              <span className="value">
                {formatCurrency(dashboard.today.earnings)}
              </span>
              <span className="label">Earned</span>
            </div>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="expert-dashboard__actions">
          <Button
            onClick={() => history.push("/expert/projects")}
            style={{ backgroundColor: "#3b82f6", flex: 1 }}
          >
            View Projects ({dashboard.pending_reviews} pending)
          </Button>
          <Button
            onClick={() => history.push("/expert/payment/dashboard")}
            style={{ backgroundColor: "#10b981", flex: 1 }}
          >
            Earnings & Payouts
          </Button>
        </div>

        {/* Recent Reviews - Simplified table */}
        <div className="expert-dashboard__recent">
          <h3>Recent Reviews</h3>
          {dashboard.recent_completed.length === 0 ? (
            <p className="no-data">No completed reviews yet.</p>
          ) : (
            <div className="recent-list">
              {dashboard.recent_completed.slice(0, 5).map((review) => (
                <div key={review.id} className="recent-item">
                  <div className="item-left">
                    <span className={`status-dot ${review.status}`}></span>
                    <span className="task-id">Task #{review.task_id}</span>
                  </div>
                  <div className="item-right">
                    <span className="payment">
                      {formatCurrency(review.payment)}
                    </span>
                    <span className="date">
                      {review.completed_at
                        ? new Date(review.completed_at).toLocaleDateString()
                        : "-"}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      <Footer />
    </div>
  );
};

// Page configuration
ExpertDashboard.displayName = "ExpertDashboard";

