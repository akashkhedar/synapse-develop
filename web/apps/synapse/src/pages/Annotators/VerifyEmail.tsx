import React, { useEffect, useState } from "react";
import { useHistory, useLocation } from "react-router-dom";
import { Button } from "@synapse/ui";
import { Navbar } from "../../components/Navbar/Navbar";
import { Footer } from "../../components/Footer/Footer";
import "./VerifyEmail.css";

export const VerifyEmail = () => {
  const history = useHistory();
  const location = useLocation();
  const [status, setStatus] = useState<"verifying" | "success" | "error">(
    "verifying"
  );
  const [errorMessage, setErrorMessage] = useState("");

  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const token = params.get("token");

    if (!token) {
      setStatus("error");
      setErrorMessage("Invalid verification link. No token found.");
      return;
    }

    verifyEmail(token);
  }, [location]);

  const verifyEmail = async (token: string) => {
    try {
      const response = await fetch("/api/annotators/verify-email", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ token }),
      });

      const data = await response.json();

      if (response.ok) {
        setStatus("success");

        // Redirect to dashboard after 3 seconds
        setTimeout(() => {
          history.push("/annotators/login/");
        }, 2000);
      } else {
        setStatus("error");
        setErrorMessage(data.error || "Verification failed. Please try again.");
      }
    } catch (error) {
      console.error("Verification error:", error);
      setStatus("error");
      setErrorMessage(
        "An error occurred during verification. Please try again."
      );
    }
  };

  return (
    <>
      <Navbar />
      <div className="verify-email-container">
        <div className="verify-email-card">
          {status === "verifying" && (
            <>
              <div className="loading-spinner">
                <div className="spinner"></div>
              </div>
              <h1>Verifying Your Email</h1>
              <p>Please wait while we verify your email address...</p>
            </>
          )}

          {status === "success" && (
            <>
              <div className="success-icon">
                <svg
                  width="80"
                  height="80"
                  viewBox="0 0 24 24"
                  fill="none"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <path
                    d="M12 2C6.48 2 2 6.48 2 12C2 17.52 6.48 22 12 22C17.52 22 22 17.52 22 12C22 6.48 17.52 2 12 2ZM10 17L5 12L6.41 10.59L10 14.17L17.59 6.58L19 8L10 17Z"
                    fill="#10b981"
                  />
                </svg>
              </div>
              <h1>Email Verified!</h1>
              <p>Your email has been successfully verified.</p>
              <p className="redirect-text">Redirecting to your test page...</p>
              <div className="progress-bar">
                <div className="progress-fill"></div>
              </div>
            </>
          )}

          {status === "error" && (
            <>
              <div className="error-icon">
                <svg
                  width="80"
                  height="80"
                  viewBox="0 0 24 24"
                  fill="none"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <path
                    d="M12 2C6.48 2 2 6.48 2 12C2 17.52 6.48 22 12 22C17.52 22 22 17.52 22 12C22 6.48 17.52 2 12 2ZM13 17H11V15H13V17ZM13 13H11V7H13V13Z"
                    fill="#ef4444"
                  />
                </svg>
              </div>
              <h1>Verification Failed</h1>
              <p className="error-message">{errorMessage}</p>
              <div className="error-actions">
                <Button
                  onClick={() => history.push("/annotators/signup")}
                  style={{ backgroundColor: "#3b82f6", width: "100%" }}
                >
                  Back to Signup
                </Button>
                <p className="contact-text">
                  Need help? Contact us at{" "}
                  <a href="mailto:support@Synapse.com">
                    support@Synapse.com
                  </a>
                </p>
              </div>
            </>
          )}
        </div>
      </div>
      <Footer />
    </>
  );
};

