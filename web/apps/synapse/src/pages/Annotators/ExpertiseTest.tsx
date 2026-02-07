import React, { useEffect, useState, useCallback, useRef } from "react";
import { useHistory, useLocation } from "react-router-dom";
import { useToast, ToastType, Spinner } from "@synapse/ui";
import {
  AnnotationTestTask,
  TestResultsDisplay,
} from "./components";
import {
  getTestCasesForSpecialties,
  getEstimatedTime,
  type TestCase,
  type AnnotationResult,
} from "./data/testCases";
import { calculateTestResults, type TestResult } from "./data/scoring";
import "./AnnotatorSkillTest.css"; // Reuse the same styles

type TestPhase = "loading" | "instructions" | "testing" | "results" | "error";

interface ExpertiseInfo {
  id: number;
  category_name: string;
  category_slug: string;
  specialization_name: string | null;
  specialization_slug: string | null;
  annotator_name: string;
  test_attempts: number;
}

export const ExpertiseTest: React.FC & { title?: string; path?: string; exact?: boolean } = () => {
  const history = useHistory();
  const location = useLocation();
  const toast = useToast();

  // Get token from URL
  const searchParams = new URLSearchParams(location.search);
  const token = searchParams.get("token");

  // Test state
  const [phase, setPhase] = useState<TestPhase>("loading");
  const [expertiseInfo, setExpertiseInfo] = useState<ExpertiseInfo | null>(null);
  const [passingScore, setPassingScore] = useState(70);
  const [testCases, setTestCases] = useState<TestCase[]>([]);
  const [currentTaskIndex, setCurrentTaskIndex] = useState(0);
  const answersRef = useRef<Map<string, AnnotationResult[]>>(new Map());
  const [testResult, setTestResult] = useState<TestResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string>("");

  // Timer
  const [timeRemaining, setTimeRemaining] = useState(0);
  const startTimeRef = useRef<number>(0);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  // Validate token and load expertise info
  useEffect(() => {
    const validateToken = async () => {
      if (!token) {
        setErrorMessage("No test token provided. Please use the link from your email.");
        setPhase("error");
        return;
      }

      try {
        const response = await fetch(`/api/annotators/expertise/test-by-token?token=${token}`, {
          credentials: "include",
        });

        const data = await response.json();

        if (!response.ok) {
          setErrorMessage(data.error || "Invalid or expired test link");
          setPhase("error");
          return;
        }

        setExpertiseInfo(data.expertise);
        
        // Set passing score from API
        if (data.passing_score) {
          setPassingScore(data.passing_score);
        }
        
        // Get test cases for this expertise
        const slug = data.expertise.specialization_slug || data.expertise.category_slug;
        const cases = getTestCasesForSpecialties([slug]);
        
        if (cases.length === 0) {
          // Fallback to category if no specific test cases
          const categoryCases = getTestCasesForSpecialties([data.expertise.category_slug]);
          if (categoryCases.length > 0) {
            setTestCases(categoryCases);
          } else {
            // Use generic test cases
            setTestCases(getTestCasesForSpecialties(["general"]));
          }
        } else {
          setTestCases(cases);
        }
        
        setPhase("instructions");
      } catch (error) {
        console.error("Token validation failed:", error);
        setErrorMessage("Failed to validate test link. Please try again.");
        setPhase("error");
      }
    };

    validateToken();
  }, [token]);

  // Timer effect
  useEffect(() => {
    if (phase === "testing" && timeRemaining > 0) {
      timerRef.current = setInterval(() => {
        setTimeRemaining((prev) => {
          if (prev <= 1) {
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

  // Start the test
  const handleStartTest = useCallback(() => {
    const estimatedMinutes = getEstimatedTime(testCases);
    setTimeRemaining(estimatedMinutes * 60);
    startTimeRef.current = Date.now();
    setPhase("testing");
  }, [testCases]);

  // Handle task completion
  const handleTaskComplete = useCallback(
    (result: AnnotationResult[]) => {
      const currentTask = testCases[currentTaskIndex];
      answersRef.current.set(currentTask.id, result);

      if (currentTaskIndex < testCases.length - 1) {
        setCurrentTaskIndex((prev) => prev + 1);
      } else {
        handleFinishTest();
      }
    },
    [currentTaskIndex, testCases]
  );

  // Finish the test and submit results
  const handleFinishTest = useCallback(async () => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
    }

    setIsLoading(true);

    try {
      const timeTaken = Math.floor((Date.now() - startTimeRef.current) / 1000);
      const results = calculateTestResults(testCases, answersRef.current, timeTaken);
      
      setTestResult(results);

      // Submit to backend
      const response = await fetch("/api/annotators/expertise/test/submit-by-token", {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          token,
          answers: Object.fromEntries(answersRef.current),
          time_taken: timeTaken,
          score: results.percentage,
          passed: results.passed,
        }),
      });

      const data = await response.json();

      if (response.ok) {
        if (data.badge_earned) {
          toast?.show({
            message: `🏆 Congratulations! You earned the ${data.expertise_name} badge!`,
            type: ToastType.info,
            duration: 8000,
          });
        }
      }

      setPhase("results");
    } catch (error) {
      console.error("Failed to submit test:", error);
      toast?.show({
        message: "Failed to submit test results",
        type: ToastType.error,
        duration: 3000,
      });
    } finally {
      setIsLoading(false);
    }
  }, [testCases, token, toast]);

  // Skip to next task
  const handleSkipTask = useCallback(() => {
    const currentTask = testCases[currentTaskIndex];
    answersRef.current.set(currentTask.id, []);

    if (currentTaskIndex < testCases.length - 1) {
      setCurrentTaskIndex((prev) => prev + 1);
    } else {
      handleFinishTest();
    }
  }, [currentTaskIndex, testCases, handleFinishTest]);

  // Handle retry
  const handleRetry = useCallback(() => {
    setCurrentTaskIndex(0);
    answersRef.current.clear();
    setTestResult(null);
    setPhase("instructions");
  }, []);

  // Handle continue - redirect to dashboard
  const handleContinue = useCallback(() => {
    // Redirect to login which will then redirect to earnings dashboard
    // This ensures proper Django session authentication
    window.location.href = "/login/?next=/annotator/earnings";
  }, []);

  // Render based on phase
  if (phase === "loading") {
    return (
      <div className="annotator-skill-test">
        <div className="test-instructions">
          <div className="test-instructions__content" style={{ textAlign: 'center' }}>
            <Spinner size={48} />
            <h2 style={{ color: '#fff', marginTop: '1rem' }}>Validating test link...</h2>
          </div>
        </div>
      </div>
    );
  }

  if (phase === "error") {
    return (
      <div className="annotator-skill-test">
        <div className="test-instructions">
          <div className="test-instructions__content" style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '4rem', marginBottom: '1rem' }}>❌</div>
            <h2 className="test-instructions__title">Unable to Start Test</h2>
            <p style={{ color: '#9ca3af', marginBottom: '2rem' }}>{errorMessage}</p>
            <button
              className="test-instructions__start"
              onClick={() => window.close()}
            >
              Close Window
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (phase === "instructions") {
    const expertiseName = expertiseInfo?.specialization_name || expertiseInfo?.category_name || "Expertise";
    return (
      <div className="annotator-skill-test">
        <div className="test-instructions">
          <div className="test-instructions__content">
            <div className="test-instructions__number">
              EXPERTISE QUALIFICATION TEST
            </div>
            <h1 className="test-instructions__title">
              {expertiseName}
            </h1>

            <div className="test-instructions__summary">
              <div className="test-instructions__summary-item">
                <span className="test-instructions__summary-label">Tasks</span>
                <span className="test-instructions__summary-value">{testCases.length}</span>
              </div>
              <div className="test-instructions__summary-item">
                <span className="test-instructions__summary-label">Time</span>
                <span className="test-instructions__summary-value">{getEstimatedTime(testCases)} min</span>
              </div>
              <div className="test-instructions__summary-item">
                <span className="test-instructions__summary-label">Passing</span>
                <span className="test-instructions__summary-value">{passingScore}%</span>
              </div>
            </div>

            <div className="test-instructions__rules">
              <h3>Test Guidelines</h3>
              <ul>
                <li>
                  <span className="test-instructions__rule-icon">✓</span>
                  Complete all annotation tasks to the best of your ability
                </li>
                <li>
                  <span className="test-instructions__rule-icon">✓</span>
                  You must score at least {passingScore}% to earn your expertise badge
                </li>
                <li>
                  <span className="test-instructions__rule-icon">✓</span>
                  The timer starts when you click "Start Test"
                </li>
                <li>
                  <span className="test-instructions__rule-icon">✓</span>
                  You can skip tasks but they will count as incorrect
                </li>
              </ul>
            </div>

            <div className="test-instructions__actions">
              <button
                className="test-instructions__back"
                onClick={() => window.close()}
              >
                ← Close
              </button>
              <button
                className="test-instructions__start"
                onClick={handleStartTest}
                disabled={testCases.length === 0 || isLoading}
              >
                {isLoading ? "Loading..." : "Start Test →"}
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (phase === "testing") {
    const currentTestCase = testCases[currentTaskIndex];
    return (
      <div className="annotator-skill-test">
        <AnnotationTestTask
          key={currentTestCase.id}
          testCase={currentTestCase}
          onComplete={handleTaskComplete}
          onSkip={handleSkipTask}
          taskNumber={currentTaskIndex + 1}
          totalTasks={testCases.length}
          timeRemaining={timeRemaining}
        />
      </div>
    );
  }

  if (phase === "results" && testResult) {
    return (
      <div className="annotator-skill-test">
        <TestResultsDisplay
          result={testResult}
          onRetry={handleRetry}
          onContinue={handleContinue}
        />
      </div>
    );
  }

  return null;
};
