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

const secondaryButtonStyle = {
  ...primaryButtonStyle,
  background: "transparent",
  border: "1px solid rgba(139, 92, 246, 0.3)",
  color: "#a78bfa",
};

// Import Cost Confirmation Modal
const ImportCostModal = ({ 
  show, 
  onConfirm, 
  onCancel, 
  costInfo, 
  loading,
  error 
}) => {
  if (!show) return null;

  return (
    <div style={{
      position: "fixed",
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      background: "rgba(0, 0, 0, 0.8)",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      zIndex: 10000,
    }}>
      <div style={{
        background: "#111827",
        border: "1px solid #374151",
        borderRadius: "12px",
        padding: "32px",
        maxWidth: "500px",
        width: "90%",
      }}>
        <h2 style={{
          color: "#f9fafb",
          fontSize: "20px",
          fontWeight: 600,
          marginBottom: "24px",
          fontFamily: "'Space Grotesk', system-ui, sans-serif",
        }}>
          Import Cost Confirmation
        </h2>

        {loading ? (
          <div style={{ display: "flex", alignItems: "center", gap: "12px", padding: "24px 0" }}>
            <Spinner size={24} />
            <span style={{ color: "#9ca3af" }}>Calculating import cost...</span>
          </div>
        ) : error ? (
          <div style={{
            background: "rgba(239, 68, 68, 0.1)",
            border: "1px solid rgba(239, 68, 68, 0.3)",
            borderRadius: "8px",
            padding: "16px",
            color: "#fca5a5",
            marginBottom: "24px",
          }}>
            {error}
          </div>
        ) : costInfo ? (
          <>
            <div style={{
              background: "rgba(139, 92, 246, 0.05)",
              border: "1px solid rgba(139, 92, 246, 0.2)",
              borderRadius: "8px",
              padding: "20px",
              marginBottom: "24px",
            }}>
              <div style={{ marginBottom: "16px" }}>
                <div style={{ color: "#9ca3af", fontSize: "12px", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: "4px" }}>
                  New Tasks
                </div>
                <div style={{ color: "#f9fafb", fontSize: "24px", fontWeight: 600 }}>
                  {costInfo.breakdown?.new_task_count || 0}
                </div>
              </div>

              <div style={{ borderTop: "1px solid rgba(139, 92, 246, 0.2)", paddingTop: "16px" }}>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "8px" }}>
                  <span style={{ color: "#9ca3af" }}>Annotation Cost</span>
                  <span style={{ color: "#f9fafb" }}>₹{Math.round(costInfo.annotation_cost || 0)}</span>
                </div>
                {costInfo.additional_base_fee > 0 && (
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "8px" }}>
                    <span style={{ color: "#9ca3af" }}>Additional Base Fee</span>
                    <span style={{ color: "#f9fafb" }}>₹{Math.round(costInfo.additional_base_fee)}</span>
                  </div>
                )}
                <div style={{ display: "flex", justifyContent: "space-between", paddingTop: "8px", borderTop: "1px solid rgba(139, 92, 246, 0.2)" }}>
                  <span style={{ color: "#f9fafb", fontWeight: 600 }}>Total Cost</span>
                  <span style={{ color: "#8b5cf6", fontWeight: 600, fontSize: "18px" }}>₹{Math.round(costInfo.total_cost || 0)}</span>
                </div>
              </div>
            </div>

            <div style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              marginBottom: "24px",
              padding: "12px 16px",
              background: costInfo.has_sufficient_credits ? "rgba(16, 185, 129, 0.1)" : "rgba(239, 68, 68, 0.1)",
              border: `1px solid ${costInfo.has_sufficient_credits ? "rgba(16, 185, 129, 0.3)" : "rgba(239, 68, 68, 0.3)"}`,
              borderRadius: "8px",
            }}>
              <span style={{ color: "#9ca3af" }}>Available Credits</span>
              <span style={{ color: costInfo.has_sufficient_credits ? "#10b981" : "#ef4444", fontWeight: 600 }}>
                ₹{Math.round(costInfo.available_credits || 0)}
              </span>
            </div>

            {!costInfo.has_sufficient_credits && (
              <div style={{
                background: "rgba(239, 68, 68, 0.1)",
                border: "1px solid rgba(239, 68, 68, 0.3)",
                borderRadius: "8px",
                padding: "16px",
                color: "#fca5a5",
                marginBottom: "24px",
                fontSize: "13px",
              }}>
                Insufficient credits. Please add ₹{Math.round((costInfo.total_cost || 0) - (costInfo.available_credits || 0))} more credits to proceed.
              </div>
            )}
          </>
        ) : null}

        <div style={{ display: "flex", gap: "12px", justifyContent: "flex-end" }}>
          <button
            onClick={onCancel}
            style={secondaryButtonStyle}
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
          >
            Confirm & Import
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

    return refresh(pathname);
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

