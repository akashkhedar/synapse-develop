import React, { useState, useEffect } from "react";
import { useHistory, useParams } from "react-router-dom";
import { Button, useToast, ToastType } from "@synapse/ui";
import { Navbar } from "../../components/Navbar/Navbar";
import { Footer } from "../../components/Footer/Footer";
import { Spinner } from "../../components";
import "./ExpertReviewPage.scss";

interface AnnotationData {
  id: number;
  annotator_email: string;
  annotator_id: number;
  completed_at: string;
  time_spent: number;
  result: any;
  flagged: boolean;
  flag_reason: string;
}

interface ConsensusData {
  id: number;
  status: string;
  consolidated_result: any;
  average_agreement: number;
  min_agreement: number;
  max_agreement: number;
  consolidation_method: string;
  required_annotations: number;
  current_annotations: number;
}

interface ReviewTaskDetails {
  success: boolean;
  task_id: number;
  task_data: any;
  project_id: number;
  project_title: string;
  consensus: ConsensusData;
  annotations: AnnotationData[];
  review_task: {
    id: number;
    status: string;
    assigned_at: string;
    assignment_reason: string;
  } | null;
  can_accept: boolean;
  can_reject: boolean;
  error?: string;
}

export const ExpertReviewPage: React.FC = () => {
  const history = useHistory();
  const toast = useToast();
  const { taskId } = useParams<{ taskId: string }>();

  const [reviewData, setReviewData] = useState<ReviewTaskDetails | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);

  const [showRejectModal, setShowRejectModal] = useState(false);
  const [rejectionReason, setRejectionReason] = useState("disagreement");
  const [reviewNotes, setReviewNotes] = useState("");
  const [requireReannotation, setRequireReannotation] = useState(true);

  useEffect(() => {
    fetchReviewDetails();
  }, [taskId]);

  const fetchReviewDetails = async () => {
    try {
      const response = await fetch(
        `/api/annotators/expert/review/${taskId}/details`,
        {
          credentials: "include",
        }
      );

      if (response.ok) {
        const data = await response.json();
        setReviewData(data);
      } else if (response.status === 403) {
        toast?.show({
          message: "Access denied. Expert privileges required.",
          type: ToastType.error,
        });
        history.push("/expert/dashboard");
      } else if (response.status === 401) {
        history.push("/annotators/login");
      } else {
        const data = await response.json();
        toast?.show({
          message: data.error || "Failed to load review details",
          type: ToastType.error,
        });
      }
    } catch (error) {
      console.error("Failed to fetch review details:", error);
      toast?.show({
        message: "Failed to load review details",
        type: ToastType.error,
      });
    } finally {
      setLoading(false);
    }
  };

  const handleAccept = async () => {
    if (!reviewData) return;

    setActionLoading(true);
    try {
      const response = await fetch(
        `/api/annotators/expert/review/${taskId}/action`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          credentials: "include",
          body: JSON.stringify({
            action: "accept",
            review_notes: reviewNotes,
          }),
        }
      );

      if (response.ok) {
        const result = await response.json();
        toast?.show({
          message: "✅ Annotation accepted and finalized!",
          type: ToastType.info,
        });

        // Redirect back to dashboard after 1 second
        setTimeout(() => {
          history.push("/expert/dashboard");
        }, 1000);
      } else {
        const data = await response.json();
        toast?.show({
          message: data.error || "Failed to accept annotation",
          type: ToastType.error,
        });
      }
    } catch (error) {
      console.error("Failed to accept:", error);
      toast?.show({
        message: "Failed to accept annotation",
        type: ToastType.error,
      });
    } finally {
      setActionLoading(false);
    }
  };

  const handleReject = async () => {
    if (!reviewData || !rejectionReason) return;

    setActionLoading(true);
    try {
      const response = await fetch(
        `/api/annotators/expert/review/${taskId}/action`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          credentials: "include",
          body: JSON.stringify({
            action: "reject",
            rejection_reason: rejectionReason,
            review_notes: reviewNotes,
            require_reannotation: requireReannotation,
          }),
        }
      );

      if (response.ok) {
        const result = await response.json();
        toast?.show({
          message: `❌ Annotation rejected. ${result.annotators_notified} annotators notified.`,
          type: ToastType.info,
        });

        setShowRejectModal(false);

        // Redirect back to dashboard after 1 second
        setTimeout(() => {
          history.push("/expert/dashboard");
        }, 1000);
      } else {
        const data = await response.json();
        toast?.show({
          message: data.error || "Failed to reject annotation",
          type: ToastType.error,
        });
      }
    } catch (error) {
      console.error("Failed to reject:", error);
      toast?.show({
        message: "Failed to reject annotation",
        type: ToastType.error,
      });
    } finally {
      setActionLoading(false);
    }
  };

  const openSynapseAnnotation = () => {
    // Open the task in Synapse annotation interface
    window.open(
      `/projects/${reviewData?.project_id}/data?task=${taskId}`,
      "_blank"
    );
  };

  if (loading) {
    return (
      <div className="expert-review-page">
        <Navbar />
        <div className="expert-review-page__loading">
          <Spinner size={48} className="" style={{}} />
          <p>Loading review details...</p>
        </div>
        <Footer />
      </div>
    );
  }

  if (!reviewData || !reviewData.success) {
    return (
      <div className="expert-review-page">
        <Navbar />
        <div className="expert-review-page__error">
          <h2>Failed to Load Review</h2>
          <p>{reviewData?.error || "Unable to load review details"}</p>
          <Button onClick={() => history.push("/expert/dashboard")}>
            Back to Dashboard
          </Button>
        </div>
        <Footer />
      </div>
    );
  }

  const { consensus, annotations, task_data } = reviewData;

  return (
    <div className="expert-review-page">
      <Navbar />

      <div className="expert-review-page__content">
        {/* Header */}
        <div className="expert-review-page__header">
          <div className="header-left">
            <Button
              variant="neutral"
              onClick={() => history.push("/expert/dashboard")}
            >
              ← Back to Dashboard
            </Button>
            <h1>Expert Review - Task #{taskId}</h1>
            <p className="project-title">{reviewData.project_title}</p>
          </div>

          <div className="header-right">
            <Button variant="neutral" onClick={openSynapseAnnotation}>
              📝 View in Annotation Tool
            </Button>
          </div>
        </div>

        {/* Consensus Info */}
        <div className="expert-review-page__consensus-card">
          <h2>Consensus Summary</h2>
          <div className="consensus-stats">
            <div className="stat">
              <span className="label">Status:</span>
              <span className={`value status-${consensus.status}`}>
                {consensus.status}
              </span>
            </div>
            <div className="stat">
              <span className="label">Agreement Score:</span>
              <span className="value">
                {(consensus.average_agreement * 100).toFixed(1)}%
              </span>
            </div>
            <div className="stat">
              <span className="label">Annotations:</span>
              <span className="value">
                {consensus.current_annotations} /{" "}
                {consensus.required_annotations}
              </span>
            </div>
            <div className="stat">
              <span className="label">Consolidation Method:</span>
              <span className="value">{consensus.consolidation_method}</span>
            </div>
          </div>

          {consensus.consolidated_result && (
            <div className="consolidated-result">
              <h3>Consolidated Result</h3>
              <pre>
                {JSON.stringify(consensus.consolidated_result, null, 2)}
              </pre>
            </div>
          )}
        </div>

        {/* Individual Annotations */}
        <div className="expert-review-page__annotations">
          <h2>Individual Annotations ({annotations.length})</h2>

          {annotations.map((annotation, idx) => (
            <div key={annotation.id} className="annotation-card">
              <div className="annotation-header">
                <h3>Annotation {idx + 1}</h3>
                <div className="annotation-meta">
                  <span>By: {annotation.annotator_email}</span>
                  <span>•</span>
                  <span>
                    Time: {Math.floor(annotation.time_spent / 60)}m{" "}
                    {annotation.time_spent % 60}s
                  </span>
                  {annotation.flagged && (
                    <>
                      <span>•</span>
                      <span className="flagged">
                        ⚠️ Flagged: {annotation.flag_reason}
                      </span>
                    </>
                  )}
                </div>
              </div>

              <div className="annotation-result">
                <pre>{JSON.stringify(annotation.result, null, 2)}</pre>
              </div>
            </div>
          ))}
        </div>

        {/* Review Notes */}
        <div className="expert-review-page__notes">
          <h2>Review Notes (Optional)</h2>
          <textarea
            className="review-notes-input"
            placeholder="Add your review notes here..."
            value={reviewNotes}
            onChange={(e) => setReviewNotes(e.target.value)}
            rows={4}
          />
        </div>

        {/* Action Buttons */}
        <div className="expert-review-page__actions">
          <Button
            variant="primary"
            size="medium"
            disabled={!reviewData.can_accept || actionLoading}
            onClick={handleAccept}
            className="action-button accept"
          >
            {actionLoading ? "Processing..." : "✓ Accept & Finalize"}
          </Button>

          <Button
            variant="negative"
            size="medium"
            disabled={!reviewData.can_reject || actionLoading}
            onClick={() => setShowRejectModal(true)}
            className="action-button reject"
          >
            ✗ Reject & Request Rework
          </Button>
        </div>
      </div>

      {/* Reject Modal */}
      {showRejectModal && (
        <div
          className="modal-overlay"
          onClick={() => setShowRejectModal(false)}
        >
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h2>Reject Annotation</h2>

            <div className="form-group">
              <label>Rejection Reason *</label>
              <select
                value={rejectionReason}
                onChange={(e) => setRejectionReason(e.target.value)}
              >
                <option value="disagreement">
                  High Annotator Disagreement
                </option>
                <option value="low_quality">Low Quality Annotations</option>
                <option value="incorrect_labels">Incorrect Labels</option>
                <option value="incomplete">Incomplete Annotation</option>
                <option value="ambiguous">Ambiguous Data - Skip</option>
                <option value="other">Other</option>
              </select>
            </div>

            <div className="form-group">
              <label>Additional Notes</label>
              <textarea
                value={reviewNotes}
                onChange={(e) => setReviewNotes(e.target.value)}
                placeholder="Provide specific feedback for annotators..."
                rows={4}
              />
            </div>

            <div className="form-group checkbox">
              <label>
                <input
                  type="checkbox"
                  checked={requireReannotation}
                  onChange={(e) => setRequireReannotation(e.target.checked)}
                />
                Require re-annotation (reset task assignments)
              </label>
            </div>

            <div className="modal-actions">
              <Button
                variant="neutral"
                onClick={() => setShowRejectModal(false)}
                disabled={actionLoading}
              >
                Cancel
              </Button>
              <Button
                variant="negative"
                onClick={handleReject}
                disabled={actionLoading || !rejectionReason}
              >
                {actionLoading ? "Processing..." : "Confirm Rejection"}
              </Button>
            </div>
          </div>
        </div>
      )}

      <Footer />
    </div>
  );
};

