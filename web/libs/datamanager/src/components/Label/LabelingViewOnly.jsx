import { observer } from "mobx-react";
import { useEffect, useState, useCallback } from "react";
import { Button } from "@synapse/ui";
import { IconChevronLeft } from "@synapse/icons";
import { cn } from "../../utils/bem";
import "./Label.scss";

/**
 * View-only labeling interface
 * Shows task data and existing annotations without any annotation tools
 */
export const LabelingViewOnly = observer(({ store }) => {
  const [task, setTask] = useState(null);
  const [annotations, setAnnotations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [currentAnnotationIndex, setCurrentAnnotationIndex] = useState(0);

  useEffect(() => {
    loadCurrentTask();
  }, [store.taskStore.selected]);

  const loadCurrentTask = async () => {
    const selectedTask = store.taskStore.selected;
    if (!selectedTask) return;

    try {
      setLoading(true);
      const taskId = selectedTask.id;
      
      // Fetch full task details with annotations
      const response = await fetch(`/api/tasks/${taskId}/`, {
        headers: { 'Content-Type': 'application/json' }
      });
      
      if (response.ok) {
        const taskData = await response.json();
        setTask(taskData);
        setAnnotations(taskData.annotations || []);
        setCurrentAnnotationIndex(0);
      }
    } catch (error) {
      console.error('Failed to load task:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleBack = useCallback(() => {
    store.SDK.setMode("explorer");
  }, [store]);

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

  const renderTaskData = () => {
    if (!task?.data) return null;

    // Handle image data
    if (task.data.image) {
      return (
        <div className="view-only-task__image">
          <img src={task.data.image} alt="Task" />
        </div>
      );
    }

    // Handle text data
    if (task.data.text) {
      return (
        <div className="view-only-task__text">
          {task.data.text}
        </div>
      );
    }

    // Handle audio data
    if (task.data.audio) {
      return (
        <div className="view-only-task__audio">
          <audio controls src={task.data.audio} />
        </div>
      );
    }

    // Handle video data
    if (task.data.video) {
      return (
        <div className="view-only-task__video">
          <video controls src={task.data.video} />
        </div>
      );
    }

    return (
      <div className="view-only-task__data">
        <pre>{JSON.stringify(task.data, null, 2)}</pre>
      </div>
    );
  };

  const renderAnnotationDetails = () => {
    if (annotations.length === 0) {
      return (
        <div className="view-only-sidebar__empty">
          <p>No annotations available for this task</p>
        </div>
      );
    }

    const annotation = annotations[currentAnnotationIndex];

    return (
      <div className="view-only-sidebar__annotation">
        <div className="view-only-sidebar__annotation-nav">
          <Button
            size="small"
            look="outlined"
            disabled={currentAnnotationIndex === 0}
            onClick={handlePrevAnnotation}
          >
            Previous
          </Button>
          <span className="view-only-sidebar__annotation-count">
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

        <div className="view-only-sidebar__annotation-meta">
          <div className="view-only-sidebar__meta-item">
            <strong>ID:</strong> {annotation.id}
          </div>
          <div className="view-only-sidebar__meta-item">
            <strong>Created by:</strong> {annotation.completed_by?.email || 'Unknown'}
          </div>
          {annotation.created_at && (
            <div className="view-only-sidebar__meta-item">
              <strong>Created:</strong> {new Date(annotation.created_at).toLocaleString()}
            </div>
          )}
        </div>

        <div className="view-only-sidebar__results">
          <h4>Results</h4>
          {annotation.result && annotation.result.length > 0 ? (
            <div className="view-only-sidebar__results-list">
              {annotation.result.map((result, idx) => (
                <div key={idx} className="view-only-sidebar__result-item">
                  <div className="result-type">{result.type}</div>
                  {result.value?.rectanglelabels && (
                    <div className="result-labels">
                      {result.value.rectanglelabels.map((label, i) => (
                        <span key={i} className="result-label">{label}</span>
                      ))}
                    </div>
                  )}
                  {result.value?.choices && (
                    <div className="result-labels">
                      {result.value.choices.map((choice, i) => (
                        <span key={i} className="result-label">{choice}</span>
                      ))}
                    </div>
                  )}
                  {result.value?.labels && (
                    <div className="result-labels">
                      {result.value.labels.map((label, i) => (
                        <span key={i} className="result-label">{label}</span>
                      ))}
                    </div>
                  )}
                  {result.value?.text && (
                    <div className="result-text">{result.value.text}</div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <p>No results in this annotation</p>
          )}
        </div>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="view-only-labeling">
        <div className="view-only-labeling__loading">Loading task...</div>
      </div>
    );
  }

  return (
    <div className="view-only-labeling">
      <div className="view-only-header">
        <Button
          size="small"
          look="outlined"
          icon={<IconChevronLeft />}
          onClick={handleBack}
        >
          Back to Tasks
        </Button>
        <div className="view-only-header__title">
          <span className="view-only-badge">🔒 VIEW ONLY MODE</span>
          <span>Task #{task?.id}</span>
        </div>
      </div>

      <div className="view-only-content">
        <div className="view-only-task">
          {renderTaskData()}
        </div>
        <div className="view-only-sidebar">
          <h3>Annotations</h3>
          {renderAnnotationDetails()}
        </div>
      </div>
    </div>
  );
});

