import { observer } from "mobx-react";
import { useEffect, useState, useCallback } from "react";
import { Button, Space } from "@synapse/ui";
import { IconChevronLeft } from "@synapse/icons";
import "./ClientDataViewer.scss";

/**
 * Completely custom data viewer for organization members
 * Built from scratch - no SF, no annotation tools
 */
export const ClientDataViewer = observer(({ store }) => {
  const [tasks, setTasks] = useState([]);
  const [selectedTask, setSelectedTask] = useState(null);
  const [annotations, setAnnotations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [currentAnnotationIndex, setCurrentAnnotationIndex] = useState(0);

  const projectId = store.project?.id;

  useEffect(() => {
    if (projectId) {
      loadTasks();
    }
  }, [projectId]);

  const loadTasks = async () => {
    try {
      setLoading(true);
      const response = await fetch(`/api/projects/${projectId}/tasks/`, {
        headers: { "Content-Type": "application/json" },
      });

      if (response.ok) {
        const data = await response.json();
        setTasks(data || []);
      }
    } catch (error) {
      console.error("Failed to load tasks:", error);
    } finally {
      setLoading(false);
    }
  };

  const loadTaskDetails = async (taskId) => {
    try {
      const response = await fetch(`/api/tasks/${taskId}/`, {
        headers: { "Content-Type": "application/json" },
      });

      if (response.ok) {
        const taskData = await response.json();
        setSelectedTask(taskData);
        setAnnotations(taskData.annotations || []);
        setCurrentAnnotationIndex(0);
      }
    } catch (error) {
      console.error("Failed to load task details:", error);
    }
  };

  const handleTaskClick = (task) => {
    loadTaskDetails(task.id);
  };

  const handleBack = () => {
    setSelectedTask(null);
    setAnnotations([]);
  };

  const handlePrevAnnotation = () => {
    if (currentAnnotationIndex > 0) {
      setCurrentAnnotationIndex(currentAnnotationIndex - 1);
    }
  };

  const handleNextAnnotation = () => {
    if (currentAnnotationIndex < annotations.length - 1) {
      setCurrentAnnotationIndex(currentAnnotationIndex + 1);
    }
  };

  const renderTaskData = (data) => {
    if (!data) return null;

    if (data.image) {
      return (
        <img
          src={data.image}
          alt="Task"
          className="client-viewer__task-image"
        />
      );
    }

    if (data.text) {
      return <div className="client-viewer__task-text">{data.text}</div>;
    }

    if (data.audio) {
      return (
        <audio
          controls
          src={data.audio}
          className="client-viewer__task-audio"
        />
      );
    }

    if (data.video) {
      return (
        <video
          controls
          src={data.video}
          className="client-viewer__task-video"
        />
      );
    }

    return (
      <pre className="client-viewer__task-json">
        {JSON.stringify(data, null, 2)}
      </pre>
    );
  };

  const renderAnnotationResults = (results) => {
    if (!results || results.length === 0) {
      return <p>No results in this annotation</p>;
    }

    return results.map((result, idx) => (
      <div key={idx} className="client-viewer__result">
        <div className="result-type">{result.type}</div>
        {result.value?.rectanglelabels && (
          <div className="result-labels">
            {result.value.rectanglelabels.map((label, i) => (
              <span key={i} className="result-label">
                {label}
              </span>
            ))}
          </div>
        )}
        {result.value?.choices && (
          <div className="result-labels">
            {result.value.choices.map((choice, i) => (
              <span key={i} className="result-label">
                {choice}
              </span>
            ))}
          </div>
        )}
        {result.value?.labels && (
          <div className="result-labels">
            {result.value.labels.map((label, i) => (
              <span key={i} className="result-label">
                {label}
              </span>
            ))}
          </div>
        )}
        {result.value?.text && (
          <div className="result-text">{result.value.text}</div>
        )}
      </div>
    ));
  };

  // Task list view
  if (!selectedTask) {
    return (
      <div className="client-viewer">
        <div className="client-viewer__header">
          <h2>
            <span className="view-only-badge">🔒 VIEW ONLY MODE</span>
            {store.project?.title || "Project Tasks"}
          </h2>
          <p>
            Organization members can view tasks and annotations but cannot
            create or modify annotations.
          </p>
        </div>

        {loading ? (
          <div className="client-viewer__loading">Loading tasks...</div>
        ) : tasks.length === 0 ? (
          <div className="client-viewer__empty">
            No tasks found in this project
          </div>
        ) : (
          <div className="client-viewer__task-list">
            <table className="client-viewer__table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Preview</th>
                  <th>Annotations</th>
                  <th>Created</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {tasks.map((task) => (
                  <tr key={task.id}>
                    <td>#{task.id}</td>
                    <td>
                      {task.data?.image && (
                        <img
                          src={task.data.image}
                          alt="Preview"
                          className="task-thumbnail"
                        />
                      )}
                      {task.data?.text && (
                        <div className="task-text-preview">
                          {task.data.text.substring(0, 50)}...
                        </div>
                      )}
                    </td>
                    <td>
                      <span className="annotation-count">
                        {task.total_annotations || 0} annotations
                      </span>
                    </td>
                    <td>
                      {task.created_at
                        ? new Date(task.created_at).toLocaleDateString()
                        : "-"}
                    </td>
                    <td>
                      <Button
                        size="small"
                        onClick={() => handleTaskClick(task)}
                      >
                        View Details
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    );
  }

  // Task detail view
  const currentAnnotation = annotations[currentAnnotationIndex];

  return (
    <div className="client-viewer">
      <div className="client-viewer__detail-header">
        <Button size="small" icon={<IconChevronLeft />} onClick={handleBack}>
          Back to Task List
        </Button>
        <h2>
          <span className="view-only-badge">🔒 VIEW ONLY</span>
          Task #{selectedTask.id}
        </h2>
      </div>

      <div className="client-viewer__detail-content">
        <div className="client-viewer__task-section">
          <h3>Task Data</h3>
          {renderTaskData(selectedTask.data)}
        </div>

        <div className="client-viewer__annotations-section">
          <h3>Annotations ({annotations.length})</h3>

          {annotations.length === 0 ? (
            <p>No annotations available for this task</p>
          ) : (
            <>
              <div className="annotation-nav">
                <Button
                  size="small"
                  look="outlined"
                  disabled={currentAnnotationIndex === 0}
                  onClick={handlePrevAnnotation}
                >
                  Previous
                </Button>
                <span className="annotation-counter">
                  {currentAnnotationIndex + 1} / {annotations.length}
                </span>
                <Button
                  size="small"
                  look="outlined"
                  disabled={currentAnnotationIndex === annotations.length - 1}
                  onClick={handleNextAnnotation}
                >
                  Next
                </Button>
              </div>

              <div className="annotation-details">
                <div className="annotation-meta">
                  <div>
                    <strong>ID:</strong> {currentAnnotation.id}
                  </div>
                  <div>
                    <strong>Created by:</strong>{" "}
                    {currentAnnotation.completed_by?.email || "Unknown"}
                  </div>
                  {currentAnnotation.created_at && (
                    <div>
                      <strong>Created:</strong>{" "}
                      {new Date(currentAnnotation.created_at).toLocaleString()}
                    </div>
                  )}
                </div>

                <div className="annotation-results">
                  <h4>Results</h4>
                  {renderAnnotationResults(currentAnnotation.result)}
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
});

