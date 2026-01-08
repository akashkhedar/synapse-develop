import { useEffect, useRef, useState } from "react";
import { useHistory } from "react-router";
import { Button, useToast, ToastType } from "@synapse/ui";
import { Form, Input } from "../../components/Form";
import { Modal } from "../../components/Modal/Modal";
import { Space } from "../../components/Space/Space";
import { useAPI } from "../../providers/ApiProvider";
import { useFixedLocation, useParams } from "../../providers/RoutesProvider";
import { cn } from "../../utils/bem";
import { isDefined } from "../../utils/helpers";
import "./ExportPage.scss";

// const formats = {
//   json: 'JSON',
//   csv: 'CSV',
// };

const downloadFile = (blob, filename) => {
  const link = document.createElement("a");

  link.href = URL.createObjectURL(blob);
  link.download = filename;
  link.click();
};

const wait = () => new Promise((resolve) => setTimeout(resolve, 5000));

export const ExportPage = () => {
  const history = useHistory();
  const location = useFixedLocation();
  const pageParams = useParams();
  const api = useAPI();
  const toast = useToast();

  const [previousExports, setPreviousExports] = useState([]);
  const [downloading, setDownloading] = useState(false);
  const [downloadingMessage, setDownloadingMessage] = useState(false);
  const [availableFormats, setAvailableFormats] = useState([]);
  const [currentFormat, setCurrentFormat] = useState("JSON");
  const [showCostPreview, setShowCostPreview] = useState(false);
  const [costEstimate, setCostEstimate] = useState(null);
  const [loadingEstimate, setLoadingEstimate] = useState(false);

  /** @type {import('react').RefObject<Form>} */
  const form = useRef();

  const fetchCostEstimate = async () => {
    setLoadingEstimate(true);
    try {
      const params = form.current.assembleFormData({
        asJSON: true,
        full: true,
        booleansAsNumbers: true,
      });

      console.log("Fetching cost estimate for project:", pageParams.id);

      const data = await api.callApi("exportCostEstimate", {
        params: {
          pk: pageParams.id,
          download_all_tasks: params.download_all_tasks || false,
        },
      });

      console.log("Cost estimate data:", data);
      setCostEstimate(data);
      setShowCostPreview(true);
    } catch (error) {
      console.error("Failed to fetch cost estimate:", error);
      toast?.show({
        message: `Failed to fetch cost estimate: ${error.message || error}`,
        type: ToastType.error,
        duration: 5000,
      });
    } finally {
      setLoadingEstimate(false);
    }
  };

  const proceedExport = async () => {
    setDownloading(true);
    setShowCostPreview(false);

    const message = setTimeout(() => {
      setDownloadingMessage(true);
    }, 1000);

    try {
      const params = form.current.assembleFormData({
        asJSON: true,
        full: true,
        booleansAsNumbers: true,
      });

      console.log("Proceeding with export for project:", pageParams.id, "params:", params);

      // Build the URL for the export endpoint
      const exportUrl = `/api/projects/${pageParams.id}/export`;
      const queryParams = new URLSearchParams({
        exportType: params.exportType || params.export_type,
        download_all_tasks: params.download_all_tasks || false,
        download_resources: params.download_resources || false,
        interpolate_key_frames: params.interpolate_key_frames || false,
      });

      console.log("Export URL:", `${exportUrl}?${queryParams.toString()}`);

      // Use fetch directly to handle file download
      const response = await fetch(`${exportUrl}?${queryParams.toString()}`, {
        method: "GET",
        credentials: "same-origin",
        headers: {
          "Content-Type": "application/json",
        },
      });

      console.log("Export response status:", response.status, response.statusText);

      if (response.ok) {
        const blob = await response.blob();
        const filename = response.headers.get("filename") || 
                        response.headers.get("content-disposition")?.split("filename=")[1]?.replace(/"/g, "") || 
                        `export-${Date.now()}.json`;
        console.log("Download filename:", filename);
        downloadFile(blob, filename);

        // Show success message with credit info
        const creditsUsed = costEstimate?.credits_required || 0;
        const newBalance = costEstimate?.balance_after || 0;
        toast?.show({
          message: `Export completed successfully! ${creditsUsed.toFixed(1)} credits used. Balance: ${newBalance.toFixed(1)}`,
          type: ToastType.success,
          duration: 5000,
        });
      } else if (response.status === 402) {
        // Payment Required - Insufficient credits
        try {
          const errorData = await response.json();
          const creditMessage = errorData.detail || "Insufficient credits for export";
          const requiredCredits = errorData.required_credits || 0;
          const taskCount = errorData.task_count || 0;
          
          toast?.show({
            message: `${creditMessage}. Export requires ${requiredCredits} credits (${taskCount} tasks × 0.1 credits/task). Please purchase more credits.`,
            type: ToastType.error,
            duration: 8000,
          });
        } catch (e) {
          toast?.show({
            message: "Insufficient credits for export. Please purchase more credits to continue.",
            type: ToastType.error,
            duration: 5000,
          });
        }
      } else {
        const errorText = await response.text();
        console.error("Export failed:", response.status, response.statusText, errorText);
        toast?.show({
          message: `Export failed: ${response.statusText}`,
          type: ToastType.error,
          duration: 5000,
        });
      }
    } catch (error) {
      console.error("Export error:", error);
      toast?.show({
        message: `Export failed: ${error.message || error}`,
        type: ToastType.error,
        duration: 5000,
      });
    } finally {
      setDownloading(false);
      setDownloadingMessage(false);
      clearTimeout(message);
    }
  };

  useEffect(() => {
    if (isDefined(pageParams.id)) {
      api
        .callApi("previousExports", {
          params: {
            pk: pageParams.id,
          },
        })
        .then(({ export_files }) => {
          setPreviousExports(export_files.slice(0, 1));
        });

      api
        .callApi("exportFormats", {
          params: {
            pk: pageParams.id,
          },
        })
        .then((formats) => {
          setAvailableFormats(formats);
          setCurrentFormat(formats[0]?.name);
        });
    }
  }, [pageParams]);

  return (
    <>
      <Modal
        onHide={() => {
          const path = location.pathname.replace(ExportPage.path, "");
          const search = location.search;

          history.replace(`${path}${search !== "?" ? search : ""}`);
        }}
        title="Export data"
        style={{ width: 720 }}
        closeOnClickOutside={false}
        allowClose={!downloading}
        // footer="Read more about supported export formats in the Documentation."
        visible
      >
        <div className={cn("export-page").toClassName()}>
          <FormatInfo
            availableFormats={availableFormats}
            selected={currentFormat}
            onClick={(format) => setCurrentFormat(format.name)}
          />

          <Form ref={form}>
            <Input type="hidden" name="exportType" value={currentFormat} />
          </Form>

          <div className={cn("export-page").elem("footer").toClassName()}>
            <Space style={{ width: "100%" }} spread>
              <div className={cn("export-page").elem("recent").toClassName()}>{/* {exportHistory} */}</div>
              <div className={cn("export-page").elem("actions").toClassName()}>
                <Space>
                  {downloadingMessage && (
                    <div style={{ display: "flex", alignItems: "center", gap: "8px", color: "#6b7280" }}>
                      <div className="spinner" style={{
                        width: "16px",
                        height: "16px",
                        border: "2px solid #e5e7eb",
                        borderTop: "2px solid #3b82f6",
                        borderRadius: "50%",
                        animation: "spin 0.8s linear infinite"
                      }}></div>
                      <span>Files are being prepared. This might take some time...</span>
                    </div>
                  )}
                  <Button 
                    className="w-[135px]" 
                    onClick={fetchCostEstimate} 
                    waiting={loadingEstimate || downloading} 
                    aria-label="Export data"
                  >
                    {loadingEstimate ? "Loading..." : downloading ? "Exporting..." : "Export"}
                  </Button>
                </Space>
              </div>
            </Space>
          </div>
        </div>
      </Modal>

      {loadingEstimate && (
        <Modal
          title="Calculating Cost..."
          visible={true}
          style={{ width: 400 }}
          closeOnClickOutside={false}
          allowClose={false}
        >
          <div style={{ 
            padding: "40px 20px", 
            textAlign: "center",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            gap: "20px"
          }}>
            <div className="spinner" style={{
              width: "40px",
              height: "40px",
              border: "4px solid #e5e7eb",
              borderTop: "4px solid #3b82f6",
              borderRadius: "50%"
            }}></div>
            <p style={{ margin: 0, color: "#6b7280", fontSize: "14px" }}>
              Calculating export cost for your tasks...
            </p>
          </div>
        </Modal>
      )}

      {showCostPreview && costEstimate && (
        <CostPreviewModal
          costEstimate={costEstimate}
          onConfirm={proceedExport}
          onCancel={() => setShowCostPreview(false)}
          isProcessing={downloading}
        />
      )}
    </>
  );
};

const FormatInfo = ({ availableFormats, selected, onClick }) => {
  return (
    <div className={cn("formats").toClassName()}>
      <div className={cn("formats").elem("info").toClassName()}>
        You can export dataset in one of the following formats:
      </div>
      <div className={cn("formats").elem("list").toClassName()}>
        {availableFormats.map((format) => (
          <div
            key={format.name}
            className={cn("formats")
              .elem("item")
              .mod({
                active: !format.disabled,
                selected: format.name === selected,
              })
              .toClassName()}
            onClick={!format.disabled ? () => onClick(format) : null}
          >
            <div className={cn("formats").elem("name").toClassName()}>
              {format.title}

              <Space size="small">
                {format.tags?.map?.((tag, index) => (
                  <div key={index} className={cn("formats").elem("tag").toClassName()}>
                    {tag}
                  </div>
                ))}
              </Space>
            </div>

            {format.description && (
              <div className={cn("formats").elem("description").toClassName()}>{format.description}</div>
            )}
          </div>
        ))}
      </div>
      <div className={cn("formats").elem("feedback").toClassName()}>
        Can't find an export format?
        <br />
        Please let us know in{" "}
        <a className="no-go" href="https://slack.synapse.io/?source=product-export" target="_blank" rel="noreferrer">
          Slack
        </a>{" "}
        or submit an issue to the{" "}
        <a
          className="no-go"
          href="https://github.com/Synapse/synapse-converter/issues"
          target="_blank"
          rel="noreferrer"
        >
          Repository
        </a>
      </div>
    </div>
  );
};

const CostPreviewModal = ({ costEstimate, onConfirm, onCancel, isProcessing }) => {
  const history = useHistory();
  const { task_count, credits_required, current_balance, balance_after, can_afford } = costEstimate;

  return (
    <Modal
      title="Confirm Export"
      visible={true}
      onHide={onCancel}
      style={{ width: 500 }}
      closeOnClickOutside={false}
      allowClose={!isProcessing}
    >
      <div style={{ padding: "20px 0" }}>
        <div style={{ 
          backgroundColor: can_afford ? "#f0f9ff" : "#fef2f2", 
          border: can_afford ? "1px solid #3b82f6" : "1px solid #ef4444",
          borderRadius: "8px", 
          padding: "20px",
          marginBottom: "20px"
        }}>
          <h3 style={{ 
            margin: "0 0 15px 0", 
            fontSize: "16px", 
            fontWeight: "600",
            color: can_afford ? "#1e40af" : "#991b1b"
          }}>
            {can_afford ? "Export Cost Summary" : "⚠️ Insufficient Credits"}
          </h3>
          
          <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <span style={{ color: "#6b7280", fontSize: "14px" }}>Tasks to export:</span>
              <span style={{ fontWeight: "600", fontSize: "16px" }}>{task_count}</span>
            </div>
            
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <span style={{ color: "#6b7280", fontSize: "14px" }}>Rate per task:</span>
              <span style={{ fontWeight: "500", fontSize: "14px" }}>0.1 credits</span>
            </div>
            
            <div style={{ 
              borderTop: "1px solid #e5e7eb", 
              paddingTop: "12px",
              marginTop: "4px"
            }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <span style={{ color: "#374151", fontSize: "15px", fontWeight: "500" }}>Credits required:</span>
                <span style={{ 
                  fontWeight: "700", 
                  fontSize: "18px",
                  color: can_afford ? "#059669" : "#dc2626"
                }}>
                  {credits_required.toFixed(1)}
                </span>
              </div>
            </div>
          </div>
        </div>

        <div style={{ 
          display: "flex", 
          flexDirection: "column", 
          gap: "10px",
          padding: "15px",
          backgroundColor: "#f9fafb",
          borderRadius: "6px"
        }}>
          <div style={{ display: "flex", justifyContent: "space-between" }}>
            <span style={{ color: "#4b5563", fontSize: "14px" }}>Current balance:</span>
            <span style={{ fontWeight: "600", color: "#111827" }}>{current_balance.toFixed(1)} credits</span>
          </div>
          
          <div style={{ display: "flex", justifyContent: "space-between" }}>
            <span style={{ color: "#4b5563", fontSize: "14px" }}>After export:</span>
            <span style={{ 
              fontWeight: "600",
              color: balance_after >= 0 ? "#059669" : "#dc2626"
            }}>
              {balance_after.toFixed(1)} credits
            </span>
          </div>
        </div>

        {!can_afford && (
          <div style={{ 
            marginTop: "15px", 
            padding: "12px", 
            backgroundColor: "#fef2f2",
            borderLeft: "4px solid #ef4444",
            borderRadius: "4px"
          }}>
            <p style={{ 
              margin: "0 0 10px 0", 
              fontSize: "13px", 
              color: "#991b1b",
              lineHeight: "1.5"
            }}>
              You don't have enough credits to complete this export. 
              Please purchase more credits or a subscription plan to continue.
            </p>
            <Button
              onClick={() => {
                onCancel();
                history.push("/billing");
              }}
              style={{
                backgroundColor: "#3b82f6",
                color: "white",
                fontSize: "13px",
                padding: "6px 12px",
                marginTop: "8px"
              }}
            >
              Purchase Credits →
            </Button>
          </div>
        )}

        <div style={{ 
          display: "flex", 
          justifyContent: "flex-end", 
          gap: "10px",
          marginTop: "25px"
        }}>
          <Button 
            onClick={onCancel} 
            disabled={isProcessing}
            style={{ minWidth: "100px" }}
          >
            Cancel
          </Button>
          <Button 
            onClick={onConfirm}
            disabled={!can_afford || isProcessing}
            waiting={isProcessing}
            style={{ 
              minWidth: "150px",
              backgroundColor: can_afford ? "#3b82f6" : "#9ca3af",
              cursor: can_afford ? "pointer" : "not-allowed"
            }}
            aria-label="Confirm and export"
          >
            {can_afford ? "Confirm & Export" : "Insufficient Credits"}
          </Button>
          {can_afford && (
            <a 
              href="/billing#transactions"
              onClick={(e) => {
                e.preventDefault();
                history.push("/billing");
              }}
              style={{
                alignSelf: "center",
                fontSize: "13px",
                color: "#3b82f6",
                textDecoration: "none",
                marginLeft: "10px"
              }}
            >
              View transactions
            </a>
          )}
        </div>
      </div>
    </Modal>
  );
};

ExportPage.path = "/export";
ExportPage.modal = true;


