import { useCallback, useRef, useState, useEffect } from "react";
import { useHistory } from "react-router";
import { Button, Spinner } from "@synapse/ui";
import { Modal } from "../../../components/Modal/Modal";
import { Space } from "../../../components/Space/Space";
import { useAPI } from "../../../providers/ApiProvider";
import { ProjectProvider, useProject } from "../../../providers/ProjectProvider";
import { useFixedLocation } from "../../../providers/RoutesProvider";
import { cn } from "../../../utils/bem";
import { useRefresh } from "../../../utils/hooks";
import { ImportPage } from "./Import";
import { useImportPage } from "./useImportPage";

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

// Icons matching SecurityDeposit style
const CreditIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <circle cx="12" cy="12" r="10" />
    <path d="M12 6v12M8 10h8M8 14h8" />
  </svg>
);

const TagIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M20.59 13.41l-7.17 7.17a2 2 0 01-2.83 0L2 12V2h10l8.59 8.59a2 2 0 010 2.82z" />
    <line x1="7" y1="7" x2="7.01" y2="7" />
  </svg>
);

const TaskIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M9 11l3 3L22 4" />
    <path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11" />
  </svg>
);

// Import Cost Confirmation Modal - styled like SecurityDeposit
const ImportCostModal = ({ 
  show, 
  onConfirm, 
  onCancel, 
  costInfo, 
  loading,
  error 
}) => {
  if (!show) return null;

  const hasAdditionalBaseFee = costInfo?.additional_base_fee > 0;

  return (
    <div style={{
      position: "fixed",
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      background: "rgba(0, 0, 0, 0.85)",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      zIndex: 10000,
    }}>
      <div style={{
        background: "#0a0a0a",
        border: "1px solid #1f2937",
        borderRadius: "8px",
        padding: "32px",
        maxWidth: "520px",
        width: "90%",
        position: "relative",
      }}>
        {/* Corner accents like SecurityDeposit */}
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
          <span style={{ color: '#6b7280' }}>// </span>Import Cost
        </h3>

        {loading ? (
          <div style={{ display: "flex", alignItems: "center", gap: "16px", padding: "48px 24px", justifyContent: "center" }}>
            <Spinner size={24} />
            <span style={{
              color: '#6b7280',
              fontSize: '12px',
              textTransform: 'uppercase',
              letterSpacing: '0.1em',
              fontFamily: 'ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace'
            }}>
              Calculating import cost...
            </span>
          </div>
        ) : error ? (
          <div style={{
            background: "rgba(239, 68, 68, 0.1)",
            border: "1px solid rgba(239, 68, 68, 0.3)",
            borderRadius: "6px",
            padding: "16px",
            color: "#fca5a5",
            marginBottom: "24px",
            fontSize: "13px",
          }}>
            {error}
          </div>
        ) : costInfo ? (
          <>
            {/* New Tasks Row */}
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              padding: '20px 0',
              borderBottom: '1px solid #1f2937'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <div style={{ color: '#8b5cf6' }}>
                  <TaskIcon />
                </div>
                <span style={{ color: '#e8e4d9', fontSize: '13px' }}>New Tasks</span>
              </div>
              <span style={{
                fontWeight: 600,
                color: '#8b5cf6',
                fontFamily: 'ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace',
                fontSize: '18px'
              }}>
                {costInfo.breakdown?.new_task_count || 0}
              </span>
            </div>

            {/* Annotation Cost Row */}
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              padding: '20px 0',
              borderBottom: '1px solid #1f2937'
            }}>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <div style={{ color: '#8b5cf6' }}>
                    <TagIcon />
                  </div>
                  <span style={{ color: '#e8e4d9', fontSize: '13px' }}>Annotation Cost</span>
                </div>
                <span style={{
                  color: '#6b7280',
                  fontSize: '11px',
                  letterSpacing: '0.02em',
                  marginLeft: '26px'
                }}>
                  {costInfo.breakdown?.new_task_count || 0} tasks × {costInfo.breakdown?.annotation_rate?.toFixed(1) || 10} rate × {costInfo.breakdown?.complexity_multiplier?.toFixed(1) || 1}x × {costInfo.breakdown?.buffer_multiplier || 1.2} buffer
                </span>
              </div>
              <span style={{
                fontWeight: 600,
                color: '#e8e4d9',
                fontFamily: 'ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace',
                fontSize: '13px'
              }}>
                {Math.round(costInfo.annotation_cost || 0)} credits
              </span>
            </div>

            {/* Additional Base Fee Row - only show if > 0 */}
            {hasAdditionalBaseFee && (
              <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                padding: '20px 0',
                borderBottom: '1px solid #1f2937'
              }}>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <div style={{ color: '#f59e0b' }}>
                      <CreditIcon />
                    </div>
                    <span style={{ color: '#e8e4d9', fontSize: '13px' }}>
                      Additional Base Fee
                      <span style={{
                        marginLeft: '8px',
                        padding: '2px 6px',
                        background: 'rgba(245, 158, 11, 0.2)',
                        border: '1px solid rgba(245, 158, 11, 0.3)',
                        borderRadius: '4px',
                        fontSize: '10px',
                        color: '#f59e0b',
                        fontWeight: 500,
                      }}>
                        TIER UPGRADE
                      </span>
                    </span>
                  </div>
                  <span style={{
                    color: '#6b7280',
                    fontSize: '11px',
                    letterSpacing: '0.02em',
                    marginLeft: '26px'
                  }}>
                    Base fee increased from ₹{Math.round(costInfo.breakdown?.original_base_fee || 500)} to ₹{Math.round(costInfo.breakdown?.new_base_fee || 500)}
                  </span>
                </div>
                <span style={{
                  fontWeight: 600,
                  color: '#f59e0b',
                  fontFamily: 'ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace',
                  fontSize: '13px'
                }}>
                  {Math.round(costInfo.additional_base_fee)} credits
                </span>
              </div>
            )}

            {/* Total Cost Row */}
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              padding: '24px 0',
              background: 'rgba(139, 92, 246, 0.05)',
              margin: '0 -32px',
              paddingLeft: '32px',
              paddingRight: '32px',
            }}>
              <span style={{
                color: '#ffffff',
                fontSize: '14px',
                fontWeight: 600,
                letterSpacing: '0.05em'
              }}>
                TOTAL IMPORT COST
              </span>
              <span style={{
                fontWeight: 700,
                color: '#8b5cf6',
                fontFamily: 'ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace',
                fontSize: '20px'
              }}>
                {Math.round(costInfo.total_cost || 0)} credits
              </span>
            </div>

            {/* Available Credits */}
            <div style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              marginTop: "20px",
              padding: "16px 20px",
              background: costInfo.has_sufficient_credits ? "rgba(16, 185, 129, 0.08)" : "rgba(239, 68, 68, 0.08)",
              border: `1px solid ${costInfo.has_sufficient_credits ? "rgba(16, 185, 129, 0.25)" : "rgba(239, 68, 68, 0.25)"}`,
              borderRadius: "6px",
            }}>
              <span style={{ color: '#9ca3af', fontSize: '13px' }}>Available Credits</span>
              <span style={{ 
                color: costInfo.has_sufficient_credits ? "#10b981" : "#ef4444", 
                fontWeight: 600,
                fontFamily: 'ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace',
                fontSize: '14px'
              }}>
                {Math.round(costInfo.available_credits || 0)} credits
              </span>
            </div>

            {!costInfo.has_sufficient_credits && (
              <div style={{
                background: "rgba(239, 68, 68, 0.1)",
                border: "1px solid rgba(239, 68, 68, 0.3)",
                borderRadius: "6px",
                padding: "16px",
                color: "#fca5a5",
                marginTop: "16px",
                fontSize: "12px",
                display: "flex",
                alignItems: "center",
                gap: "8px",
              }}>
                <span>⚠</span>
                <span>Insufficient credits. Please add {Math.round((costInfo.total_cost || 0) - (costInfo.available_credits || 0))} more credits to proceed.</span>
              </div>
            )}
          </>
        ) : null}

        {/* Action Buttons */}
        <div style={{ display: "flex", gap: "12px", justifyContent: "flex-end", marginTop: "24px" }}>
          <button
            onClick={onCancel}
            style={{
              ...dangerButtonStyle,
              padding: "0 20px",
              height: "40px",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = "rgba(239, 68, 68, 0.2)";
              e.currentTarget.style.borderColor = "rgba(239, 68, 68, 0.5)";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = "rgba(239, 68, 68, 0.12)";
              e.currentTarget.style.borderColor = "rgba(239, 68, 68, 0.3)";
            }}
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            disabled={loading || !costInfo?.has_sufficient_credits}
            style={{
              ...primaryButtonStyle,
              opacity: (loading || !costInfo?.has_sufficient_credits) ? 0.5 : 1,
              cursor: (loading || !costInfo?.has_sufficient_credits) ? "not-allowed" : "pointer",
            }}
            onMouseEnter={(e) => {
              if (!loading && costInfo?.has_sufficient_credits) {
                e.currentTarget.style.background = "#7c3aed";
                e.currentTarget.style.borderColor = "#7c3aed";
                e.currentTarget.style.transform = "translateY(-1px)";
                e.currentTarget.style.boxShadow = "0 4px 12px rgba(139, 92, 246, 0.4)";
              }
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = "#8b5cf6";
              e.currentTarget.style.borderColor = "#8b5cf6";
              e.currentTarget.style.transform = "translateY(0)";
              e.currentTarget.style.boxShadow = "none";
            }}
          >
            {loading ? (
              <>
                <Spinner size="small" />
                Processing...
              </>
            ) : (
              "Confirm & Import"
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export const Inner = () => {
  const history = useHistory();
  const location = useFixedLocation();
  const modal = useRef();
  const refresh = useRefresh();
  const { project } = useProject();
  const [waiting, setWaitingStatus] = useState(false);
  const [sample, setSample] = useState(null);
  const [showCostModal, setShowCostModal] = useState(false);
  const [costInfo, setCostInfo] = useState(null);
  const [costLoading, setCostLoading] = useState(false);
  const [costError, setCostError] = useState(null);
  const [estimatedTaskCount, setEstimatedTaskCount] = useState(0);
  const api = useAPI();

  const { uploading, uploadDisabled, finishUpload, fileIds, pageProps, uploadSample } = useImportPage(project);

  const backToDM = useCallback(() => {
    const path = location.pathname.replace(ImportModal.path, "");
    const search = location.search;
    const pathname = `${path}${search !== "?" ? search : ""}`;

    // Use history.push directly to avoid landing page flash
    history.push(pathname);
  }, [location, history]);

  const onCancel = useCallback(async () => {
    setWaitingStatus(true);
    await api.callApi("deleteFileUploads", {
      params: {
        pk: project.id,
      },
      body: {
        file_upload_ids: fileIds,
      },
    });
    setWaitingStatus(false);
    modal?.current?.hide();
    backToDM();
  }, [modal, project, fileIds, backToDM]);

  // Calculate import cost
  const calculateImportCost = useCallback(async (taskCount) => {
    setCostLoading(true);
    setCostError(null);
    
    try {
      const response = await api.callApi("calculateImportCost", {
        body: {
          project_id: project.id,
          new_task_count: taskCount,
          file_upload_ids: fileIds,
        },
      });

      if (response?.success) {
        setCostInfo(response);
      } else {
        setCostError(response?.error || "Failed to calculate import cost");
      }
    } catch (err) {
      console.error("Error calculating import cost:", err);
      setCostError(err.message || "Error calculating import cost");
    } finally {
      setCostLoading(false);
    }
  }, [api, project?.id, fileIds]);

  // Handle import button click - show cost confirmation
  const onImportClick = useCallback(async () => {
    // Use estimated task count from file uploads
    const taskCount = estimatedTaskCount || fileIds?.length || 0;
    
    if (taskCount <= 0) {
      // No tasks, just finish upload
      const imported = await finishUpload();
      if (imported) backToDM();
      return;
    }

    // Show cost modal and calculate cost
    setShowCostModal(true);
    await calculateImportCost(taskCount);
  }, [estimatedTaskCount, fileIds, finishUpload, backToDM, calculateImportCost]);

  // Confirm import and charge
  const onConfirmImport = useCallback(async () => {
    setWaitingStatus(true);
    setCostError(null);

    try {
      // Charge import cost
      const chargeResponse = await api.callApi("chargeImportCost", {
        body: {
          project_id: project.id,
          new_task_count: estimatedTaskCount || fileIds?.length || 0,
        },
      });

      if (!chargeResponse?.success) {
        setCostError(chargeResponse?.error || "Failed to charge import cost");
        setWaitingStatus(false);
        return;
      }

      // Upload sample if selected
      if (sample) {
        await uploadSample(
          sample,
          () => {},
          () => {},
        );
      }

      // Finish the import
      const imported = await finishUpload();

      if (!imported) {
        setCostError("Import failed after payment. Please contact support.");
        setWaitingStatus(false);
        return;
      }

      setShowCostModal(false);
      backToDM();
    } catch (err) {
      console.error("Error during import:", err);
      setCostError(err.message || "Error during import");
    } finally {
      setWaitingStatus(false);
    }
  }, [api, project?.id, estimatedTaskCount, fileIds, sample, uploadSample, finishUpload, backToDM]);

  // Handle file list updates to track estimated task count
  const handleFileListUpdate = useCallback((ids, taskCount) => {
    pageProps.onFileListUpdate(ids);
    if (taskCount !== undefined) {
      setEstimatedTaskCount(taskCount);
    } else {
      setEstimatedTaskCount(ids?.length || 0);
    }
  }, [pageProps]);

  return (
    <>
      <Modal
        title="Import data"
        ref={modal}
        onHide={() => backToDM()}
        closeOnClickOutside={false}
        fullscreen
        visible
        bare
      >
        <Modal.Header divided>
          <div className={cn("modal").elem("title").toClassName()}>Import Data</div>

          <Space>
            <button
              size="small"
              variant="negative"
              look="outlined"
              waiting={waiting}
              onClick={onCancel}
              aria-label="Cancel import"
              style={dangerButtonStyle}
            >
              Cancel
            </button>
            <button
              size="small"
              onClick={onImportClick}
              waiting={waiting || uploading}
              disabled={uploadDisabled || fileIds?.length === 0}
              aria-label="Finish import"
              style={{
                ...primaryButtonStyle,
                opacity: (uploadDisabled || fileIds?.length === 0) ? 0.5 : 1,
                cursor: (uploadDisabled || fileIds?.length === 0) ? "not-allowed" : "pointer",
              }}
            >
              Import
            </button>
          </Space>
        </Modal.Header>
        <ImportPage
          project={project}
          sample={sample}
          onSampleDatasetSelect={setSample}
          projectConfigured={Object.keys(project.parsed_label_config ?? {}).length > 0}
          openLabelingConfig={() => {
            history.push(`/projects/${project.id}/settings/labeling`);
          }}
          {...pageProps}
          onFileListUpdate={handleFileListUpdate}
          onEstimatedTasksUpdate={setEstimatedTaskCount}
        />
      </Modal>

      <ImportCostModal
        show={showCostModal}
        costInfo={costInfo}
        loading={costLoading || waiting}
        error={costError}
        onConfirm={onConfirmImport}
        onCancel={() => {
          setShowCostModal(false);
          setCostInfo(null);
          setCostError(null);
        }}
      />
    </>
  );
};

export const ImportModal = () => {
  return (
    <ProjectProvider>
      <Inner />
    </ProjectProvider>
  );
};

ImportModal.path = "/import";
ImportModal.modal = true;

