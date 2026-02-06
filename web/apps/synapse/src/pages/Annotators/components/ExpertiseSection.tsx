import React, { useState, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useToast, ToastType, Spinner } from "@synapse/ui";
import "./ExpertiseSection.css";

interface Badge {
  id: number;
  name: string;
  category: string;
  category_slug: string;
  icon: string;
  specialization: string | null;
  earned_at: string | null;
  score: number | null;
  tasks_completed: number;
  accuracy_score: number;
}

interface ExpertiseCategory {
  id: number;
  name: string;
  slug: string;
  description: string;
  icon: string;
  specializations: ExpertiseSpecialization[];
}

interface ExpertiseSpecialization {
  id: number;
  name: string;
  slug: string;
  description: string;
  icon: string;
  passing_score: number;
  requires_certification: boolean;
}

interface MyExpertise {
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
  test_attempts: number;
  last_test_score: number | null;
  badge_earned: boolean;
  badge_earned_at: string | null;
  can_retry: boolean;
  test_email_sent: boolean;
}

// Icon mapping for badges
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

export const ExpertiseSection: React.FC = () => {
  const toast = useToast();
  
  const [loading, setLoading] = useState(true);
  const [categories, setCategories] = useState<ExpertiseCategory[]>([]);
  const [myExpertise, setMyExpertise] = useState<MyExpertise[]>([]);
  const [badges, setBadges] = useState<Badge[]>([]);
  const [showApplyModal, setShowApplyModal] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState<ExpertiseCategory | null>(null);
  const [selectedSpecialization, setSelectedSpecialization] = useState<ExpertiseSpecialization | null>(null);
  const [applying, setApplying] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      
      // Fetch all data in parallel
      const [categoriesRes, expertiseRes, badgesRes] = await Promise.all([
        fetch("/api/annotators/expertise/categories", { credentials: "include" }),
        fetch("/api/annotators/expertise/my-expertise", { credentials: "include" }),
        fetch("/api/annotators/expertise/badges", { credentials: "include" }),
      ]);

      if (categoriesRes.ok) {
        const catData = await categoriesRes.json();
        setCategories(catData.categories || []);
      }

      if (expertiseRes.ok) {
        const expData = await expertiseRes.json();
        setMyExpertise(expData.expertise || []);
      }

      if (badgesRes.ok) {
        const badgeData = await badgesRes.json();
        setBadges(badgeData.badges || []);
      }
    } catch (error) {
      console.error("Failed to fetch expertise data:", error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleApply = async () => {
    if (!selectedCategory) return;

    setApplying(true);
    try {
      const response = await fetch("/api/annotators/expertise/apply", {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          category_id: selectedCategory.id,
          specialization_id: selectedSpecialization?.id || null,
        }),
      });

      const data = await response.json();

      if (response.ok) {
        toast?.show({
          message: data.email_sent 
            ? "Test link sent to your email!" 
            : "Application submitted. Check your email for the test link.",
          type: ToastType.info,
          duration: 5000,
        });
        setShowApplyModal(false);
        setSelectedCategory(null);
        setSelectedSpecialization(null);
        fetchData();
      } else {
        toast?.show({
          message: data.error || "Failed to apply",
          type: ToastType.error,
          duration: 3000,
        });
      }
    } catch (error) {
      toast?.show({
        message: "Failed to submit application",
        type: ToastType.error,
        duration: 3000,
      });
    } finally {
      setApplying(false);
    }
  };

  const handleResendEmail = async (expertiseId: number) => {
    try {
      const response = await fetch(`/api/annotators/expertise/resend-email/${expertiseId}`, {
        method: "POST",
        credentials: "include",
      });

      const data = await response.json();

      if (response.ok) {
        toast?.show({
          message: "Test email resent successfully!",
          type: ToastType.info,
          duration: 3000,
        });
        fetchData();
      } else {
        toast?.show({
          message: data.error || "Failed to resend email",
          type: ToastType.error,
          duration: 3000,
        });
      }
    } catch (error) {
      toast?.show({
        message: "Failed to resend email",
        type: ToastType.error,
        duration: 3000,
      });
    }
  };

  const getStatusBadge = (status: string) => {
    const statusConfig: Record<string, { color: string; label: string }> = {
      claimed: { color: "#f59e0b", label: "Pending" },
      testing: { color: "#3b82f6", label: "Testing" },
      verified: { color: "#22c55e", label: "Verified" },
      failed: { color: "#ef4444", label: "Failed" },
      expired: { color: "#6b7280", label: "Expired" },
    };
    return statusConfig[status] || { color: "#6b7280", label: status };
  };

  if (loading) {
    return (
      <div className="expertise-section loading">
        <Spinner size={32} />
        <span>Loading expertise...</span>
      </div>
    );
  }

  return (
    <motion.section
      className="section-card expertise-section"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.45 }}
    >
      <div className="section-header">
        <span className="section-number">06/</span>
        <h2 className="section-title">My Expertise & Badges</h2>
        <button
          className="apply-btn"
          onClick={() => setShowApplyModal(true)}
        >
          + Apply for New Skill
        </button>
      </div>

      {/* Badges Display */}
      {badges.length > 0 && (
        <div className="badges-container">
          <h3 className="subsection-title">🏆 Earned Badges</h3>
          <div className="badges-grid">
            {badges.map((badge) => (
              <motion.div
                key={badge.id}
                className="badge-card"
                whileHover={{ scale: 1.05 }}
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
              >
                <div className="badge-icon">{getIcon(badge.icon)}</div>
                <div className="badge-info">
                  <span className="badge-name">{badge.name}</span>
                  <span className="badge-category">{badge.category}</span>
                  {badge.score && (
                    <span className="badge-score">{badge.score.toFixed(0)}% score</span>
                  )}
                </div>
                <div className="badge-glow" />
              </motion.div>
            ))}
          </div>
        </div>
      )}

      {/* My Expertise List */}
      <div className="expertise-list">
        <h3 className="subsection-title">📋 My Applications</h3>
        {myExpertise.length === 0 ? (
          <div className="empty-state">
            <span className="empty-icon">🎯</span>
            <span className="empty-text">No expertise applications yet</span>
            <span className="empty-hint">Apply for a skill to start earning in that area</span>
          </div>
        ) : (
          <div className="expertise-items">
            {myExpertise.map((exp) => {
              const statusInfo = getStatusBadge(exp.status);
              return (
                <div key={exp.id} className={`expertise-item status-${exp.status}`}>
                  <div className="expertise-icon">
                    {getIcon(exp.specialization_icon || exp.category_icon)}
                  </div>
                  <div className="expertise-details">
                    <span className="expertise-name">
                      {exp.specialization_name || exp.category_name}
                    </span>
                    {exp.specialization_name && (
                      <span className="expertise-category">{exp.category_name}</span>
                    )}
                  </div>
                  <div 
                    className="expertise-status"
                    style={{ backgroundColor: statusInfo.color }}
                  >
                    {statusInfo.label}
                  </div>
                  {exp.badge_earned && (
                    <div className="badge-earned-indicator" title="Badge Earned!">
                      🏆
                    </div>
                  )}
                  {(exp.status === 'claimed' || exp.status === 'failed') && exp.can_retry && (
                    <button
                      className="resend-btn"
                      onClick={() => handleResendEmail(exp.id)}
                      title="Resend test email"
                    >
                      📧 Resend
                    </button>
                  )}
                  {exp.last_test_score !== null && !isNaN(Number(exp.last_test_score)) ? (
                    <span className="last-score">
                      Last: {Number(exp.last_test_score).toFixed(0)}%
                    </span>
                  ) : (
                    <span className="last-score">Last: -</span>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Apply Modal */}
      <AnimatePresence>
        {showApplyModal && (
          <motion.div
            className="expertise-modal-overlay"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setShowApplyModal(false)}
          >
            <motion.div
              className="expertise-modal"
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
            >
              <div className="modal-header">
                <h2>Apply for New Expertise</h2>
                <button 
                  className="close-btn"
                  onClick={() => setShowApplyModal(false)}
                >
                  ✕
                </button>
              </div>

              <div className="modal-body">
                {!selectedCategory ? (
                  <>
                    <p className="modal-instruction">
                      Select a category to apply for:
                    </p>
                    <div className="categories-grid">
                      {categories.map((cat) => (
                        <motion.button
                          key={cat.id}
                          className="category-card"
                          whileHover={{ scale: 1.02 }}
                          whileTap={{ scale: 0.98 }}
                          onClick={() => setSelectedCategory(cat)}
                        >
                          <span className="cat-icon">{getIcon(cat.icon)}</span>
                          <span className="cat-name">{cat.name}</span>
                          <span className="cat-count">
                            {cat.specializations.length} specializations
                          </span>
                        </motion.button>
                      ))}
                    </div>
                  </>
                ) : (
                  <>
                    <button 
                      className="back-btn"
                      onClick={() => {
                        setSelectedCategory(null);
                        setSelectedSpecialization(null);
                      }}
                    >
                      ← Back to categories
                    </button>
                    
                    <div className="selected-category">
                      <span className="cat-icon">{getIcon(selectedCategory.icon)}</span>
                      <span className="cat-name">{selectedCategory.name}</span>
                    </div>

                    <p className="modal-instruction">
                      Select a specialization (optional):
                    </p>

                    <div className="specializations-list">
                      <motion.button
                        className={`spec-card ${!selectedSpecialization ? 'selected' : ''}`}
                        whileHover={{ scale: 1.01 }}
                        onClick={() => setSelectedSpecialization(null)}
                      >
                        <span className="spec-icon">📋</span>
                        <div className="spec-info">
                          <span className="spec-name">General {selectedCategory.name}</span>
                          <span className="spec-desc">Take the general category test</span>
                        </div>
                        {!selectedSpecialization && <span className="check">✓</span>}
                      </motion.button>

                      {selectedCategory.specializations.map((spec) => (
                        <motion.button
                          key={spec.id}
                          className={`spec-card ${selectedSpecialization?.id === spec.id ? 'selected' : ''}`}
                          whileHover={{ scale: 1.01 }}
                          onClick={() => setSelectedSpecialization(spec)}
                        >
                          <span className="spec-icon">{getIcon(spec.icon)}</span>
                          <div className="spec-info">
                            <span className="spec-name">{spec.name}</span>
                            <span className="spec-desc">{spec.description}</span>
                            <span className="spec-score">Passing: {spec.passing_score}%</span>
                          </div>
                          {selectedSpecialization?.id === spec.id && <span className="check">✓</span>}
                          {spec.requires_certification && (
                            <span className="cert-badge" title="Requires certification">📜</span>
                          )}
                        </motion.button>
                      ))}
                    </div>
                  </>
                )}
              </div>

              {selectedCategory && (
                <div className="modal-footer">
                  <button
                    className="cancel-btn"
                    onClick={() => setShowApplyModal(false)}
                  >
                    Cancel
                  </button>
                  <motion.button
                    className="submit-btn"
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={handleApply}
                    disabled={applying}
                  >
                    {applying ? (
                      <>
                        <Spinner size={16} /> Applying...
                      </>
                    ) : (
                      <>Apply & Get Test Link →</>
                    )}
                  </motion.button>
                </div>
              )}
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.section>
  );
};
