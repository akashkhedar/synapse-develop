import React, { useState, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useToast, ToastType, Spinner } from "@synapse/ui";
import "./ExpertExpertiseSection.css";

interface Badge {
  name: string;
  icon: string;
  color: string;
}

interface ExpertExpertise {
  id: number;
  category: number;
  category_name: string;
  category_slug: string;
  category_icon: string;
  specialization: number | null;
  specialization_name: string | null;
  specialization_slug: string | null;
  specialization_icon: string | null;
  status: string;
  assigned_at: string | null;
  assigned_by_email: string | null;
  tasks_reviewed: number;
  accuracy_score: number;
  notes: string;
  badge_info: Badge | null;
  created_at: string;
}

interface ExpertiseSummary {
  active_expertise_count: number;
  total_expertise_count: number;
  total_tasks_reviewed: number;
  active_categories: string[];
}

// Icon mapping for expertise categories
const ICON_MAP: Record<string, string> = {
  image: "🖼️",
  activity: "🏥",
  "file-text": "📝",
  mic: "🎙️",
  video: "🎬",
  "message-circle": "💬",
  zap: "⚡",
  database: "📊",
  target: "🎯",
  tag: "🏷️",
  layers: "📐",
  type: "✍️",
  crosshair: "⊕",
  heart: "❤️",
  circle: "🔘",
  grid: "📏",
  user: "👤",
  smile: "😊",
  link: "🔗",
  globe: "🌍",
  headphones: "🎧",
  users: "👥",
  music: "🎵",
  clock: "⏰",
  star: "⭐",
  edit: "✏️",
  code: "💻",
  "thumbs-up": "👍",
  table: "📋",
  receipt: "🧾",
};

const getIcon = (iconName: string | null | undefined): string => {
  if (!iconName) return "🏆";
  return ICON_MAP[iconName] || "🏆";
};

export const ExpertExpertiseSection: React.FC = () => {
  const toast = useToast();
  
  const [loading, setLoading] = useState(true);
  const [expertise, setExpertise] = useState<ExpertExpertise[]>([]);
  const [summary, setSummary] = useState<ExpertiseSummary | null>(null);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      
      // Fetch expertise list and summary
      const [expertiseRes, summaryRes] = await Promise.all([
        fetch("/api/annotators/expert/expertise", { credentials: "include" }),
        fetch("/api/annotators/expert/expertise/summary", { credentials: "include" }),
      ]);

      if (expertiseRes.ok) {
        const data = await expertiseRes.json();
        setExpertise(data.expertise || []);
      }

      if (summaryRes.ok) {
        const data = await summaryRes.json();
        setSummary(data);
      }
    } catch (error) {
      console.error("Failed to fetch expertise data:", error);
      toast?.show({
        message: "Failed to load expertise data",
        type: ToastType.error,
        duration: 3000,
      });
    } finally {
      setLoading(false);
    }
  }, [toast]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const getStatusBadge = (status: string) => {
    const statusConfig: Record<string, { color: string; label: string }> = {
      assigned: { color: "#f59e0b", label: "Pending Activation" },
      active: { color: "#22c55e", label: "Active" },
      revoked: { color: "#ef4444", label: "Revoked" },
    };
    return statusConfig[status] || { color: "#6b7280", label: status };
  };

  const formatDate = (dateString: string | null): string => {
    if (!dateString) return "-";
    return new Date(dateString).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  };

  if (loading) {
    return (
      <div className="expert-expertise-section loading">
        <Spinner size={32} />
        <span>Loading expertise...</span>
      </div>
    );
  }

  const activeExpertise = expertise.filter(e => e.status === "active");
  const pendingExpertise = expertise.filter(e => e.status === "assigned");
  const revokedExpertise = expertise.filter(e => e.status === "revoked");

  return (
    <motion.section
      className="expert-expertise-section"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.2 }}
    >
      <div className="section-header">
        <div className="header-left">
          <span className="section-tag">EXPERTISE</span>
          <h2 className="section-title">My Assigned Expertise</h2>
        </div>
        {summary && (
          <div className="summary-badges">
            <div className="summary-badge">
              <span className="badge-value">{summary.active_expertise_count}</span>
              <span className="badge-label">Active</span>
            </div>
            <div className="summary-badge reviews">
              <span className="badge-value">{summary.total_tasks_reviewed}</span>
              <span className="badge-label">Reviews</span>
            </div>
          </div>
        )}
      </div>

      {/* Active Expertise */}
      {activeExpertise.length > 0 && (
        <div className="expertise-group">
          <h3 className="group-title">
            <span className="status-dot active" />
            Active Expertise ({activeExpertise.length})
          </h3>
          <div className="expertise-grid">
            <AnimatePresence>
              {activeExpertise.map((exp, index) => (
                <motion.div
                  key={exp.id}
                  className="expertise-card active"
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.1 }}
                  whileHover={{ scale: 1.02 }}
                >
                  <div className="card-icon">
                    {getIcon(exp.specialization_icon || exp.category_icon)}
                  </div>
                  <div className="card-content">
                    <h4 className="expertise-name">
                      {exp.specialization_name || exp.category_name}
                    </h4>
                    {exp.specialization_name && (
                      <span className="category-label">{exp.category_name}</span>
                    )}
                    <div className="expertise-stats">
                      <span className="stat">
                        <span className="stat-label">Reviews:</span>
                        <span className="stat-value">{exp.tasks_reviewed}</span>
                      </span>
                      {exp.accuracy_score > 0 && (
                        <span className="stat">
                          <span className="stat-label">Accuracy:</span>
                          <span className="stat-value">
                            {Number(exp.accuracy_score).toFixed(1)}%
                          </span>
                        </span>
                      )}
                    </div>
                  </div>
                  {exp.badge_info && (
                    <div 
                      className="badge-indicator"
                      style={{ backgroundColor: exp.badge_info.color }}
                      title={exp.badge_info.name}
                    >
                      {getIcon(exp.badge_info.icon)}
                    </div>
                  )}
                  <div className="card-meta">
                    <span className="assigned-at">
                      Since {formatDate(exp.assigned_at)}
                    </span>
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>
          </div>
        </div>
      )}

      {/* Pending Expertise */}
      {pendingExpertise.length > 0 && (
        <div className="expertise-group">
          <h3 className="group-title">
            <span className="status-dot pending" />
            Pending Activation ({pendingExpertise.length})
          </h3>
          <div className="expertise-grid">
            {pendingExpertise.map((exp, index) => (
              <motion.div
                key={exp.id}
                className="expertise-card pending"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
              >
                <div className="card-icon">
                  {getIcon(exp.specialization_icon || exp.category_icon)}
                </div>
                <div className="card-content">
                  <h4 className="expertise-name">
                    {exp.specialization_name || exp.category_name}
                  </h4>
                  {exp.specialization_name && (
                    <span className="category-label">{exp.category_name}</span>
                  )}
                </div>
                <div className="status-badge pending">
                  {getStatusBadge("assigned").label}
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      )}

      {/* Empty State */}
      {expertise.length === 0 && (
        <div className="empty-state">
          <span className="empty-icon">🎯</span>
          <h3 className="empty-title">No Expertise Assigned</h3>
          <p className="empty-description">
            Your expertise areas will be assigned by the admin team.
            Once assigned, you'll be able to review tasks in those categories.
          </p>
        </div>
      )}

      {/* Revoked Expertise (collapsed by default) */}
      {revokedExpertise.length > 0 && (
        <details className="expertise-group revoked">
          <summary className="group-title clickable">
            <span className="status-dot revoked" />
            Revoked Expertise ({revokedExpertise.length})
          </summary>
          <div className="expertise-grid">
            {revokedExpertise.map((exp) => (
              <div key={exp.id} className="expertise-card revoked">
                <div className="card-icon muted">
                  {getIcon(exp.specialization_icon || exp.category_icon)}
                </div>
                <div className="card-content">
                  <h4 className="expertise-name">
                    {exp.specialization_name || exp.category_name}
                  </h4>
                </div>
                <div className="status-badge revoked">Revoked</div>
              </div>
            ))}
          </div>
        </details>
      )}
    </motion.section>
  );
};

export default ExpertExpertiseSection;
