import React, { useState, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useToast, ToastType, Spinner } from "@synapse/ui";
import {
  Icon,
  TrophyIcon,
  PlusIcon,
  CloseIcon,
  CheckIcon,
  ChevronLeftIcon,
  ArrowRightIcon,
  MailIcon,
  CertificateIcon,
  TargetIcon,
  DocumentIcon,
} from "./ExpertiseIcons";
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

  const getStatusInfo = (status: string) => {
    const statusConfig: Record<string, { className: string; label: string }> = {
      claimed: { className: "status-pending", label: "Pending" },
      testing: { className: "status-testing", label: "Testing" },
      verified: { className: "status-verified", label: "Verified" },
      failed: { className: "status-failed", label: "Failed" },
      expired: { className: "status-expired", label: "Expired" },
    };
    return statusConfig[status] || { className: "status-default", label: status };
  };

  if (loading) {
    return (
      <div className="expertise-section expertise-loading">
        <Spinner size={24} />
        <span className="loading-text">Loading expertise...</span>
      </div>
    );
  }

  return (
    <motion.section
      className="expertise-section"
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, ease: "easeOut" }}
    >
      <header className="expertise-header">
        <div className="header-title-group">
          <TrophyIcon size={20} className="header-icon" />
          <h2 className="expertise-title">Expertise & Badges</h2>
        </div>
        <button
          className="add-skill-btn"
          onClick={() => setShowApplyModal(true)}
        >
          <PlusIcon size={16} />
          <span>Add Skill</span>
        </button>
      </header>

      {/* Badges Display */}
      {badges.length > 0 && (
        <div className="badges-section">
          <div className="section-label">
            <span className="label-text">Earned Badges</span>
            <span className="label-count">{badges.length}</span>
          </div>
          <div className="badges-grid">
            {badges.map((badge) => (
              <motion.div
                key={badge.id}
                className="badge-card"
                whileHover={{ y: -2 }}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.2 }}
              >
                <div className="badge-icon-wrapper">
                  <Icon name={badge.icon} size={20} className="badge-icon" />
                </div>
                <div className="badge-content">
                  <span className="badge-name">{badge.name}</span>
                  <span className="badge-category">{badge.category}</span>
                  {badge.score !== null && (
                    <span className="badge-score">{badge.score.toFixed(0)}%</span>
                  )}
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      )}

      {/* My Expertise List */}
      <div className="applications-section">
        <div className="section-label">
          <span className="label-text">My Applications</span>
          {myExpertise.length > 0 && (
            <span className="label-count">{myExpertise.length}</span>
          )}
        </div>
        {myExpertise.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon-wrapper">
              <TargetIcon size={32} className="empty-icon" />
            </div>
            <div className="empty-content">
              <span className="empty-title">No expertise applications yet</span>
              <span className="empty-description">Apply for a skill to start earning in that area</span>
            </div>
          </div>
        ) : (
          <div className="expertise-list">
            {myExpertise.map((exp) => {
              const statusInfo = getStatusInfo(exp.status);
              return (
                <div key={exp.id} className={`expertise-item ${statusInfo.className}`}>
                  <div className="item-icon-wrapper">
                    <Icon name={exp.specialization_icon || exp.category_icon} size={18} className="item-icon" />
                  </div>
                  <div className="item-details">
                    <span className="item-name">
                      {exp.specialization_name || exp.category_name}
                    </span>
                    {exp.specialization_name && (
                      <span className="item-category">{exp.category_name}</span>
                    )}
                  </div>
                  <span className={`item-status ${statusInfo.className}`}>
                    {statusInfo.label}
                  </span>
                  {exp.badge_earned && (
                    <div className="badge-indicator" title="Badge Earned">
                      <TrophyIcon size={16} />
                    </div>
                  )}
                  {(exp.status === 'claimed' || exp.status === 'failed') && exp.can_retry && (
                    <button
                      className="resend-btn"
                      onClick={() => handleResendEmail(exp.id)}
                      title="Resend test email"
                    >
                      <MailIcon size={14} />
                      <span>Resend</span>
                    </button>
                  )}
                  <span className="item-score">
                    {exp.last_test_score !== null && !isNaN(Number(exp.last_test_score)) 
                      ? `${Number(exp.last_test_score).toFixed(0)}%`
                      : "-"
                    }
                  </span>
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
            className="modal-overlay"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setShowApplyModal(false)}
          >
            <motion.div
              className="modal-container"
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 16 }}
              transition={{ duration: 0.2 }}
              onClick={(e) => e.stopPropagation()}
            >
              <header className="modal-header">
                <h2 className="modal-title">Apply for Expertise</h2>
                <button 
                  className="modal-close-btn"
                  onClick={() => setShowApplyModal(false)}
                  aria-label="Close modal"
                >
                  <CloseIcon size={18} />
                </button>
              </header>

              <div className="modal-content">
                {!selectedCategory ? (
                  <>
                    <p className="modal-instruction">
                      Select a category to apply for:
                    </p>
                    <div className="category-grid">
                      {categories.map((cat) => (
                        <motion.button
                          key={cat.id}
                          className="category-card"
                          whileHover={{ y: -2 }}
                          whileTap={{ scale: 0.98 }}
                          onClick={() => setSelectedCategory(cat)}
                        >
                          <div className="category-icon-wrapper">
                            <Icon name={cat.icon} size={22} className="category-icon" />
                          </div>
                          <span className="category-name">{cat.name}</span>
                          <span className="category-count">
                            {cat.specializations.length} {cat.specializations.length === 1 ? 'specialization' : 'specializations'}
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
                      <ChevronLeftIcon size={16} />
                      <span>Back to categories</span>
                    </button>
                    
                    <div className="selected-category-card">
                      <div className="selected-category-icon">
                        <Icon name={selectedCategory.icon} size={20} />
                      </div>
                      <span className="selected-category-name">{selectedCategory.name}</span>
                    </div>

                    <p className="modal-instruction">
                      Select a specialization (optional):
                    </p>

                    <div className="specialization-list">
                      <motion.button
                        className={`specialization-card ${!selectedSpecialization ? 'is-selected' : ''}`}
                        whileHover={{ backgroundColor: 'var(--color-neutral-surface-hover)' }}
                        onClick={() => setSelectedSpecialization(null)}
                      >
                        <div className="spec-icon-wrapper">
                          <DocumentIcon size={18} className="spec-icon" />
                        </div>
                        <div className="spec-content">
                          <span className="spec-name">General {selectedCategory.name}</span>
                          <span className="spec-desc">Take the general category test</span>
                        </div>
                        {!selectedSpecialization && (
                          <div className="spec-check">
                            <CheckIcon size={16} />
                          </div>
                        )}
                      </motion.button>

                      {selectedCategory.specializations.map((spec) => (
                        <motion.button
                          key={spec.id}
                          className={`specialization-card ${selectedSpecialization?.id === spec.id ? 'is-selected' : ''}`}
                          whileHover={{ backgroundColor: 'var(--color-neutral-surface-hover)' }}
                          onClick={() => setSelectedSpecialization(spec)}
                        >
                          <div className="spec-icon-wrapper">
                            <Icon name={spec.icon} size={18} className="spec-icon" />
                          </div>
                          <div className="spec-content">
                            <span className="spec-name">{spec.name}</span>
                            <span className="spec-desc">{spec.description}</span>
                            <span className="spec-passing">Passing score: {spec.passing_score}%</span>
                          </div>
                          {selectedSpecialization?.id === spec.id && (
                            <div className="spec-check">
                              <CheckIcon size={16} />
                            </div>
                          )}
                          {spec.requires_certification && (
                            <div className="spec-cert" title="Requires certification">
                              <CertificateIcon size={16} />
                            </div>
                          )}
                        </motion.button>
                      ))}
                    </div>
                  </>
                )}
              </div>

              {selectedCategory && (
                <footer className="modal-footer">
                  <button
                    className="btn-secondary"
                    onClick={() => setShowApplyModal(false)}
                  >
                    Cancel
                  </button>
                  <motion.button
                    className="btn-primary"
                    whileHover={{ y: -1 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={handleApply}
                    disabled={applying}
                  >
                    {applying ? (
                      <>
                        <Spinner size={14} />
                        <span>Applying...</span>
                      </>
                    ) : (
                      <>
                        <span>Apply & Get Test Link</span>
                        <ArrowRightIcon size={16} />
                      </>
                    )}
                  </motion.button>
                </footer>
              )}
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.section>
  );
};
