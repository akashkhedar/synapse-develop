import React, { useState, useEffect, useMemo } from "react";
import { useHistory } from "react-router-dom";
import { motion } from "framer-motion";
import { useToast, ToastType } from "@synapse/ui";
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

// Floating pixels decoration
const FloatingPixels = () => {
  const pixels = [
    { x: "8%", y: "20%", size: 3, opacity: 0.2 },
    { x: "15%", y: "60%", size: 4, opacity: 0.25 },
    { x: "88%", y: "25%", size: 3, opacity: 0.2 },
    { x: "92%", y: "70%", size: 4, opacity: 0.3 },
  ];
  
  return (
    <div className="floating-pixels">
      {pixels.map((p, i) => (
        <motion.div
          key={i}
          className="pixel"
          style={{ left: p.x, top: p.y, width: p.size, height: p.size, opacity: p.opacity }}
          animate={{ opacity: [p.opacity * 0.5, p.opacity, p.opacity * 0.5], scale: [0.9, 1, 0.9] }}
          transition={{ duration: 4 + Math.random() * 2, repeat: Infinity, ease: "linear" }}
        />
      ))}
    </div>
  );
};

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

  const formatTime = (minutes: number) => {
    if (minutes < 60) return `${Math.round(minutes)}m`;
    const hours = Math.floor(minutes / 60);
    const mins = Math.round(minutes % 60);
    return `${hours}h ${mins}m`;
  };

  const formatRelativeTime = (dateStr: string) => {
    const date = new Date(dateStr);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    return `${diffDays}d ago`;
  };

  // Performance metrics
  const performanceData = useMemo(() => {
    if (!dashboard) return null;
    const { stats } = dashboard;
    const total = stats.total_approvals + stats.total_rejections + stats.total_corrections;
    return {
      approvalPercent: total > 0 ? (stats.total_approvals / total) * 100 : 0,
      rejectionPercent: total > 0 ? (stats.total_rejections / total) * 100 : 0,
      correctionPercent: total > 0 ? (stats.total_corrections / total) * 100 : 0,
    };
  }, [dashboard]);

  if (loading) {
    return (
      <div className="expert-page">
        <div className="expert-loading">
          <motion.div
            className="loader-dot"
            animate={{ scale: [1, 1.2, 1], opacity: [0.5, 1, 0.5] }}
            transition={{ duration: 1.5, repeat: Infinity }}
          />
          <span className="loader-text">Loading dashboard...</span>
        </div>
      </div>
    );
  }

  if (!dashboard) {
    return (
      <div className="expert-page">
        <div className="expert-error">
          <span className="error-code">ERROR_LOAD</span>
          <h2>Unable to load dashboard</h2>
          <p className="error-desc">Something went wrong while fetching data.</p>
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            className="retry-btn"
            onClick={fetchDashboard}
          >
            Try Again
          </motion.button>
        </div>
      </div>
    );
  }

  return (
    <div className="expert-page">
      <FloatingPixels />
      <div className="bg-grid" />
      <div className="bg-glow" />

      <div className="expert-container">
        {/* Header */}
        <motion.header 
          className="expert-header"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <div className="header-left">
            <span className="header-tag">// EXPERT PANEL</span>
            <h1 className="header-title">Dashboard</h1>
            <div className="header-badge">
              <span className="badge-icon">✦</span>
              <span className="badge-text">{dashboard.expertise_level.replace("_", " ")}</span>
            </div>
          </div>
          <div className="header-actions">
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              className="action-btn secondary"
              onClick={() => history.push("/expert/earnings")}
            >
              Earnings
            </motion.button>
            <motion.button
              whileHover={{ scale: 1.02, boxShadow: "0 0 30px rgba(139, 92, 246, 0.3)" }}
              whileTap={{ scale: 0.98 }}
              className="action-btn primary"
              onClick={() => history.push("/expert/projects")}
            >
              Review Queue →
            </motion.button>
          </div>
        </motion.header>

        {/* Stats Row */}
        <motion.div 
          className="stats-row"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.1 }}
        >
          <div 
            className="stat-card pending clickable"
            onClick={() => history.push("/expert/projects")}
          >
            <div className="stat-label">PENDING REVIEWS</div>
            <div className="stat-value highlight">{dashboard.pending_reviews}</div>
            <div className="stat-hint">Click to review</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">COMPLETED</div>
            <div className="stat-value">{dashboard.stats.total_reviews}</div>
            <div className="stat-hint">Total reviews</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">APPROVAL RATE</div>
            <div className="stat-value">{dashboard.stats.approval_rate.toFixed(0)}%</div>
            <div className="stat-hint">Quality metric</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">AVAILABLE</div>
            <div className="stat-value accent">{formatCurrency(dashboard.earnings.available_balance)}</div>
            <div className="stat-hint">Ready to withdraw</div>
          </div>
        </motion.div>

        {/* Main Grid */}
        <div className="main-grid">
          {/* Left Column */}
          <div className="left-col">
            {/* Today's Activity */}
            <motion.section 
              className="section-card today-section"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.2 }}
            >
              <div className="section-header">
                <span className="section-number">01/</span>
                <h2 className="section-title">Today</h2>
                <span className="section-date">
                  {new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                </span>
              </div>
              
              <div className="today-grid">
                <div className="today-stat">
                  <span className="today-value">{dashboard.today.reviews_completed}</span>
                  <span className="today-label">Reviews Completed</span>
                </div>
                <div className="today-stat">
                  <span className="today-value accent">{formatCurrency(dashboard.today.earnings)}</span>
                  <span className="today-label">Earned Today</span>
                </div>
                <div className="today-stat">
                  <span className="today-value">{formatTime(dashboard.stats.average_review_time)}</span>
                  <span className="today-label">Avg Review Time</span>
                </div>
              </div>
            </motion.section>

            {/* Performance Breakdown */}
            <motion.section 
              className="section-card performance-section"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.3 }}
            >
              <div className="section-header">
                <span className="section-number">02/</span>
                <h2 className="section-title">Performance</h2>
              </div>
              
              <div className="performance-breakdown">
                <div className="perf-row">
                  <div className="perf-info">
                    <span className="perf-label">Approved</span>
                    <span className="perf-count">{dashboard.stats.total_approvals}</span>
                  </div>
                  <div className="perf-bar">
                    <motion.div 
                      className="perf-fill approved"
                      initial={{ width: 0 }}
                      animate={{ width: `${performanceData?.approvalPercent || 0}%` }}
                      transition={{ duration: 0.8, delay: 0.4 }}
                    />
                  </div>
                  <span className="perf-percent">{performanceData?.approvalPercent.toFixed(0)}%</span>
                </div>
                
                <div className="perf-row">
                  <div className="perf-info">
                    <span className="perf-label">Corrected</span>
                    <span className="perf-count">{dashboard.stats.total_corrections}</span>
                  </div>
                  <div className="perf-bar">
                    <motion.div 
                      className="perf-fill corrected"
                      initial={{ width: 0 }}
                      animate={{ width: `${performanceData?.correctionPercent || 0}%` }}
                      transition={{ duration: 0.8, delay: 0.5 }}
                    />
                  </div>
                  <span className="perf-percent">{performanceData?.correctionPercent.toFixed(0)}%</span>
                </div>
                
                <div className="perf-row">
                  <div className="perf-info">
                    <span className="perf-label">Rejected</span>
                    <span className="perf-count">{dashboard.stats.total_rejections}</span>
                  </div>
                  <div className="perf-bar">
                    <motion.div 
                      className="perf-fill rejected"
                      initial={{ width: 0 }}
                      animate={{ width: `${performanceData?.rejectionPercent || 0}%` }}
                      transition={{ duration: 0.8, delay: 0.6 }}
                    />
                  </div>
                  <span className="perf-percent">{performanceData?.rejectionPercent.toFixed(0)}%</span>
                </div>
              </div>
            </motion.section>

            {/* Earnings Summary */}
            <motion.section 
              className="section-card earnings-section"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.35 }}
            >
              <div className="section-header">
                <span className="section-number">03/</span>
                <h2 className="section-title">Earnings</h2>
                <button className="view-all" onClick={() => history.push("/expert/earnings")}>
                  Details
                </button>
              </div>
              
              <div className="earnings-grid">
                <div className="earning-item">
                  <span className="earning-label">This Month</span>
                  <span className="earning-value">{formatCurrency(dashboard.earnings.monthly_earnings)}</span>
                </div>
                <div className="earning-item">
                  <span className="earning-label">Pending Payout</span>
                  <span className="earning-value">{formatCurrency(dashboard.earnings.pending_payout)}</span>
                </div>
                <div className="earning-item">
                  <span className="earning-label">Total Earned</span>
                  <span className="earning-value">{formatCurrency(dashboard.earnings.total_earned)}</span>
                </div>
              </div>
            </motion.section>
          </div>

          {/* Right Column */}
          <div className="right-col">
            {/* Pending Tasks */}
            <motion.section 
              className="section-card queue-section"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.25 }}
            >
              <div className="section-header">
                <span className="section-number">04/</span>
                <h2 className="section-title">Review Queue</h2>
                <span className="queue-count">{dashboard.pending_tasks.length}</span>
              </div>
              
              <div className="queue-list">
                {dashboard.pending_tasks.length === 0 ? (
                  <div className="empty-queue">
                    <span className="empty-icon">✓</span>
                    <span className="empty-text">All caught up!</span>
                    <span className="empty-hint">No pending reviews</span>
                  </div>
                ) : (
                  dashboard.pending_tasks.slice(0, 5).map((task, i) => (
                    <motion.div 
                      key={task.id} 
                      className={`queue-item ${task.is_overdue ? 'overdue' : ''}`}
                      initial={{ opacity: 0, x: 20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: 0.3 + i * 0.05 }}
                      onClick={() => history.push(`/expert/review/${task.id}`)}
                    >
                      <div className="queue-left">
                        <span className="queue-indicator" />
                        <div className="queue-info">
                          <span className="queue-project">{task.project_title}</span>
                          <span className="queue-reason">{task.assignment_reason}</span>
                        </div>
                      </div>
                      <div className="queue-right">
                        {task.is_overdue && <span className="overdue-badge">!</span>}
                        <span className="queue-time">{formatRelativeTime(task.assigned_at)}</span>
                      </div>
                    </motion.div>
                  ))
                )}
              </div>
              
              {dashboard.pending_tasks.length > 5 && (
                <button className="view-more" onClick={() => history.push("/expert/projects")}>
                  View all {dashboard.pending_tasks.length} tasks →
                </button>
              )}
            </motion.section>

            {/* Recent Completed */}
            <motion.section 
              className="section-card recent-section"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.4 }}
            >
              <div className="section-header">
                <span className="section-number">05/</span>
                <h2 className="section-title">Recent Reviews</h2>
              </div>
              
              <div className="recent-list">
                {dashboard.recent_completed.length === 0 ? (
                  <div className="empty-state">
                    <span className="empty-text">No completed reviews yet</span>
                  </div>
                ) : (
                  dashboard.recent_completed.slice(0, 5).map((review) => (
                    <div key={review.id} className="recent-item">
                      <div className="recent-left">
                        <span className={`status-indicator ${review.status}`} />
                        <span className="recent-task">Task #{review.task_id}</span>
                      </div>
                      <div className="recent-right">
                        <span className="recent-payment">{formatCurrency(review.payment)}</span>
                        <span className="recent-date">
                          {review.completed_at ? formatRelativeTime(review.completed_at) : '-'}
                        </span>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </motion.section>

            {/* Expertise Areas */}
            {dashboard.expertise_areas && dashboard.expertise_areas.length > 0 && (
              <motion.section 
                className="section-card expertise-section"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.45 }}
              >
                <div className="section-header">
                  <span className="section-number">06/</span>
                  <h2 className="section-title">Expertise</h2>
                </div>
                
                <div className="expertise-tags">
                  {dashboard.expertise_areas.map((area, i) => (
                    <span key={i} className="expertise-tag">{area}</span>
                  ))}
                </div>
              </motion.section>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

// Page configuration
ExpertDashboard.displayName = "ExpertDashboard";

