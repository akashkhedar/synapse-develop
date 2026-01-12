import React, { useEffect, useState, useCallback, useRef } from "react";
import { useHistory } from "react-router-dom";
import { useToast, ToastType } from "@synapse/ui";
import { SpecialtySelection, AnnotationTestTask, TestResultsDisplay } from "./components";
import { getTestCasesForSpecialties, getEstimatedTime, type TestCase, type AnnotationResult } from "./data/testCases";
import { calculateTestResults, type TestResult } from "./data/scoring";
import "./AnnotatorSkillTest.css";

type TestPhase = "specialty-selection" | "instructions" | "testing" | "results";

export const AnnotatorSkillTest = () => {
  const history = useHistory();
  const toast = useToast();

  // Test state
  const [phase, setPhase] = useState<TestPhase>("specialty-selection");
  const [selectedSpecialties, setSelectedSpecialties] = useState<string[]>([]);
  const [testCases, setTestCases] = useState<TestCase[]>([]);
  const [currentTaskIndex, setCurrentTaskIndex] = useState(0);
  const [answers, setAnswers] = useState<Map<string, AnnotationResult[]>>(new Map());
  const [testResult, setTestResult] = useState<TestResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  // Timer
  const [timeRemaining, setTimeRemaining] = useState(0);
  const startTimeRef = useRef<number>(0);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  // Check authentication
  useEffect(() => {
    const checkAuth = async () => {
      try {
        const res = await fetch("/api/annotators/auth-check", {
          credentials: "include",
        });
        const data = await res.json();

        if (!data.authenticated) {
          history.push("/annotators/login");
        }
      } catch (error) {
        console.error("Auth check failed:", error);
      }
    };

    checkAuth();
  }, [history]);

  // Timer effect
  useEffect(() => {
    if (phase === "testing" && timeRemaining > 0) {
      timerRef.current = setInterval(() => {
        setTimeRemaining((prev) => {
          if (prev <= 1) {
            // Time's up - auto submit
            handleFinishTest();
            return 0;
          }
          return prev - 1;
        });
      }, 1000);

      return () => {
        if (timerRef.current) {
          clearInterval(timerRef.current);
        }
      };
    }
  }, [phase, timeRemaining]);

  // Cleanup timer on unmount
  useEffect(() => {
    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
  }, []);

  // Handle specialty selection confirmation
  const handleSpecialtyConfirm = useCallback((specialties: string[]) => {
    setSelectedSpecialties(specialties);
    const cases = getTestCasesForSpecialties(specialties);
    setTestCases(cases);
    
    // Calculate time (estimated time in minutes, convert to seconds)
    const estimatedMinutes = getEstimatedTime(cases);
    setTimeRemaining(estimatedMinutes * 60);
    
    setPhase("instructions");
  }, []);

  // Start the test
  const handleStartTest = useCallback(async () => {
    setIsLoading(true);
    
    try {
      // Optionally notify backend that test is starting
      const response = await fetch("/api/annotators/test/start", {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          specialties: selectedSpecialties,
          testCaseIds: testCases.map(tc => tc.id),
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to start test");
      }

      startTimeRef.current = Date.now();
      setPhase("testing");
    } catch (error) {
      // If API fails, still allow local testing
      console.warn("Could not notify server of test start:", error);
      startTimeRef.current = Date.now();
      setPhase("testing");
    } finally {
      setIsLoading(false);
    }
  }, [selectedSpecialties, testCases]);

  // Handle task completion
  const handleTaskComplete = useCallback((annotation: AnnotationResult[]) => {
    const currentTestCase = testCases[currentTaskIndex];
    
    setAnswers((prev) => {
      const newAnswers = new Map(prev);
      newAnswers.set(currentTestCase.id, annotation);
      return newAnswers;
    });

    // Move to next task or finish
    if (currentTaskIndex < testCases.length - 1) {
      setCurrentTaskIndex((prev) => prev + 1);
    } else {
      handleFinishTest();
    }
  }, [testCases, currentTaskIndex]);

  // Handle task skip
  const handleTaskSkip = useCallback(() => {
    if (currentTaskIndex < testCases.length - 1) {
      setCurrentTaskIndex((prev) => prev + 1);
    } else {
      handleFinishTest();
    }
  }, [testCases.length, currentTaskIndex]);

  // Finish test and calculate results
  const handleFinishTest = useCallback(async () => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
    }

    const timeTaken = Math.floor((Date.now() - startTimeRef.current) / 1000);
    const result = calculateTestResults(testCases, answers, timeTaken);
    setTestResult(result);

    // Submit results to backend
    try {
      await fetch("/api/annotators/test/submit", {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          specialties: selectedSpecialties,
          results: {
            ...result,
            taskScores: result.taskScores.map(ts => ({
              testCaseId: ts.testCaseId,
              specialty: ts.specialty,
              earnedPoints: ts.earnedPoints,
              maxPoints: ts.maxPoints,
              percentage: ts.percentage,
            })),
          },
        }),
      });
    } catch (error) {
      console.warn("Could not submit results to server:", error);
    }

    setPhase("results");
  }, [testCases, answers, selectedSpecialties]);

  // Handle retry
  const handleRetry = useCallback(() => {
    setPhase("specialty-selection");
    setSelectedSpecialties([]);
    setTestCases([]);
    setCurrentTaskIndex(0);
    setAnswers(new Map());
    setTestResult(null);
    setTimeRemaining(0);
  }, []);

  // Handle continue to dashboard
  const handleContinue = useCallback(() => {
    history.push("/annotators/earnings");
  }, [history]);

  // Render based on phase
  const renderPhase = () => {
    switch (phase) {
      case "specialty-selection":
        return (
          <SpecialtySelection
            onConfirm={handleSpecialtyConfirm}
            isLoading={isLoading}
          />
        );

      case "instructions":
        return (
          <div className="test-instructions">
            <div className="test-instructions__content">
              <div className="test-instructions__number">02/</div>
              <h1 className="test-instructions__title">Test Instructions</h1>
              
              <div className="test-instructions__summary">
                <div className="test-instructions__summary-item">
                  <span className="test-instructions__summary-label">Specialties</span>
                  <span className="test-instructions__summary-value">
                    {selectedSpecialties.length} selected
                  </span>
                </div>
                <div className="test-instructions__summary-item">
                  <span className="test-instructions__summary-label">Tasks</span>
                  <span className="test-instructions__summary-value">
                    {testCases.length} total
                  </span>
                </div>
                <div className="test-instructions__summary-item">
                  <span className="test-instructions__summary-label">Time Limit</span>
                  <span className="test-instructions__summary-value">
                    {Math.ceil(timeRemaining / 60)} minutes
                  </span>
                </div>
              </div>

              <div className="test-instructions__rules">
                <h3>Before you begin:</h3>
                <ul>
                  <li>
                    <span className="test-instructions__rule-icon">
                      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                        <circle cx="12" cy="12" r="10" />
                        <polyline points="12 6 12 12 16 14" />
                      </svg>
                    </span>
                    The timer starts once you click "Begin Test" and cannot be paused.
                  </li>
                  <li>
                    <span className="test-instructions__rule-icon">
                      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                        <polyline points="14 2 14 8 20 8" />
                        <line x1="16" y1="13" x2="8" y2="13" />
                        <line x1="16" y1="17" x2="8" y2="17" />
                      </svg>
                    </span>
                    Read each task carefully before annotating. Follow the instructions provided.
                  </li>
                  <li>
                    <span className="test-instructions__rule-icon">
                      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                        <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
                        <polyline points="22 4 12 14.01 9 11.01" />
                      </svg>
                    </span>
                    You must complete an annotation before submitting each task.
                  </li>
                  <li>
                    <span className="test-instructions__rule-icon">
                      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                        <polygon points="5 4 15 12 5 20 5 4" />
                        <line x1="19" y1="5" x2="19" y2="19" />
                      </svg>
                    </span>
                    You can skip tasks, but skipped tasks will receive 0 points.
                  </li>
                  <li>
                    <span className="test-instructions__rule-icon">
                      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                        <circle cx="12" cy="12" r="10" />
                        <circle cx="12" cy="12" r="6" />
                        <circle cx="12" cy="12" r="2" />
                      </svg>
                    </span>
                    You need at least 70% to pass. Try your best on each task!
                  </li>
                </ul>
              </div>

              <div className="test-instructions__actions">
                <button
                  type="button"
                  className="test-instructions__back"
                  onClick={() => setPhase("specialty-selection")}
                >
                  ← Back
                </button>
                <button
                  type="button"
                  className="test-instructions__start"
                  onClick={handleStartTest}
                  disabled={isLoading}
                >
                  {isLoading ? "Starting..." : "Begin Test"}
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M5 12h14M12 5l7 7-7 7" />
                  </svg>
                </button>
              </div>
            </div>
          </div>
        );

      case "testing":
        const currentTestCase = testCases[currentTaskIndex];
        return (
          <AnnotationTestTask
            key={currentTestCase.id}
            testCase={currentTestCase}
            onComplete={handleTaskComplete}
            onSkip={handleTaskSkip}
            taskNumber={currentTaskIndex + 1}
            totalTasks={testCases.length}
            timeRemaining={timeRemaining}
          />
        );

      case "results":
        return testResult ? (
          <TestResultsDisplay
            result={testResult}
            onRetry={handleRetry}
            onContinue={handleContinue}
          />
        ) : null;

      default:
        return null;
    }
  };

  return <div className="annotator-skill-test">{renderPhase()}</div>;
};

// Export for router
export default AnnotatorSkillTest;
