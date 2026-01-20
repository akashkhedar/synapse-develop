import React, { useState, useEffect, useCallback } from "react";
import { useHistory } from "react-router";
import { Button, Typography, Spinner } from "@synapse/ui";
import { useAPI } from "../../../providers/ApiProvider";
import { Modal } from "../../../components/Modal/Modal";
import "./SecurityDeposit.scss";

// SVG Icons
const WarningIcon = () => (
  <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
    <path d="M12 9v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" strokeLinecap="round" strokeLinejoin="round"/>
  </svg>
);

const CheckIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M5 13l4 4L19 7" strokeLinecap="round" strokeLinejoin="round"/>
  </svg>
);

const ClockIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <circle cx="12" cy="12" r="10"/>
    <path d="M12 6v6l4 2" strokeLinecap="round" strokeLinejoin="round"/>
  </svg>
);

const FolderIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" strokeLinecap="round" strokeLinejoin="round"/>
  </svg>
);

const SmallWarningIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M12 9v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" strokeLinecap="round" strokeLinejoin="round"/>
  </svg>
);

const CreditIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <circle cx="12" cy="12" r="8"/>
    <path d="M12 6v12M6 12h12" strokeLinecap="round" strokeLinejoin="round"/>
  </svg>
);

const ShieldIcon = () => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" strokeLinecap="round" strokeLinejoin="round"/>
  </svg>
);

const DatabaseIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <ellipse cx="12" cy="5" rx="9" ry="3"/>
    <path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/>
    <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/>
  </svg>
);

const TagIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M20.59 13.41l-7.17 7.17a2 2 0 01-2.83 0L2 12V2h10l8.59 8.59a2 2 0 010 2.82z"/>
    <line x1="7" y1="7" x2="7.01" y2="7" strokeLinecap="round" strokeLinejoin="round"/>
  </svg>
);

const InfoIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <circle cx="12" cy="12" r="10"/>
    <path d="M12 16v-4M12 8h.01" strokeLinecap="round" strokeLinejoin="round"/>
  </svg>
);

const primaryButtonStyle = {
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  gap: "6px",
  padding: "0 16px",
  height: "40px",
  minWidth: "90px",
  background: "#8b5cf6",
  border: "1px solid #8b5cf6",
  color: "#ffffff",
  fontSize: "13px",
  fontWeight: 600,
  fontFamily: "'Space Grotesk', system-ui, sans-serif",
  cursor: "pointer",
  transition: "all 0.2s ease",
};

const dangerButtonStyle = {
  ...primaryButtonStyle,
  background: "rgba(239, 68, 68, 0.12)",
  border: "1px solid rgba(239, 68, 68, 0.3)",
  color: "#fca5a5",
};

const successButtonStyle = {
  ...primaryButtonStyle,
  background: "#10b981",
  borderColor: "#10b981",
  color: "#ffffff",
};

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
    <div className="security-deposit p-2">
      {/* Insufficient Credits Modal */}
      {showInsufficientModal && (
        <Modal
          onHide={() => setShowInsufficientModal(false)}
          title="Insufficient Credits"
          visible={showInsufficientModal}
        >
          <div className="security-deposit__modal">
            <div className="security-deposit__modal-icon" style={{ color: '#f59e0b' }}>
              <WarningIcon />
            </div>
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
              <button
                style={primaryButtonStyle}
                onMouseEnter={(e) => e.currentTarget.style.background = "#7c3aed"}
                onMouseLeave={(e) => e.currentTarget.style.background = "#8b5cf6"}
                onClick={goToBillingPage}
              >
                Purchase Credits
              </button>
              <button
                style={dangerButtonStyle}
                onMouseEnter={(e) => {
                  e.currentTarget.style.background = "rgba(239, 68, 68, 0.2)";
                  e.currentTarget.style.borderColor = "rgba(239, 68, 68, 0.5)";
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.background = "rgba(239, 68, 68, 0.12)";
                  e.currentTarget.style.borderColor = "rgba(239, 68, 68, 0.3)";
                }}
                onClick={() => setShowInsufficientModal(false)}
              >
                Cancel
              </button>
            </div>
          </div>
        </Modal>
      )}

      <div className="security-deposit__header p-2">
        <p className="security-deposit__subtitle" style={{
          color: '#6b7280',
          lineHeight: 1.7,
          fontSize: '14px',
          letterSpacing: '0.02em',
          letterSpacing: '0.02em',
          margin: '12px 0 24px 0'
        }}>
          A refundable security deposit is required to publish your project.
          This helps ensure project quality and prevents abandoned projects.
        </p>
      </div>

      {calculating ? (
        <div className="security-deposit__loading" style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '16px',
          padding: '64px 24px'
        }}>
          <Spinner size={24} />
          <span style={{
            color: '#6b7280',
            fontSize: '12px',
            textTransform: 'uppercase',
            letterSpacing: '0.1em',
            fontFamily: 'ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace'
          }}>
            Calculating deposit amount...
          </span>
        </div>
      ) : depositInfo ? (
        <>
          <div className="security-deposit__breakdown" style={{
            background: 'transparent',
            border: '1px solid #1f2937',
            borderRadius: '8px',
            borderRadius: '8px',
            padding: '32px',
            display: 'flex',
            flexDirection: 'column',
            gap: 0,
            position: 'relative'
          }}>
            <div style={{
              position: 'absolute',
              top: '-1px',
              left: '-1px',
              width: '20px',
              height: '20px',
              borderTop: '2px solid #8b5cf6',
              borderLeft: '2px solid #8b5cf6'
            }} />
            <div style={{
              position: 'absolute',
              bottom: '-1px',
              right: '-1px',
              width: '20px',
              height: '20px',
              borderBottom: '2px solid #8b5cf6',
              borderRight: '2px solid #8b5cf6'
            }} />

            <h3 style={{
              marginBottom: '20px',
              color: '#ffffff',
              fontSize: '12px',
              fontWeight: 500,
              textTransform: 'uppercase',
              letterSpacing: '0.1em',
              fontFamily: 'ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace'
            }}>
              <span style={{ color: '#6b7280' }}>// </span>Deposit Breakdown
            </h3>

            <div className="security-deposit__row" style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              padding: '24px 0',
              borderBottom: '1px solid #1f2937'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <div style={{ color: '#8b5cf6' }}>
                  <CreditIcon />
                </div>
                <span style={{ color: '#e8e4d9', fontSize: '13px' }}>Base Fee</span>
              </div>
              <span style={{
                fontWeight: 600,
                color: '#e8e4d9',
                fontFamily: 'ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace',
                fontSize: '13px'
              }}>
                {Math.round(depositInfo.breakdown?.base_fee || 500)} credits
              </span>
            </div>

            <div className="security-deposit__row" style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              padding: '24px 0',
              borderBottom: '1px solid #1f2937'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <div style={{ color: '#8b5cf6' }}>
                  <DatabaseIcon />
                </div>
                <span style={{ color: '#e8e4d9', fontSize: '13px' }}>
                  Storage Fee ({depositInfo.breakdown?.estimated_storage_gb?.toFixed(1) || 0} GB)
                </span>
              </div>
              <span style={{
                fontWeight: 600,
                color: '#e8e4d9',
                fontFamily: 'ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace',
                fontSize: '13px'
              }}>
                {Math.round(depositInfo.breakdown?.storage_fee || 0)} credits
              </span>
            </div>

            <div className="security-deposit__row" style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              padding: '24px 0',
              borderBottom: '1px solid #1f2937'
            }}>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <div style={{ color: '#8b5cf6' }}>
                    <TagIcon />
                  </div>
                  <span style={{ color: '#e8e4d9', fontSize: '13px' }}>Annotation Estimate</span>
                </div>
                <span style={{
                  color: '#6b7280',
                  fontSize: '11px',
                  letterSpacing: '0.02em',
                  marginLeft: '24px'
                }}>
                  {depositInfo.breakdown?.estimated_tasks || 0} tasks × {depositInfo.breakdown?.annotation_rate?.toFixed(1) || 5} rate × {depositInfo.breakdown?.complexity_multiplier || 1}x complexity × 1.5 buffer
                </span>
              </div>
              <span style={{
                fontWeight: 600,
                color: '#e8e4d9',
                fontFamily: 'ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace',
                fontSize: '13px'
              }}>
                {Math.round(depositInfo.breakdown?.annotation_fee || 0)} credits
              </span>
            </div>

            {depositInfo.breakdown?.duration_pricing && (
              <div style={{
                background: 'rgba(139, 92, 246, 0.05)',
                margin: '8px -20px',
                padding: '12px 20px',
                borderRadius: '4px',
                borderLeft: '2px solid rgba(139, 92, 246, 0.3)',
                display: 'flex',
                alignItems: 'center',
                gap: '8px'
              }}>
                <div style={{ color: '#8b5cf6' }}>
                  <ClockIcon />
                </div>
                <span style={{
                  color: '#9ca3af',
                  fontSize: '11px',
                  fontStyle: 'normal'
                }}>
                  Duration-based pricing: ~
                  {depositInfo.breakdown.duration_pricing.avg_duration_mins?.toFixed(1)}{" "}
                  mins/task @ {depositInfo.breakdown.duration_pricing.base_rate_per_min}{" "}
                  credits/min
                </span>
              </div>
            )}

            {depositInfo.breakdown?.data_types?.length > 0 && (
              <div style={{
                background: 'rgba(139, 92, 246, 0.05)',
                margin: '8px -20px',
                padding: '12px 20px',
                borderRadius: '4px',
                borderLeft: '2px solid rgba(139, 92, 246, 0.3)',
                display: 'flex',
                alignItems: 'center',
                gap: '8px'
              }}>
                <div style={{ color: '#8b5cf6' }}>
                  <FolderIcon />
                </div>
                <span style={{
                  color: '#9ca3af',
                  fontSize: '11px',
                  fontStyle: 'normal'
                }}>
                  Data types: {depositInfo.breakdown.data_types.join(", ")}
                </span>
              </div>
            )}

            {depositInfo.breakdown?.total_labels > 0 && (
              <div style={{
                background: 'rgba(139, 92, 246, 0.05)',
                margin: '8px -20px',
                padding: '12px 20px',
                borderRadius: '4px',
                borderLeft: '2px solid rgba(139, 92, 246, 0.3)',
                display: 'flex',
                alignItems: 'center',
                gap: '8px'
              }}>
                <div style={{ color: '#8b5cf6' }}>
                  <InfoIcon />
                </div>
                <span style={{
                  color: '#9ca3af',
                  fontSize: '11px',
                  fontStyle: 'normal'
                }}>
                  Detected: {depositInfo.breakdown?.annotation_types?.join(", ") || "default"}
                  {depositInfo.breakdown?.total_labels > 0 && ` • ${depositInfo.breakdown?.total_labels} labels`}
                  {depositInfo.breakdown?.complexity_multiplier > 1 && ` • ${depositInfo.breakdown?.complexity_multiplier}x complexity`}
                </span>
              </div>
            )}

            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              padding: '32px 0 8px',
              marginTop: '16px',
              borderTop: '1px solid #374151'
            }}>
              <span style={{
                color: '#ffffff',
                fontSize: '14px',
                fontWeight: 500,
                textTransform: 'uppercase',
                letterSpacing: '0.1em',
                fontFamily: 'ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace'
              }}>
                Total Deposit
              </span>
              <span style={{
                fontWeight: 600,
                color: '#8b5cf6',
                fontSize: '18px',
                fontFamily: 'ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace'
              }}>
                {Math.round(depositInfo.total_deposit || 500)} credits
              </span>
            </div>

            {/* Show current balance */}
            {userBalance !== null && (
              <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                background: 'rgba(31, 41, 55, 0.5)',
                margin: '16px -20px -20px',
                padding: '16px 20px',
                borderRadius: '0 0 6px 6px',
                borderTop: '1px solid #374151'
              }}>
                <span style={{ color: '#9ca3af', fontSize: '13px' }}>
                  Your Balance
                </span>
                <span style={{
                  fontWeight: 600,
                  color: hasInsufficientCredits ? '#ef4444' : '#10b981',
                  fontFamily: 'ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace',
                  fontSize: '13px'
                }}>
                  {userBalance} credits
                </span>
              </div>
            )}
          </div>

          {/* Insufficient credits warning */}
          {hasInsufficientCredits && (
            <div style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              gap: '20px',
              padding: '20px',
              background: 'rgba(245, 158, 11, 0.1)',
              border: '1px solid rgba(245, 158, 11, 0.3)',
              borderRadius: '6px',
              color: '#f59e0b',
              fontSize: '13px',
              marginTop: "1em",
              marginBottom:"1em"
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <SmallWarningIcon />
                <span>You need {creditsNeeded} more credits to pay this deposit.</span>
              </div>
              <button
                style={{
                  ...primaryButtonStyle,
                  height: "32px",
                  fontSize: "11px",
                  whiteSpace: "nowrap",
                }}
                onMouseEnter={(e) =>
                  (e.currentTarget.style.background = "#7c3aed")
                }
                onMouseLeave={(e) =>
                  (e.currentTarget.style.background = "#8b5cf6")
                }
                onClick={goToBillingPage}
              >
                Purchase Credits
              </button>
            </div>
          )}

          <div style={{
            background: 'rgba(139, 92, 246, 0.05)',
            border: '1px solid rgba(139, 92, 246, 0.2)',
            borderRadius: '6px',
            padding: '20px',
            color: '#9ca3af',
            lineHeight: 1.7,
            fontSize: '12px',
            marginTop: '24px'
          }}>
            <div style={{ display: 'flex', alignItems: 'flex-start', gap: '8px', marginBottom: '8px' }}>
              <div style={{ color: '#8b5cf6', marginTop: '2px' }}>
                <InfoIcon />
              </div>
              <span>Deposit is refundable upon project completion and data export</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'flex-start', gap: '8px', marginBottom: '8px' }}>
              <div style={{ color: '#8b5cf6', marginTop: '2px' }}>
                <InfoIcon />
              </div>
              <span>Unused credits will be returned when project is closed</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'flex-start', gap: '8px' }}>
              <div style={{ color: '#8b5cf6', marginTop: '2px' }}>
                <InfoIcon />
              </div>
              <span>If project is abandoned (no activity for 30 days), deposit may be forfeited</span>
            </div>
          </div>

          {depositPaid ? (
            <div style={{
              padding: '20px 24px',
              background: 'rgba(16, 185, 129, 0.1)',
              border: '1px solid rgba(16, 185, 129, 0.3)',
              borderRadius: '6px',
              color: '#10b981',
              fontWeight: 500,
              fontSize: '13px',
              display: 'flex',
              alignItems: 'center',
              gap: '12px'
            }}>
              <CheckIcon />
              <span>Security deposit collected successfully</span>
            </div>
          ) : (
            <div className="security-deposit__action" style={{ marginTop: '32px', display: 'flex', flexDirection: 'column', alignItems: 'flex-end' }}>
              <button
                style={
                  loading || !depositInfo
                    ? {
                        ...primaryButtonStyle,
                        opacity: 0.6,
                        cursor: "not-allowed",
                        background: "#4b5563",
                        borderColor: "#4b5563",
                      }
                    : primaryButtonStyle
                }
                onMouseEnter={(e) => {
                  if (!(loading || !depositInfo))
                    e.currentTarget.style.background = "#7c3aed";
                }}
                onMouseLeave={(e) => {
                  if (!(loading || !depositInfo))
                    e.currentTarget.style.background = "#8b5cf6";
                }}
                onClick={
                  hasInsufficientCredits ? goToBillingPage : collectDeposit
                }
                disabled={loading || !depositInfo}
              >
                {hasInsufficientCredits
                  ? "Purchase Credits"
                  : `Pay ${Math.round(
                      depositInfo.total_deposit || 500
                    )} Credits`}
              </button>

              {error && (
                <div style={{
                  padding: '16px 20px',
                  background: 'rgba(239, 68, 68, 0.1)',
                  border: '1px solid rgba(239, 68, 68, 0.3)',
                  borderRadius: '6px',
                  color: '#ef4444',
                  fontSize: '12px',
                  marginTop: '12px'
                }}>
                  {error}
                </div>
              )}
            </div>
          )}
        </>
      ) : error ? (
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          gap: '20px',
          alignItems: 'center',
          padding: '48px 32px',
          background: 'rgba(239, 68, 68, 0.05)',
          border: '1px solid rgba(239, 68, 68, 0.2)',
          borderRadius: '8px',
          textAlign: 'center'
        }}>
          <span style={{ color: '#ef4444', fontSize: '14px' }}>{error}</span>
          <button
            style={primaryButtonStyle}
            onMouseEnter={(e) =>
              (e.currentTarget.style.background = "#7c3aed")
            }
            onMouseLeave={(e) =>
              (e.currentTarget.style.background = "#8b5cf6")
            }
            onClick={calculateDeposit}
          >
            Retry
          </button>
        </div>
      ) : null}
    </div>
  );
};

export default SecurityDeposit;

