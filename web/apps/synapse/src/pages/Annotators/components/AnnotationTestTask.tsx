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
  const annotationRef = useRef<AnnotationResult[]>([]);
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
    easy: {
      bg: "rgba(34, 197, 94, 0.15)",
      border: "rgba(34, 197, 94, 0.3)",
      text: "#22c55e",
    },
    medium: {
      bg: "rgba(251, 191, 36, 0.15)",
      border: "rgba(251, 191, 36, 0.3)",
      text: "#fbbf24",
    },
    hard: {
      bg: "rgba(239, 68, 68, 0.15)",
      border: "rgba(239, 68, 68, 0.3)",
      text: "#ef4444",
    },
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
                // Listeners are now handled in the separate useEffect
              }
              setIsLoading(false);
            };
            setTimeout(initAnnotation, 100);
          },
        });
      } catch (e) {
        console.error("Failed to load Synapse editor:", e);
        setError(
          "Failed to load annotation interface. Please refresh the page."
        );
        setIsLoading(false);
      }
    };

    loadSynapse();

    return () => {
      cleanup();
    };
  }, [testCase]);

  // POLLING-BASED DATA CAPTURE (REMAKE)
  // Listeners were unreliable for 'Choices', so we poll the store state directly.
  useEffect(() => {
    // Poll every 250ms to check for annotation changes
    const pollInterval = setInterval(() => {
      if (!sfInstance.current) return;

      try {
        const store = sfInstance.current.store;
        if (!store || !store.annotationStore) return;

        const annotationObj = store.annotationStore.selected;
        if (annotationObj) {
          // Get the serialized annotation
          const result = annotationObj.serializeAnnotation();

          // DEBUG: Also try to get choices directly from the annotation areas/results
          // The Synapse editor stores choices in annotationObj.results
          if (annotationObj.results) {
            const resultsArray = Array.from(
              annotationObj.results.values?.() || []
            );
            if (resultsArray.length > 0 && (!result || result.length === 0)) {
              console.warn(
                "[POLLER DEBUG] annotationObj.results has data but serializeAnnotation returned empty!",
                {
                  resultsCount: resultsArray.length,
                  resultsTypes: resultsArray.map((r: any) => r.type),
                  firstResult: resultsArray[0],
                }
              );
            }
          }

          // Only update if changed to avoid render thrashing
          const currentStr = JSON.stringify(annotationRef.current);
          const newStr = JSON.stringify(result);

          if (currentStr !== newStr) {
            console.log("[POLLER] Annotation changed:", result);
            console.log(
              "[POLLER] Annotation from_names:",
              result?.map((r: any) => r.from_name)
            );
            setAnnotation(result);
            annotationRef.current = result;
          }
        }
      } catch (e) {
        // Log errors for debugging
        console.warn("[POLLER] Error reading annotation:", e);
      }
    }, 250);

    return () => clearInterval(pollInterval);
  }, [testCase]);

  // Submit Handler
  const handleSubmit = useCallback(() => {
    console.log("[SUBMIT] Submit clicked.");

    // 1. Try reading from Ref (populated by Poller)
    let finalAnnotation = annotationRef.current;
    console.log("[SUBMIT] Annotation from Ref:", finalAnnotation);

    // 2. Force Immediate Read (Failsafe)
    if (
      (!finalAnnotation || finalAnnotation.length === 0) &&
      sfInstance.current
    ) {
      try {
        console.log("[SUBMIT] Ref empty, forcing Store read...");
        const store = sfInstance.current.store;
        const annotationObj = store?.annotationStore?.selected;
        if (annotationObj) {
          const fresh = annotationObj.serializeAnnotation();
          console.log("[SUBMIT] Forced serializeAnnotation Result:", fresh);
          if (fresh && fresh.length > 0) {
            finalAnnotation = fresh;
          }
        }
      } catch (e) {
        console.error("[SUBMIT] Forced Store Read Failed:", e);
      }
    }

    // 3. DEEP FALLBACK: Extract directly from annotation areas/results
    // This handles cases where serializeAnnotation doesn't return Choices
    if (
      (!finalAnnotation || finalAnnotation.length === 0) &&
      sfInstance.current
    ) {
      try {
        console.log("[SUBMIT] Trying deep extraction from annotation areas...");
        const store = sfInstance.current.store;
        const annotationObj = store?.annotationStore?.selected;

        if (annotationObj) {
          const extractedResults: AnnotationResult[] = [];

          // Try to access the internal results/areas of the annotation
          // Synapse editor stores selected choices in the annotation's results or areas
          const areas = annotationObj.areas || new Map();
          const results = annotationObj.results || new Map();

          // Iterate over areas (this is where choices are stored)
          if (areas?.values) {
            for (const area of areas.values()) {
              if (area.type === "choices" || area.results) {
                console.log("[SUBMIT] Found area:", area.type, area);

                // For choices, extract the selected values
                if (area.results?.values) {
                  for (const result of area.results.values()) {
                    if (result.type === "choices") {
                      const choices =
                        result.selectedValues || result.value?.choices || [];
                      if (choices.length > 0) {
                        extractedResults.push({
                          type: "choices",
                          value: { choices },
                          from_name:
                            result.from_name?.name ||
                            result.from_name ||
                            "unknown",
                          to_name:
                            result.to_name?.name || result.to_name || "unknown",
                        });
                      }
                    }
                  }
                }
              }
            }
          }

          // Also try direct results iteration
          if (results?.values) {
            for (const result of results.values()) {
              console.log("[SUBMIT] Found result:", result.type, result);
              if (result.type === "choices") {
                const choices =
                  result.selectedValues || result.value?.choices || [];
                if (choices.length > 0) {
                  extractedResults.push({
                    type: "choices",
                    value: { choices },
                    from_name:
                      result.from_name?.name || result.from_name || "unknown",
                    to_name:
                      result.to_name?.name || result.to_name || "unknown",
                  });
                }
              }
            }
          }

          if (extractedResults.length > 0) {
            console.log(
              "[SUBMIT] Deep extraction found results:",
              extractedResults
            );
            finalAnnotation = extractedResults;
          }
        }
      } catch (e) {
        console.error("[SUBMIT] Deep extraction failed:", e);
      }
    }

    if (!finalAnnotation || finalAnnotation.length === 0) {
      console.error(
        "[SUBMIT] CRITICAL: Still no annotation found after all attempts!"
      );
    } else {
      console.log("[SUBMIT] Final annotation to submit:", finalAnnotation);
    }

    onComplete(finalAnnotation);
  }, [onComplete]);

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
          <div
            className={`annotation-test-task__timer ${
              timeRemaining < 60 ? "annotation-test-task__timer--warning" : ""
            }`}
          >
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
            >
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
        <p className="annotation-test-task__description">
          {testCase.description}
        </p>
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
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
            >
              <circle cx="12" cy="12" r="10" />
              <line x1="12" y1="8" x2="12" y2="12" />
              <line x1="12" y1="16" x2="12.01" y2="16" />
            </svg>
            <span>{error}</span>
          </div>
        )}
        <div
          ref={rootRef}
          className={`annotation-test-task__editor ${
            isLoading ? "annotation-test-task__editor--hidden" : ""
          }`}
        />
      </div>

      {/* Footer Actions */}
      <div className="annotation-test-task__footer">
        <div className="annotation-test-task__annotation-status">
          <div
            style={{
              fontSize: "10px",
              color: "#666",
              marginBottom: "4px",
              fontFamily: "monospace",
            }}
          >
            Debug: {annotation.length} result(s) |
            {annotation.length > 0
              ? JSON.stringify(annotation[0].value).substring(0, 50) + "..."
              : "Empty"}
          </div>
          {annotation.length > 0 ? (
            <span className="annotation-test-task__status--has-annotation">
              <svg
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
              >
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
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
            >
              <path d="M5 12h14M12 5l7 7-7 7" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
};
