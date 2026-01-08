import React, { useState, useEffect, useCallback } from "react";
import { useHistory } from "react-router";
import { Button, Typography, Spinner } from "@synapse/ui";
import { useAPI } from "../../../providers/ApiProvider";
import { Modal } from "../../../components/Modal/Modal";
import "./SecurityDeposit.scss";

/**
 * SecurityDeposit component for collecting security deposit during project creation.
 *
 * Shows the calculated deposit amount and allows user to confirm payment from credits.
 */
export const SecurityDeposit = ({
  project,
  estimatedTasks = 0,
  estimatedStorageGB = 0,
  onDepositCollected,
  onError,
  show = true,
}) => {
  const api = useAPI();
  const history = useHistory();
  const [loading, setLoading] = useState(false);
  const [calculating, setCalculating] = useState(false);
  const [depositInfo, setDepositInfo] = useState(null);
  const [error, setError] = useState(null);
  const [depositPaid, setDepositPaid] = useState(false);
  const [userBalance, setUserBalance] = useState(null);
  const [showInsufficientModal, setShowInsufficientModal] = useState(false);

  // Fetch user's credit balance
  const fetchUserBalance = useCallback(async () => {
    try {
      const response = await fetch("/api/billing/billing/dashboard/", {
        credentials: "include",
        headers: { "Content-Type": "application/json" },
      });
      if (response.ok) {
        const data = await response.json();
        setUserBalance(data.billing?.available_credits || 0);
      }
    } catch (err) {
      console.error("Error fetching balance:", err);
    }
  }, []);

  useEffect(() => {
    if (show) {
      fetchUserBalance();
    }
  }, [show, fetchUserBalance]);

  // Calculate deposit when project or estimates change
  const calculateDeposit = useCallback(async () => {
    if (!project?.id) return;

    setCalculating(true);
    setError(null);

    try {
      const response = await api.callApi("calculateSecurityDeposit", {
        body: {
          project_id: project.id,
          label_config: project.label_config,
          estimated_tasks: estimatedTasks || project.task_number || 1,
          estimated_storage_gb: estimatedStorageGB,
        },
      });

      if (response?.success) {
        setDepositInfo(response);
      } else {
        setError(response?.error || "Failed to calculate deposit");
      }
    } catch (err) {
      console.error("Error calculating deposit:", err);
      setError(err.message || "Error calculating deposit");
    } finally {
      setCalculating(false);
    }
  }, [
    api,
    project?.id,
    project?.label_config,
    estimatedTasks,
    estimatedStorageGB,
  ]);

  useEffect(() => {
    if (project?.id && show) {
      calculateDeposit();
    }
  }, [project?.id, show, calculateDeposit]);

  // Collect deposit
  const collectDeposit = async () => {
    if (!project?.id) return;

    // Check if user has enough credits
    const requiredCredits = Math.round(depositInfo?.total_deposit || 500);
    if (userBalance !== null && userBalance < requiredCredits) {
      setShowInsufficientModal(true);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await api.callApi("collectSecurityDeposit", {
        body: {
          project_id: project.id,
          // Pass the calculated deposit amount to ensure consistency
          deposit_amount: depositInfo?.total_deposit || null,
          estimated_tasks: estimatedTasks || project.task_number || 1,
          estimated_storage_gb:
            estimatedStorageGB || depositInfo?.breakdown?.storage_gb || 0,
        },
      });

      if (response?.success) {
        setDepositPaid(true);
        onDepositCollected?.(response);
      } else {
        const errorMsg = response?.error || "Failed to collect deposit";
        // Check if it's an insufficient credits error
        if (
          errorMsg.toLowerCase().includes("insufficient") ||
          errorMsg.toLowerCase().includes("not enough")
        ) {
          setShowInsufficientModal(true);
        } else {
          setError(errorMsg);
          onError?.(errorMsg);
        }
      }
    } catch (err) {
      console.error("Error collecting deposit:", err);
      const errorMsg = err.message || "Error collecting deposit";
      // Check if it's an insufficient credits error
      if (
        errorMsg.toLowerCase().includes("insufficient") ||
        errorMsg.toLowerCase().includes("not enough")
      ) {
        setShowInsufficientModal(true);
      } else {
        setError(errorMsg);
        onError?.(errorMsg);
      }
    } finally {
      setLoading(false);
    }
  };

  // Navigate to billing page
  const goToBillingPage = () => {
    setShowInsufficientModal(false);
    history.push("/billing");
  };

  // Calculate how many more credits are needed
  const creditsNeeded =
    depositInfo && userBalance !== null
      ? Math.max(0, Math.round(depositInfo.total_deposit) - userBalance)
      : 0;

  // Check if user has sufficient credits
  const hasInsufficientCredits =
    userBalance !== null &&
    depositInfo &&
    userBalance < Math.round(depositInfo.total_deposit);

  if (!show) return null;

  return (
    <div className="security-deposit">
      {/* Insufficient Credits Modal */}
      {showInsufficientModal && (
        <Modal
          onHide={() => setShowInsufficientModal(false)}
          title="Insufficient Credits"
          visible={showInsufficientModal}
        >
          <div className="security-deposit__modal">
            <div className="security-deposit__modal-icon">⚠️</div>
            <Typography variant="body" size="medium">
              You don't have enough credits to pay the security deposit.
            </Typography>
            <div className="security-deposit__modal-details">
              <div className="security-deposit__modal-row">
                <span>Required:</span>
                <strong>
                  {Math.round(depositInfo?.total_deposit || 0)} credits
                </strong>
              </div>
              <div className="security-deposit__modal-row">
                <span>Your balance:</span>
                <strong>{userBalance || 0} credits</strong>
              </div>
              <div className="security-deposit__modal-row security-deposit__modal-row--needed">
                <span>Credits needed:</span>
                <strong>{creditsNeeded} credits</strong>
              </div>
            </div>
            <div className="security-deposit__modal-actions">
              <Button look="primary" size="medium" onClick={goToBillingPage}>
                Purchase Credits
              </Button>
              <Button
                look="outlined"
                size="medium"
                onClick={() => setShowInsufficientModal(false)}
              >
                Cancel
              </Button>
            </div>
          </div>
        </Modal>
      )}

      <div className="security-deposit__header">
        <Typography variant="headline" size="medium">
          Security Deposit
        </Typography>
        <Typography
          variant="body"
          size="small"
          className="security-deposit__subtitle"
        >
          A refundable security deposit is required to publish your project.
          This helps ensure project quality and prevents abandoned projects.
        </Typography>
      </div>

      {calculating ? (
        <div className="security-deposit__loading">
          <Spinner size={24} />
          <Typography
            variant="body"
            size="medium"
            className="security-deposit__loading-text"
          >
            Calculating deposit amount...
          </Typography>
        </div>
      ) : depositInfo ? (
        <>
          <div className="security-deposit__breakdown">
            <Typography
              variant="title"
              size="small"
              className="security-deposit__breakdown-title"
            >
              Deposit Breakdown
            </Typography>

            <div className="security-deposit__row">
              <Typography variant="body" size="small">
                Base Fee
              </Typography>
              <Typography
                variant="body"
                size="small"
                className="security-deposit__amount"
              >
                {Math.round(depositInfo.breakdown?.base_fee || 500)} credits
              </Typography>
            </div>

            <div className="security-deposit__row">
              <Typography variant="body" size="small">
                Storage Fee (
                {depositInfo.breakdown?.estimated_storage_gb?.toFixed(1) || 0}{" "}
                GB)
              </Typography>
              <Typography
                variant="body"
                size="small"
                className="security-deposit__amount"
              >
                {Math.round(depositInfo.breakdown?.storage_fee || 0)} credits
              </Typography>
            </div>

            <div className="security-deposit__row">
              <div className="security-deposit__row-details">
                <Typography variant="body" size="small">
                  Annotation Estimate
                </Typography>
                <Typography
                  variant="body"
                  size="smaller"
                  className="security-deposit__detail-text"
                >
                  {depositInfo.breakdown?.estimated_tasks || 0} tasks ×{" "}
                  {depositInfo.breakdown?.annotation_rate?.toFixed(1) || 5} rate
                  × {depositInfo.breakdown?.complexity_multiplier || 1}x
                  complexity × 1.5 buffer
                </Typography>
              </div>
              <Typography
                variant="body"
                size="small"
                className="security-deposit__amount"
              >
                {Math.round(depositInfo.breakdown?.annotation_fee || 0)} credits
              </Typography>
            </div>

            {depositInfo.breakdown?.duration_pricing && (
              <div className="security-deposit__row security-deposit__row--info">
                <Typography
                  variant="body"
                  size="smaller"
                  className="security-deposit__info-text"
                >
                  ⏱️ Duration-based pricing: ~
                  {depositInfo.breakdown.duration_pricing.avg_duration_mins?.toFixed(
                    1
                  )}{" "}
                  mins/task @{" "}
                  {depositInfo.breakdown.duration_pricing.base_rate_per_min}{" "}
                  credits/min
                </Typography>
              </div>
            )}

            {depositInfo.breakdown?.data_types?.length > 0 && (
              <div className="security-deposit__row security-deposit__row--info">
                <Typography
                  variant="body"
                  size="smaller"
                  className="security-deposit__info-text"
                >
                  📁 Data types: {depositInfo.breakdown.data_types.join(", ")}
                </Typography>
              </div>
            )}

            {depositInfo.breakdown?.total_labels > 0 && (
              <div className="security-deposit__row security-deposit__row--info">
                <Typography
                  variant="body"
                  size="smaller"
                  className="security-deposit__info-text"
                >
                  Detected:{" "}
                  {depositInfo.breakdown?.annotation_types?.join(", ") ||
                    "default"}
                  {depositInfo.breakdown?.total_labels > 0 &&
                    ` • ${depositInfo.breakdown?.total_labels} labels`}
                  {depositInfo.breakdown?.complexity_multiplier > 1 &&
                    ` • ${depositInfo.breakdown?.complexity_multiplier}x complexity`}
                </Typography>
              </div>
            )}

            <div className="security-deposit__row security-deposit__row--total">
              <Typography variant="title" size="small">
                Total Deposit
              </Typography>
              <Typography
                variant="title"
                size="small"
                className="security-deposit__amount security-deposit__amount--total"
              >
                {Math.round(depositInfo.total_deposit || 500)} credits
              </Typography>
            </div>

            {/* Show current balance */}
            {userBalance !== null && (
              <div className="security-deposit__row security-deposit__row--balance">
                <Typography variant="body" size="small">
                  Your Balance
                </Typography>
                <Typography
                  variant="body"
                  size="small"
                  className={`security-deposit__amount ${
                    hasInsufficientCredits
                      ? "security-deposit__amount--insufficient"
                      : "security-deposit__amount--sufficient"
                  }`}
                >
                  {userBalance} credits
                </Typography>
              </div>
            )}
          </div>

          {/* Insufficient credits warning */}
          {hasInsufficientCredits && (
            <div className="security-deposit__warning">
              <Typography variant="body" size="small">
                ⚠️ You need {creditsNeeded} more credits to pay this deposit.
              </Typography>
              <Button look="outlined" size="small" onClick={goToBillingPage}>
                Purchase Credits
              </Button>
            </div>
          )}

          <div className="security-deposit__notes">
            <Typography variant="body" size="smaller">
              • Deposit is refundable upon project completion and data export
              <br />
              • Unused credits will be returned when project is closed
              <br />• If project is abandoned (no activity for 30 days), deposit
              may be forfeited
            </Typography>
          </div>

          {depositPaid ? (
            <div className="security-deposit__success">
              <Typography variant="body" size="medium">
                ✓ Security deposit collected successfully
              </Typography>
            </div>
          ) : (
            <div className="security-deposit__action">
              <Button
                look={hasInsufficientCredits ? "outlined" : "primary"}
                size="medium"
                onClick={
                  hasInsufficientCredits ? goToBillingPage : collectDeposit
                }
                waiting={loading}
                disabled={loading || !depositInfo}
              >
                {hasInsufficientCredits
                  ? "Purchase Credits"
                  : `Pay ${Math.round(
                      depositInfo.total_deposit || 500
                    )} Credits`}
              </Button>

              {error && (
                <div className="security-deposit__error">
                  <Typography variant="body" size="small">
                    {error}
                  </Typography>
                </div>
              )}
            </div>
          )}
        </>
      ) : error ? (
        <div className="security-deposit__error-container">
          <Typography variant="body" size="medium">
            {error}
          </Typography>
          <Button look="outlined" size="medium" onClick={calculateDeposit}>
            Retry
          </Button>
        </div>
      ) : null}
    </div>
  );
};

export default SecurityDeposit;

