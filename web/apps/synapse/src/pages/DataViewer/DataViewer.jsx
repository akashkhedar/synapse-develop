import React, { useEffect, useState } from "react";
import { Button, Spin, Empty, Image, Tag, Typography } from "antd";
import { ArrowLeftOutlined, EyeOutlined } from "@ant-design/icons";
import { useAPI } from "../../providers/ApiProvider";
import { useParams, useHistory } from "react-router-dom";
import "./DataViewer.scss";

const { Title, Text } = Typography;

/**
 * Read-only Data Viewer for Organization Members
 * Shows tasks and annotations without any editing capabilities
 */
export const DataViewer = () => {
  const api = useAPI();
  const history = useHistory();
  const params = useParams();
  const projectId = params.id; // Route uses :id not :projectId

  const [loading, setLoading] = useState(true);
  const [tasks, setTasks] = useState([]);
  const [selectedTask, setSelectedTask] = useState(null);
  const [project, setProject] = useState(null);

  useEffect(() => {
    if (projectId) {
      loadProject();
      loadTasks();
    }
  }, [projectId]);

  const loadProject = async () => {
    try {
      const response = await api.callApi("project", {
        params: { pk: projectId },
      });
      setProject(response);
    } catch (error) {
      console.error("Failed to load project:", error);
    }
  };

  const loadTasks = async () => {
    try {
      setLoading(true);
      // Use Data Manager tasks API. Backend will restrict to annotator-assigned
      // tasks when the requester is an annotator (RBAC handled server-side).
      const url = `/api/dm/tasks?project=${projectId}&page=1&page_size=100`;
      const response = await fetch(url, {
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include",
      });

      if (!response.ok) throw new Error("Failed to load tasks");

      const data = await response.json();
      // TaskPagination returns { tasks: [...], total, total_annotations, total_predictions }
      if (Array.isArray(data?.tasks)) {
        setTasks(data.tasks);
      } else if (Array.isArray(data)) {
        // fallback if API returns plain list
        setTasks(data);
      } else {
        setTasks([]);
      }
    } catch (error) {
      console.error("Failed to load tasks:", error);
      setTasks([]);
    } finally {
      setLoading(false);
    }
  };

  const loadTaskDetails = async (taskId) => {
    try {
      setLoading(true);
      // Fetch task details including annotations
      const response = await fetch(
        `/api/tasks/${taskId}?project=${projectId}`,
        {
          headers: {
            "Content-Type": "application/json",
          },
        }
      );

      if (!response.ok) throw new Error("Failed to load task details");

      const taskData = await response.json();
      setSelectedTask(taskData);
    } catch (error) {
      console.error("Failed to load task details:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleTaskClick = (task) => {
    loadTaskDetails(task.id);
  };

  const handleBack = () => {
    if (selectedTask) {
      setSelectedTask(null);
    } else {
      history.push(`/projects/${projectId}`);
    }
  };

  const renderTaskList = () => (
    <div className="data-viewer">
      <div className="data-viewer__header">
        <Button icon={<ArrowLeftOutlined />} onClick={handleBack} type="link">
          Back to Project
        </Button>
        <Title level={3}>
          <EyeOutlined /> View Data - {project?.title}
        </Title>
        <Tag color="blue">View Only Mode</Tag>
      </div>

      {loading ? (
        <div className="data-viewer__loading">
          <Spin size="large" />
        </div>
      ) : tasks.length === 0 ? (
        <Empty description="No tasks found in this project" />
      ) : (
        <div className="data-viewer__grid">
          {tasks.map((task) => (
            <div
              key={task.id}
              className="data-viewer__card"
              onClick={() => handleTaskClick(task)}
            >
              <div className="data-viewer__card-preview">
                {task.data?.image ? (
                  <img src={task.data.image} alt={`Task ${task.id}`} />
                ) : (
                  <div className="data-viewer__card-placeholder">
                    No Preview
                  </div>
                )}
              </div>
              <div className="data-viewer__card-info">
                <Text strong>Task #{task.id}</Text>
                <div>
                  <Tag color={task.total_annotations > 0 ? "green" : "default"}>
                    {task.total_annotations || 0} Annotations
                  </Tag>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );

  const renderTaskDetail = () => {
    if (!selectedTask) return null;

    const annotations = selectedTask.annotations || [];
    const hasAnnotations = annotations.length > 0;

    return (
      <div className="data-viewer">
        <div className="data-viewer__header">
          <Button icon={<ArrowLeftOutlined />} onClick={handleBack} type="link">
            Back to Tasks
          </Button>
          <Title level={3}>Task #{selectedTask.id}</Title>
          <Tag color="blue">View Only</Tag>
        </div>

        <div className="data-viewer__detail">
          <div className="data-viewer__detail-content">
            {/* Task Data */}
            <div className="data-viewer__detail-image">
              {selectedTask.data?.image && (
                <Image
                  src={selectedTask.data.image}
                  alt={`Task ${selectedTask.id}`}
                  style={{ maxWidth: "100%" }}
                />
              )}
            </div>

            {/* Annotations Display */}
            <div className="data-viewer__detail-annotations">
              <Title level={4}>Annotations ({annotations.length})</Title>
              {!hasAnnotations ? (
                <Empty description="No annotations yet" />
              ) : (
                <div className="data-viewer__annotations-list">
                  {annotations.map((annotation, idx) => (
                    <div
                      key={annotation.id}
                      className="data-viewer__annotation-item"
                    >
                      <div className="data-viewer__annotation-header">
                        <Text strong>Annotation #{idx + 1}</Text>
                        <Text type="secondary">
                          by {annotation.completed_by?.email || "Unknown"}
                        </Text>
                      </div>
                      <div className="data-viewer__annotation-results">
                        {annotation.result?.map((result, resultIdx) => (
                          <Tag key={resultIdx} color="blue">
                            {result.value?.rectanglelabels?.[0] ||
                              result.value?.choices?.[0] ||
                              result.value?.text ||
                              "Annotation"}
                          </Tag>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="data-viewer-container">
      {selectedTask ? renderTaskDetail() : renderTaskList()}
    </div>
  );
};

