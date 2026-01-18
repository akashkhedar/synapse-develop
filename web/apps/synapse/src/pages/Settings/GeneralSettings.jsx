import { EnterpriseBadge, Select, Typography } from "@synapse/ui";
import { useCallback, useContext } from "react";
import { Button } from "@synapse/ui";
import { Form, Input, TextArea } from "../../components/Form";
import { RadioGroup } from "../../components/Form/Elements/RadioGroup/RadioGroup";
import { ProjectContext } from "../../providers/ProjectProvider";
import { cn } from "../../utils/bem";
import { FF_LSDV_E_297, isFF } from "../../utils/feature-flags";

export const GeneralSettings = () => {
  const { project, fetchProject } = useContext(ProjectContext);

  const updateProject = useCallback(() => {
    if (project.id) fetchProject(project.id, true);
  }, [project]);

  const colors = [
    "#FDFDFC",
    "#FF4C25",
    "#FF750F",
    "#ECB800",
    "#9AC422",
    "#34988D",
    "#617ADA",
    "#CC6FBE",
  ];

  const samplings = [
    {
      value: "Sequential",
      label: "Sequential",
      description: "Tasks are ordered by Task ID",
    },
    {
      value: "Uniform",
      label: "Random",
      description: "Tasks are chosen with uniform random",
    },
  ];

  return (
    <div className={cn("general-settings").toClassName()}>
      <div className={cn("general-settings").elem("wrapper").toClassName()}>
        <h1>General Settings</h1>
        <div className={cn("settings-wrapper").toClassName()}>
          <Form
            action="updateProject"
            formData={{ ...project }}
            params={{ pk: project.id }}
            onSubmit={updateProject}
          >
            <Form.Row columnCount={1} rowGap="16px">
              <Input name="title" label="Project Name" />

              <TextArea
                name="description"
                label="Description"
                style={{ minHeight: 128 }}
              />

              <RadioGroup
                name="color"
                label="Color"
                size="large"
                labelProps={{ size: "large" }}
              >
                {colors.map((color) => (
                  <RadioGroup.Button key={color} value={color}>
                    <div
                      className={cn("color").toClassName()}
                      style={{ "--background": color }}
                    />
                  </RadioGroup.Button>
                ))}
              </RadioGroup>

              <RadioGroup
                label="Task Sampling"
                labelProps={{ size: "large" }}
                name="sampling"
                simple
              >
                {samplings.map(({ value, label, description }) => (
                  <RadioGroup.Button
                    key={value}
                    value={`${value} sampling`}
                    label={`${label} sampling`}
                    description={description}
                  />
                ))}
              </RadioGroup>
            </Form.Row>

            <Form.Actions>
              <Form.Indicator>
                <span case="success">Saved!</span>
              </Form.Indicator>
              <button
                type="submit"
                aria-label="Save general settings"
                style={{
                  width: "150px",
                  height: "44px",
                  background: "linear-gradient(135deg, rgba(139, 92, 246, 0.2), rgba(168, 85, 247, 0.12))",
                  border: "1px solid rgba(139, 92, 246, 0.4)",
                  borderRadius: "0",
                  color: "#c4b5fd",
                  fontSize: "13px",
                  fontWeight: "600",
                  textTransform: "uppercase",
                  letterSpacing: "0.05em",
                  fontFamily: "'Space Grotesk', system-ui, sans-serif",
                  cursor: "pointer",
                  transition: "all 0.2s cubic-bezier(0.4, 0, 0.2, 1)",
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.background = "linear-gradient(135deg, rgba(139, 92, 246, 0.3), rgba(168, 85, 247, 0.18))";
                  e.currentTarget.style.borderColor = "rgba(139, 92, 246, 0.6)";
                  e.currentTarget.style.color = "#ffffff";
                  e.currentTarget.style.boxShadow = "0 4px 16px rgba(139, 92, 246, 0.25)";
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.background = "linear-gradient(135deg, rgba(139, 92, 246, 0.2), rgba(168, 85, 247, 0.12))";
                  e.currentTarget.style.borderColor = "rgba(139, 92, 246, 0.4)";
                  e.currentTarget.style.color = "#c4b5fd";
                  e.currentTarget.style.boxShadow = "none";
                }}
              >
                Save
              </button>
            </Form.Actions>
          </Form>
        </div>
      </div>
    </div>
  );
};

GeneralSettings.menuItem = "General";
GeneralSettings.path = "/";
GeneralSettings.exact = true;
