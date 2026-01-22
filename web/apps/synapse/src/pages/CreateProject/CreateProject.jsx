import { EnterpriseBadge, Select, Typography } from "@synapse/ui";
import React from "react";
import { useHistory } from "react-router";
import { ToggleItems } from "../../components";
import { Button } from "@synapse/ui";
import { Modal } from "../../components/Modal/Modal";
import { Space } from "../../components/Space/Space";

import { useAPI } from "../../providers/ApiProvider";
import { cn } from "../../utils/bem";
import { ConfigPage } from "./Config/Config";
import "./CreateProject.scss";
import { ImportPage } from "./Import/Import";
import { useImportPage } from "./Import/useImportPage";
import { useDraftProject } from "./utils/useDraftProject";
import { Input, TextArea } from "../../components/Form";
import { FF_LSDV_E_297, isFF } from "../../utils/feature-flags";

import { SecurityDeposit } from "./SecurityDeposit/SecurityDeposit";

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

const ProjectName = ({
  name,
  setName,
  onSaveName,
  onSubmit,
  error,
  description,
  setDescription,
  show = true,
}) =>
  !show ? null : (
    <form
      className={cn("project-name")}
      onSubmit={(e) => {
        e.preventDefault();
        onSubmit();
      }}
    >
      <div className="w-full flex flex-col gap-2">
        <label className="w-full" htmlFor="project_name">
          Project Name
        </label>
        <Input
          name="name"
          id="project_name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          onBlur={onSaveName}
          className="project-title w-full"
        />
        {error && <span className="-mt-1 text-negative-content">{error}</span>}
      </div>
      <div className="w-full flex flex-col gap-2">
        <label className="w-full" htmlFor="project_description">
          Description
        </label>
        <TextArea
          name="description"
          id="project_description"
          placeholder="Optional description of your project"
          rows="4"
          style={{ minHeight: 100 }}
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          className="project-description w-full"
        />
      </div>
    </form>
  );

export const CreateProject = ({ onClose }) => {
  const [step, _setStep] = React.useState("name"); // name | import | config | deposit
  const [waiting, setWaitingStatus] = React.useState(false);

  const { project, setProject: updateProject } = useDraftProject();
  const history = useHistory();
  const api = useAPI();

  const [name, setName] = React.useState("");
  const [error, setError] = React.useState();
  const [description, setDescription] = React.useState("");
  const [sample, setSample] = React.useState(null);
  const [depositPaid, setDepositPaid] = React.useState(false);

  const setStep = React.useCallback((step) => {
    _setStep(step);
    const eventNameMap = {
      name: "project_name",
      import: "data_import",
      config: "labeling_setup",
      deposit: "security_deposit",
    };
    __lsa(`create_project.tab.${eventNameMap[step]}`);
  }, []);

  React.useEffect(() => {
    setError(null);
  }, [name]);

  const {
    columns,
    uploading,
    uploadDisabled,
    finishUpload,
    fileIds,
    pageProps,
    uploadSample,
  } = useImportPage(project, sample);

  const rootClass = cn("create-project");
  const tabClass = rootClass.elem("tab");
  const steps = {
    name: (
      <span className={tabClass.mod({ disabled: !!error })}>Project Name</span>
    ),
    import: (
      <span className={tabClass.mod({ disabled: uploadDisabled })}>
        Data Import
      </span>
    ),
    config: "Labeling Setup",
    deposit: (
      <span className={tabClass.mod({ disabled: !depositPaid })}>
        Security Deposit
      </span>
    ),
  };

  // Handle deposit collection
  const handleDepositCollected = React.useCallback((response) => {
    setDepositPaid(true);
    console.log("Security deposit collected:", response);
  }, []);

  const handleDepositError = React.useCallback((errorMsg) => {
    console.error("Deposit error:", errorMsg);
    // Could show a toast or modal here
  }, []);

  // name intentionally skipped from deps:
  // this should trigger only once when we got project loaded
  React.useEffect(() => {
    project && !name && setName(project.title);
  }, [project]);

  const projectBody = React.useMemo(
    () => ({
      title: name,
      description,
      label_config: project?.label_config ?? "<View></View>",
    }),
    [name, description, project?.label_config]
  );

  const onCreate = React.useCallback(async () => {
    // First, persist project with label_config so import/reimport validates against it
    const response = await api.callApi("updateProject", {
      params: {
        pk: project.id,
      },
      body: { ...projectBody, is_draft: false },
    });

    if (response === null) return;

    const imported = await finishUpload();

    if (!imported) return;

    setWaitingStatus(true);

    if (sample) await uploadSample(sample);

    __lsa("create_project.create", { sample: sample?.url });

    setWaitingStatus(false);

    history.push(`/projects/${response.id}/data`);
  }, [project, projectBody, finishUpload]);

  const onSaveName = async () => {
    if (error) return;
    const res = await api.callApi("updateProjectRaw", {
      params: {
        pk: project.id,
      },
      body: {
        title: name,
      },
    });

    if (res.ok) return;
    const err = await res.json();

    setError(err.validation_errors?.title);
  };

  const onDelete = React.useCallback(() => {
    const performClose = async () => {
      setWaitingStatus(true);
      if (project?.id)
        await api.callApi("deleteProject", {
          params: {
            pk: project.id,
          },
        });
      setWaitingStatus(false);
      updateProject(null);
      onClose?.();
    };
    performClose();
  }, [project]);

  // Get estimated task count from uploads
  const estimatedTasks = React.useMemo(() => {
    // Use fileIds length (number of uploaded files) as the task estimate
    return fileIds?.length || project?.task_number || 0;
  }, [fileIds, project?.task_number]);

  const isDisabled = !project || uploadDisabled || !!error || !depositPaid;

  const saveButtonStyle = isDisabled
    ? {
        ...primaryButtonStyle,
        background: "rgba(55, 65, 81, 0.5)",
        borderColor: "rgba(55, 65, 81, 0.5)",
        color: "#6b7280",
        cursor: "not-allowed",
      }
    : primaryButtonStyle;

  return (
    <Modal
      onHide={onDelete}
      closeOnClickOutside={false}
      allowToInterceptEscape
      fullscreen
      visible
      bare
    >
      <div className={rootClass}>
        <Modal.Header>
          <h1>Create Project</h1>
          <ToggleItems items={steps} active={step} onSelect={setStep} />

          <Space>
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
              look="outlined"
              onClick={onDelete}
              waiting={waiting}
              aria-label="Cancel project creation"
            >
              Cancel
            </button>
            <button
              look="primary"
              onClick={onCreate}
              style={saveButtonStyle}
              onMouseEnter={(e) => {
                if (!isDisabled) e.currentTarget.style.background = "#7c3aed";
              }}
              onMouseLeave={(e) => {
                if (!isDisabled) e.currentTarget.style.background = "#8b5cf6";
              }}
              waiting={waiting || uploading}
              waitingClickable={false}
              disabled={isDisabled}
            >
              Save
            </button>
          </Space>
        </Modal.Header>
        <ProjectName
          name={name}
          setName={setName}
          error={error}
          onSaveName={onSaveName}
          onSubmit={onCreate}
          description={description}
          setDescription={setDescription}
          show={step === "name"}
        />
        <ImportPage
          project={project}
          show={step === "import"}
          sample={sample}
          onSampleDatasetSelect={setSample}
          openLabelingConfig={() => setStep("config")}
          {...pageProps}
        />
        <ConfigPage
          project={project}
          onUpdate={(config) => {
            updateProject({ ...project, label_config: config });
          }}
          show={step === "config"}
          columns={columns}
          disableSaveButton={true}
        />
        <SecurityDeposit
          project={project}
          estimatedTasks={estimatedTasks}
          estimatedStorageGB={0}
          onDepositCollected={handleDepositCollected}
          onError={handleDepositError}
          show={step === "deposit"}
        />
      </div>
    </Modal>
  );
};
