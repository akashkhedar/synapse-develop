import React from "react";
import { useHistory, useLocation } from "react-router-dom";
import { Button } from "@synapse/ui";
import "./TestResult.css";

interface Result {
  passed: boolean;
  overall_score: number;
  total_possible: number;
  percentage: number;
  knowledge_score: number;
  knowledge_total: number;
  practical_score: number;
  practical_total: number;
  status: string;
  can_retake_at?: string;
  feedback?: string;
}

export const TestResult = () => {
  const history = useHistory();
  const location = useLocation<{ result: Result }>();
  const result = location.state?.result;

  const pct = (score: number, total: number) =>
    total > 0 ? (score / total) * 100 : 0;

  if (!result) {
    return (
      <div className="result-container">
        <div className="result-card">
          <h1>No Results Available</h1>
          <Button onClick={() => history.push("/annotators/test")}>
            Go to Test
          </Button>
        </div>
      </div>
    );
  }

  const {
    passed,
    overall_score,
    total_possible,
    percentage,
    knowledge_score,
    knowledge_total,
    practical_score,
    practical_total,
    can_retake_at,
    feedback,
  } = result;

  return (
    <div className="result-container">
      <div className="result-card">
        <div className={`result-icon ${passed ? "success" : "failed"}`}>
          {passed ? (
            <svg
              width="100"
              height="100"
              viewBox="0 0 24 24"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path
                d="M12 2C6.48 2 2 6.48 2 12C2 17.52 6.48 22 12 22C17.52 22 22 17.52 22 12C22 6.48 17.52 2 12 2ZM10 17L5 12L6.41 10.59L10 14.17L17.59 6.58L19 8L10 17Z"
                fill="#10b981"
              />
            </svg>
          ) : (
            <svg
              width="100"
              height="100"
              viewBox="0 0 24 24"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path
                d="M12 2C6.48 2 2 6.48 2 12C2 17.52 6.48 22 12 22C17.52 22 22 17.52 22 12C22 6.48 17.52 2 12 2ZM13 17H11V15H13V17ZM13 13H11V7H13V13Z"
                fill="#ef4444"
              />
            </svg>
          )}
        </div>

        <h1 className={passed ? "success-title" : "failed-title"}>
          {passed ? "Congratulations!" : "Test Not Passed"}
        </h1>

        <p className="result-subtitle">
          {passed
            ? "You have successfully passed the qualification test!"
            : "You did not meet the minimum passing criteria."}
        </p>

        <div className="score-overview">
          <div className="overall-score">
            <span className="score-label">Overall Score</span>
            <span className={`score-value ${passed ? "pass" : "fail"}`}>
              {overall_score} / {total_possible}
            </span>
            <span className="score-percentage">{percentage.toFixed(1)}%</span>
          </div>
        </div>

        <div className="score-breakdown">
          <h2>Score Breakdown</h2>

          <div className="breakdown-item">
            <div className="breakdown-header">
              <span className="breakdown-label">Medical Knowledge</span>
              <span className="breakdown-score">
                {knowledge_score} / {knowledge_total}
                <span className="breakdown-percentage">{`${pct}%`}</span>
              </span>
            </div>
            <div className="progress-bar">
              <div
                className={`progress-fill ${
                  knowledge_score / knowledge_total >= 0.6 ? "pass" : "fail"
                }`}
                style={{ width: `${pct}%` }}
              />
            </div>
            <span className="requirement-text">
              {knowledge_score / knowledge_total >= 0.6
                ? "✓ Passed"
                : "✗ Failed"}{" "}
              (Minimum: 60%)
            </span>
          </div>

          <div className="breakdown-item">
            <div className="breakdown-header">
              <span className="breakdown-label">Practical Tasks</span>
              <span className="breakdown-score">
                {practical_score} / {practical_total}
                <span className="breakdown-percentage">
                  ({((practical_score / practical_total) * 100).toFixed(1)}%)
                </span>
              </span>
            </div>
            <div className="progress-bar">
              <div
                className={`progress-fill ${
                  practical_score / practical_total >= 0.7 ? "pass" : "fail"
                }`}
                style={{
                  width: `${(practical_score / practical_total) * 100}%`,
                }}
              />
            </div>
            <span className="requirement-text">
              {practical_score / practical_total >= 0.7
                ? "✓ Passed"
                : "✗ Failed"}{" "}
              (Minimum: 70%)
            </span>
          </div>
        </div>

        {feedback && (
          <div className="feedback-section">
            <h3>Feedback</h3>
            <p>{feedback}</p>
          </div>
        )}

        <div className="next-steps">
          <h2>Next Steps</h2>
          {passed ? (
            <div className="success-steps">
              <div className="step-item">
                <div className="step-icon success">1</div>
                <div className="step-content">
                  <h3>Test Submitted</h3>
                  <p>Your test has been submitted for expert review</p>
                </div>
              </div>

              <div className="step-item">
                <div className="step-icon pending">2</div>
                <div className="step-content">
                  <h3>Under Review</h3>
                  <p>
                    Our experts will review your test answers within 24-48 hours
                  </p>
                </div>
              </div>

              <div className="step-item">
                <div className="step-icon pending">3</div>
                <div className="step-content">
                  <h3>Approval</h3>
                  <p>
                    Once approved, you can start working on annotation projects
                  </p>
                </div>
              </div>
            </div>
          ) : (
            <div className="failed-steps">
              <div className="retry-info">
                <svg
                  width="24"
                  height="24"
                  viewBox="0 0 24 24"
                  fill="none"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <path
                    d="M12 2C6.48 2 2 6.48 2 12C2 17.52 6.48 22 12 22C17.52 22 22 17.52 22 12C22 6.48 17.52 2 12 2ZM13 17H11V15H13V17ZM13 13H11V7H13V13Z"
                    fill="#f59e0b"
                  />
                </svg>
                <div>
                  <h3>Retake Opportunity</h3>
                  <p>You can retake the test after 7 days.</p>
                  {can_retake_at && (
                    <p className="retake-date">
                      Available from:{" "}
                      <strong>
                        {new Date(can_retake_at).toLocaleDateString()}
                      </strong>
                    </p>
                  )}
                </div>
              </div>

              <div className="study-tips">
                <h3>Preparation Tips</h3>
                <ul>
                  <li>Review medical terminology and common abbreviations</li>
                  <li>
                    Practice identifying medications, diseases, and symptoms in
                    clinical text
                  </li>
                  <li>Study HIPAA guidelines and data privacy basics</li>
                  <li>
                    Familiarize yourself with medical report classification
                  </li>
                </ul>
              </div>
            </div>
          )}
        </div>

        <div className="result-actions">
          <Button
            onClick={() => history.push("/projects/")}
            style={{ backgroundColor: "#3b82f6" }}
          >
            Go to Dashboard
          </Button>

          {passed && (
            <p className="notification-text">
              You will receive an email notification once your test is reviewed
            </p>
          )}
        </div>
      </div>
    </div>
  );
};

