import { useCallback, useRef, useState } from "react";
import { useHistory } from "react-router";
import { Button } from "@synapse/ui";
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

export const Inner = () => {
  const history = useHistory();
  const location = useFixedLocation();
  const modal = useRef();
  const refresh = useRefresh();
  const { project } = useProject();
  const [waiting, setWaitingStatus] = useState(false);
  const [sample, setSample] = useState(null);
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

  const onFinish = useCallback(async () => {
    if (sample) {
      await uploadSample(
        sample,
        () => setWaitingStatus(true),
        () => setWaitingStatus(false),
      );
    }

    const imported = await finishUpload();

    if (!imported) return;
    backToDM();
  }, [backToDM, finishUpload, sample]);

  return (
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
            onClick={onFinish}
            waiting={waiting || uploading}
            disabled={uploadDisabled}
            aria-label="Finish import"
            style={primaryButtonStyle}
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
      />
    </Modal>
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

