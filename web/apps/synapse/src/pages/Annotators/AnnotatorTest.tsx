import React, { useEffect, useState } from "react";
import { useHistory } from "react-router-dom";
import { Button, useToast, ToastType } from "@synapse/ui";
import "./AnnotatorTest.css";

interface Question {
  id: number;
  type: string;
  question?: string;
  instruction?: string;
  text?: string;
  options?: string[];
  labels?: string[];
  correct_answer?: number;
  points: number;
}

interface TestData {
  knowledge_questions: Question[];
  text_annotation_tasks: Question[];
  classification_tasks: Question[];
  scoring_config: {
    time_limit_minutes: number;
    total_points: number;
  };
}

interface TextAnnotation {
  start: number;
  end: number;
  text: string;
  label: string;
}

export const AnnotatorTest = () => {
  const history = useHistory();
  const toast = useToast();

  const [testData, setTestData] = useState<TestData | null>(null);
  const [loading, setLoading] = useState(true);
  const [testStarted, setTestStarted] = useState(false);
  const [currentSection, setCurrentSection] = useState<
    "knowledge" | "text" | "classification"
  >("knowledge");
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [submitting, setSubmitting] = useState(false);

  // Answers
  const [mcqAnswers, setMcqAnswers] = useState<{ [key: number]: number }>({});
  const [textAnnotations, setTextAnnotations] = useState<{
    [key: number]: TextAnnotation[];
  }>({});
  const [classificationAnswers, setClassificationAnswers] = useState<{
    [key: number]: number;
  }>({});

  // Timer
  const [timeRemaining, setTimeRemaining] = useState(0);
  const [testAttemptId, setTestAttemptId] = useState<string | null>(null);

  useEffect(() => {
    const checkAuth = async () => {
      const res = await fetch("/api/annotators/auth-check", {
        credentials: "include",
      });
      const data = await res.json();

      if (!data.authenticated) {
        history.push("/annotators/login");
      }
    };

    checkAuth();
  }, []);

  useEffect(() => {
    fetchTestData();
  }, []);

  useEffect(() => {
    if (testStarted && timeRemaining > 0) {
      const timer = setInterval(() => {
        setTimeRemaining((prev) => {
          if (prev <= 1) {
            handleSubmit(true);
            return 0;
          }
          return prev - 1;
        });
      }, 1000);

      return () => clearInterval(timer);
    }
  }, [testStarted, timeRemaining]);

  const fetchTestData = async () => {
    try {
      const response = await fetch("/api/annotators/test/questions", {
        credentials: "include",
      });

      if (response.ok) {
        const data = await response.json();
        setTestData(data);
        setTimeRemaining(data.scoring_config.time_limit_minutes * 60);
      } else {
        toast?.show({
          message: "Failed to load test. Please try again.",
          type: ToastType.error,
          duration: 4000,
        });
      }
    } catch (error) {
      console.error("Test fetch error:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleStartTest = async () => {
    try {
      const response = await fetch("/api/annotators/test/start", {
        method: "POST",
        credentials: "include",
      });

      if (response.ok) {
        const data = await response.json();
        setTestAttemptId(data.attempt_id);
        setTestStarted(true);
      } else {
        toast?.show({
          message: "Failed to start test. Please try again.",
          type: ToastType.error,
          duration: 4000,
        });
      }
    } catch (error) {
      console.error("Test start error:", error);
    }
  };

  const handleMcqAnswer = (questionId: number, answerIndex: number) => {
    setMcqAnswers({ ...mcqAnswers, [questionId]: answerIndex });
  };

  const handleTextSelection = (taskId: number) => {
    const selection = window.getSelection();
    if (!selection || selection.toString().trim() === "") return;

    const range = selection.getRangeAt(0);
    const textElement = document.getElementById(`text-task-${taskId}`);

    if (!textElement) return;

    // Calculate start and end positions
    const preSelectionRange = range.cloneRange();
    preSelectionRange.selectNodeContents(textElement);
    preSelectionRange.setEnd(range.startContainer, range.startOffset);
    const start = preSelectionRange.toString().length;
    const end = start + range.toString().length;

    // Show label selection modal
    const label = prompt(
      "Enter label (MEDICATION, DISEASE, SYMPTOM, LOCATION, PROCEDURE, DOSAGE):"
    );
    if (!label) return;

    const annotation: TextAnnotation = {
      start,
      end,
      text: selection.toString(),
      label: label.toUpperCase(),
    };

    setTextAnnotations({
      ...textAnnotations,
      [taskId]: [...(textAnnotations[taskId] || []), annotation],
    });

    selection.removeAllRanges();
  };

  const removeAnnotation = (taskId: number, index: number) => {
    const updated = [...(textAnnotations[taskId] || [])];
    updated.splice(index, 1);
    setTextAnnotations({ ...textAnnotations, [taskId]: updated });
  };

  const handleClassificationAnswer = (taskId: number, answerIndex: number) => {
    setClassificationAnswers({
      ...classificationAnswers,
      [taskId]: answerIndex,
    });
  };

  const handleSubmit = async (force = false) => {
    if (submitting) return;
    setSubmitting(true);
    if (!testAttemptId) return;

    if (!force) {
      const confirmSubmit = window.confirm(
        "Are you sure you want to submit your test?"
      );
      if (!confirmSubmit) return;
    }

    try {
      const response = await fetch("/api/annotators/test/submit", {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          attempt_id: testAttemptId,
          mcq_answers: mcqAnswers,
          text_annotations: textAnnotations,
          classification_answers: classificationAnswers,
        }),
      });

      if (response.ok) {
        const result = await response.json();
        toast?.show({
          message: "Test submitted successfully!",
          type: ToastType.info,
          duration: 3000,
        });

        // Redirect to results page
        setTimeout(() => {
          history.push("/annotators/test-result", { result });
        }, 2000);
      } else {
        toast?.show({
          message: "Failed to submit test. Please try again.",
          type: ToastType.error,
          duration: 4000,
        });
      }
    } catch (error) {
      console.error("Test submit error:", error);
    }
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  };

  const getCurrentQuestion = () => {
    if (!testData) return null;

    switch (currentSection) {
      case "knowledge":
        return testData.knowledge_questions[currentQuestionIndex];
      case "text":
        return testData.text_annotation_tasks[currentQuestionIndex];
      case "classification":
        return testData.classification_tasks[currentQuestionIndex];
    }
  };

  const getTotalQuestionsInSection = () => {
    if (!testData) return 0;

    switch (currentSection) {
      case "knowledge":
        return testData.knowledge_questions.length;
      case "text":
        return testData.text_annotation_tasks.length;
      case "classification":
        return testData.classification_tasks.length;
    }
  };

  const handleNext = () => {
    const total = getTotalQuestionsInSection();

    if (currentQuestionIndex < total - 1) {
      setCurrentQuestionIndex(currentQuestionIndex + 1);
    } else {
      // Move to next section
      if (currentSection === "knowledge") {
        setCurrentSection("text");
        setCurrentQuestionIndex(0);
      } else if (currentSection === "text") {
        setCurrentSection("classification");
        setCurrentQuestionIndex(0);
      }
    }
  };

  const handlePrevious = () => {
    if (currentQuestionIndex > 0) {
      setCurrentQuestionIndex(currentQuestionIndex - 1);
    } else {
      // Move to previous section
      if (currentSection === "classification") {
        setCurrentSection("text");
        setCurrentQuestionIndex(testData!.text_annotation_tasks.length - 1);
      } else if (currentSection === "text") {
        setCurrentSection("knowledge");
        setCurrentQuestionIndex(testData!.knowledge_questions.length - 1);
      }
    }
  };

  const isLastQuestion = () => {
    return (
      currentSection === "classification" &&
      currentQuestionIndex === getTotalQuestionsInSection() - 1
    );
  };

  if (loading) {
    return (
      <div className="test-container">
        <div className="loading-spinner">
          <div className="spinner"></div>
        </div>
        <p>Loading test...</p>
      </div>
    );
  }

  if (!testStarted) {
    return (
      <div className="test-container">
        <div className="test-intro-card">
          <h1>Annotator Qualification Test</h1>
          <p className="test-intro-subtitle">
            Complete this test to qualify for medical data annotation projects
          </p>

          <div className="test-info-section">
            <h2>Test Structure</h2>
            <div className="test-info-grid">
              <div className="info-card">
                <div className="info-icon">📝</div>
                <h3>Medical Knowledge</h3>
                <p>10 multiple choice questions</p>
                <span className="points">22 points</span>
              </div>

              <div className="info-card">
                <div className="info-icon">🔍</div>
                <h3>Text Annotation</h3>
                <p>3 clinical text labeling tasks</p>
                <span className="points">45 points</span>
              </div>

              <div className="info-card">
                <div className="info-icon">📊</div>
                <h3>Classification</h3>
                <p>3 medical report classification tasks</p>
                <span className="points">30 points</span>
              </div>
            </div>
          </div>

          <div className="test-requirements">
            <h2>Requirements</h2>
            <ul>
              <li>
                ⏱️ Time Limit: {testData?.scoring_config.time_limit_minutes}{" "}
                minutes
              </li>
              <li>✅ Minimum Score: 70% overall</li>
              <li>📋 Medical Knowledge: Minimum 60%</li>
              <li>🎯 Practical Tasks: Minimum 70%</li>
              <li>⚠️ Test will auto-submit when time expires</li>
              <li>🔄 You can retake the test after 7 days if you don't pass</li>
            </ul>
          </div>

          <div className="test-instructions">
            <h2>Instructions</h2>
            <ol>
              <li>Read each question carefully before answering</li>
              <li>
                For text annotation tasks, select the text and enter the
                appropriate label
              </li>
              <li>
                You can navigate between questions using Previous/Next buttons
              </li>
              <li>Make sure to answer all questions before submitting</li>
              <li>Once submitted, you cannot change your answers</li>
            </ol>
          </div>

          <Button
            onClick={handleStartTest}
            style={{
              backgroundColor: "#10b981",
              padding: "16px 48px",
              fontSize: "18px",
              marginTop: "24px",
            }}
          >
            Start Test
          </Button>
        </div>
      </div>
    );
  }

  const currentQuestion = getCurrentQuestion();
  if (!currentQuestion || !testData) return null;

  return (
    <div className="test-container">
      <div className="test-header">
        <div className="test-progress">
          <span className="section-name">
            {currentSection === "knowledge" && "Medical Knowledge"}
            {currentSection === "text" && "Text Annotation"}
            {currentSection === "classification" && "Classification"}
          </span>
          <span className="question-counter">
            Question {currentQuestionIndex + 1} of{" "}
            {getTotalQuestionsInSection()}
          </span>
        </div>

        <div className={`timer ${timeRemaining < 300 ? "warning" : ""}`}>
          <svg
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path
              d="M12 2C6.48 2 2 6.48 2 12C2 17.52 6.48 22 12 22C17.52 22 22 17.52 22 12C22 6.48 17.52 2 12 2ZM13 13H11V7H13V13Z"
              fill="currentColor"
            />
          </svg>
          {formatTime(timeRemaining)}
        </div>
      </div>

      <div className="test-content">
        {/* MCQ Questions */}
        {currentSection === "knowledge" && currentQuestion.type === "mcq" && (
          <div className="question-card">
            <h2 className="question-text">{currentQuestion.question}</h2>
            <div className="options-list">
              {currentQuestion.options?.map((option, index) => (
                <div
                  key={index}
                  className={`option-item ${
                    mcqAnswers[currentQuestion.id] === index ? "selected" : ""
                  }`}
                  onClick={() => handleMcqAnswer(currentQuestion.id, index)}
                >
                  <div className="option-radio">
                    {mcqAnswers[currentQuestion.id] === index && (
                      <div className="radio-selected" />
                    )}
                  </div>
                  <span>{option}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Text Annotation Tasks */}
        {currentSection === "text" && currentQuestion.type === "ner" && (
          <div className="question-card">
            <h2 className="instruction-text">{currentQuestion.instruction}</h2>

            <div className="labels-info">
              <strong>Available Labels:</strong>
              {currentQuestion.labels?.map((label) => (
                <span key={label} className="label-badge">
                  {label}
                </span>
              ))}
            </div>

            <div className="annotation-help">
              💡 Select text with your mouse and enter the label when prompted
            </div>

            <div
              id={`text-task-${currentQuestion.id}`}
              className="annotation-text"
              onMouseUp={() => handleTextSelection(currentQuestion.id)}
            >
              {currentQuestion.text}
            </div>

            <div className="annotations-list">
              <h3>
                Your Annotations (
                {textAnnotations[currentQuestion.id]?.length || 0})
              </h3>
              {textAnnotations[currentQuestion.id]?.map((annotation, index) => (
                <div key={index} className="annotation-item">
                  <span className="annotation-text">"{annotation.text}"</span>
                  <span
                    className={`annotation-label label-${annotation.label.toLowerCase()}`}
                  >
                    {annotation.label}
                  </span>
                  <button
                    className="remove-btn"
                    onClick={() => removeAnnotation(currentQuestion.id, index)}
                  >
                    ✕
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Classification Tasks */}
        {currentSection === "classification" &&
          currentQuestion.type === "classification" && (
            <div className="question-card">
              <h2 className="instruction-text">
                {currentQuestion.instruction}
              </h2>

              <div className="case-text">{currentQuestion.text}</div>

              <div className="options-list">
                {currentQuestion.options?.map((option, index) => (
                  <div
                    key={index}
                    className={`option-item ${
                      classificationAnswers[currentQuestion.id] === index
                        ? "selected"
                        : ""
                    }`}
                    onClick={() =>
                      handleClassificationAnswer(currentQuestion.id, index)
                    }
                  >
                    <div className="option-radio">
                      {classificationAnswers[currentQuestion.id] === index && (
                        <div className="radio-selected" />
                      )}
                    </div>
                    <span>{option}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
      </div>

      <div className="test-footer">
        <Button
          onClick={handlePrevious}
          disabled={
            currentSection === "knowledge" && currentQuestionIndex === 0
          }
          style={{ backgroundColor: "#6b7280" }}
        >
          Previous
        </Button>

        <div className="footer-center">
          <span className="points-info">{currentQuestion.points} points</span>
        </div>

        {!isLastQuestion() ? (
          <Button onClick={handleNext} style={{ backgroundColor: "#3b82f6" }}>
            Next
          </Button>
        ) : (
          <Button
            onClick={() => handleSubmit()}
            style={{ backgroundColor: "#10b981" }}
          >
            Submit Test
          </Button>
        )}
      </div>
    </div>
  );
};

