import React, { useEffect, useRef, useState, useCallback } from "react";
import { onSnapshot } from "mobx-state-tree";
import type { TestCase, AnnotationResult } from "../data/testCases";
import "./AnnotationTestTask.css";

interface AnnotationTestTaskProps {
  testCase: TestCase;
  onComplete: (annotation: AnnotationResult[]) => void;
  onSkip?: () => void;
  taskNumber: number;
  totalTasks: number;
  timeRemaining?: number;
}

export const AnnotationTestTask: React.FC<AnnotationTestTaskProps> = ({
  testCase,
  onComplete,
  onSkip,
  taskNumber,
  totalTasks,
  timeRemaining,
}) => {
  const rootRef = useRef<HTMLDivElement>(null);
  const sfInstance = useRef<any>(null);
  const [annotation, setAnnotation] = useState<AnnotationResult[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Format time as MM:SS
  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  };

  // Difficulty badge colors
  const difficultyColors = {
    easy: { bg: "rgba(34, 197, 94, 0.15)", border: "rgba(34, 197, 94, 0.3)", text: "#22c55e" },
    medium: { bg: "rgba(251, 191, 36, 0.15)", border: "rgba(251, 191, 36, 0.3)", text: "#fbbf24" },
    hard: { bg: "rgba(239, 68, 68, 0.15)", border: "rgba(239, 68, 68, 0.3)", text: "#ef4444" },
  };

  const difficultyStyle = difficultyColors[testCase.difficulty];

  // Initialize Synapse editor
  useEffect(() => {
    let Synapse: any;
    let snapshotDisposer: any;

    const cleanup = () => {
      if (sfInstance.current) {
        try {
          sfInstance.current.destroy();
        } catch {
          // Ignore cleanup errors
        }
        sfInstance.current = null;
      }
      if (snapshotDisposer) {
        snapshotDisposer();
        snapshotDisposer = null;
      }
    };

    const loadSynapse = async () => {
      try {
        setIsLoading(true);
        setError(null);
        
        // Dynamic import of Synapse editor
        const editorModule = await import("@synapse/editor");
        Synapse = editorModule.Synapse;

        if (!Synapse || !rootRef.current) {
          setError("Failed to load annotation editor");
          setIsLoading(false);
          return;
        }

        cleanup();

        // Create Synapse instance
        // Use taskNumber as numeric ID since Synapse requires numeric task IDs
        sfInstance.current = new Synapse(rootRef.current, {
          config: testCase.config,
          task: {
            id: taskNumber,
            data: testCase.task.data,
          },
          interfaces: ["side-column", "controls"],
          instanceOptions: {
            reactVersion: "v18",
          },
          settings: {
            forceBottomPanel: false,
            fullscreen: false,
          },
          onStorageInitialized: (LS: any) => {
            const initAnnotation = () => {
              const as = LS.annotationStore;
              const c = as.createAnnotation();
              as.selectAnnotation(c.id);

              const annotationObj = as.selected;
              if (annotationObj) {
                // Listen for annotation changes
                snapshotDisposer = onSnapshot(annotationObj, () => {
                  const serialized = annotationObj.serializeAnnotation();
                  setAnnotation(serialized || []);
                });
              }
              setIsLoading(false);
            };
            setTimeout(initAnnotation, 100);
          },
        });
      } catch (e) {
        console.error("Failed to load Synapse editor:", e);
        setError("Failed to load annotation interface. Please refresh the page.");
        setIsLoading(false);
      }
    };

    loadSynapse();

    return () => {
      cleanup();
    };
  }, [testCase]);

  const handleSubmit = useCallback(() => {
    onComplete(annotation);
  }, [annotation, onComplete]);

  return (
    <div className="annotation-test-task">
      {/* Header */}
      <div className="annotation-test-task__header">
        <div className="annotation-test-task__progress">
          <span className="annotation-test-task__task-number">
            Task {taskNumber}/{totalTasks}
          </span>
          <div className="annotation-test-task__progress-bar">
            <div
              className="annotation-test-task__progress-fill"
              style={{ width: `${(taskNumber / totalTasks) * 100}%` }}
            />
          </div>
        </div>
        {timeRemaining !== undefined && (
          <div className={`annotation-test-task__timer ${timeRemaining < 60 ? "annotation-test-task__timer--warning" : ""}`}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10" />
              <polyline points="12 6 12 12 16 14" />
            </svg>
            {formatTime(timeRemaining)}
          </div>
        )}
      </div>

      {/* Task Info */}
      <div className="annotation-test-task__info">
        <div className="annotation-test-task__title-row">
          <h2 className="annotation-test-task__title">{testCase.title}</h2>
          <div className="annotation-test-task__badges">
            <span
              className="annotation-test-task__difficulty"
              style={{
                background: difficultyStyle.bg,
                borderColor: difficultyStyle.border,
                color: difficultyStyle.text,
              }}
            >
              {testCase.difficulty}
            </span>
            <span className="annotation-test-task__points">
              {testCase.points} pts
            </span>
          </div>
        </div>
        <p className="annotation-test-task__description">{testCase.description}</p>
      </div>

      {/* Editor Container */}
      <div className="annotation-test-task__editor-container">
        {isLoading && (
          <div className="annotation-test-task__loading">
            <div className="annotation-test-task__spinner" />
            <span>Loading annotation interface...</span>
          </div>
        )}
        {error && (
          <div className="annotation-test-task__error">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10" />
              <line x1="12" y1="8" x2="12" y2="12" />
              <line x1="12" y1="16" x2="12.01" y2="16" />
            </svg>
            <span>{error}</span>
          </div>
        )}
        <div
          ref={rootRef}
          className={`annotation-test-task__editor ${isLoading ? "annotation-test-task__editor--hidden" : ""}`}
        />
      </div>

      {/* Footer Actions */}
      <div className="annotation-test-task__footer">
        <div className="annotation-test-task__annotation-status">
          {annotation.length > 0 ? (
            <span className="annotation-test-task__status--has-annotation">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <polyline points="20 6 9 17 4 12" />
              </svg>
              Annotation added
            </span>
          ) : (
            <span className="annotation-test-task__status--no-annotation">
              No annotation yet
            </span>
          )}
        </div>
        <div className="annotation-test-task__actions">
          {onSkip && (
            <button
              type="button"
              className="annotation-test-task__skip"
              onClick={onSkip}
            >
              Skip
            </button>
          )}
          <button
            type="button"
            className="annotation-test-task__submit"
            onClick={handleSubmit}
            disabled={annotation.length === 0}
          >
            Submit & Continue
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M5 12h14M12 5l7 7-7 7" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
};
