import React, { useState, useEffect } from "react";
import { useHistory } from "react-router-dom";
import { Button, useToast, ToastType } from "@synapse/ui";
import "./AnnotatorLogin.css";

export const AnnotatorLogin = () => {
  const history = useHistory();
  const toast = useToast();

  const [formData, setFormData] = useState({
    email: "",
    password: "",
  });

  const [loading, setLoading] = useState(false);
  const [checkingAuth, setCheckingAuth] = useState(true);

  // Check if annotator is already authenticated on component mount
  useEffect(() => {
    const checkAuthentication = async () => {
      try {
        const response = await fetch("/api/annotators/auth-check", {
          method: "GET",
          credentials: "include", // Include credentials to send session cookie
        });

        const data = await response.json();

        if (data.authenticated) {
          if (data.user) {
            localStorage.setItem("annotator_user", JSON.stringify(data.user));
          }
          history.push("/projects");
        } else {
          setCheckingAuth(false);
        }
      } catch (error) {
        // On error, show the login form
        setCheckingAuth(false);
      }
    };

    checkAuthentication();
  }, [history]);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData({ ...formData, [name]: value });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.email || !formData.password) {
      toast?.show({
        message: "Please enter both email and password",
        type: ToastType.error,
        duration: 3000,
      });
      return;
    }

    setLoading(true);

    try {
      const response = await fetch("/api/annotators/login", {
        method: "POST",
        credentials: "include", // CRITICAL: Include credentials to receive session cookie
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(formData),
      });

      const data = await response.json();

      if (response.ok) {
        // Store user info for RBAC
        localStorage.setItem("annotator_user", JSON.stringify(data.user));
        localStorage.setItem("user_role", "annotator");

        toast?.show({
          message: "Login successful! Welcome Annotator!",
          type: ToastType.info,
          duration: 2000,
        });

        // Redirect to projects page
        setTimeout(() => {
          history.push("/projects/");
        }, 500);
      } else {
        toast?.show({
          message:
            data.error ||
            data.detail ||
            "Login failed. Please check your credentials.",
          type: ToastType.error,
          duration: 4000,
        });
      }
    } catch (error) {
      console.error("Login error:", error);
      toast?.show({
        message: "An error occurred. Please try again later.",
        type: ToastType.error,
        duration: 4000,
      });
    } finally {
      setLoading(false);
    }
  };

  // Show loading state while checking authentication
  if (checkingAuth) {
    return (
      <div className="annotator-login-container">
        <div className="annotator-login-card">
          <div className="login-header">
            <p className="login-subtitle">Checking your authentication...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="annotator-login-container">
      <div className="annotator-login-card">
        <div className="login-header">
          <div className="login-icon">
            <svg
              width="60"
              height="60"
              viewBox="0 0 24 24"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path
                d="M12 2C6.48 2 2 6.48 2 12C2 17.52 6.48 22 12 22C17.52 22 22 17.52 22 12C22 6.48 17.52 2 12 2ZM12 5C13.66 5 15 6.34 15 8C15 9.66 13.66 11 12 11C10.34 11 9 9.66 9 8C9 6.34 10.34 5 12 5ZM12 19.2C9.5 19.2 7.29 17.92 6 15.98C6.03 13.99 10 12.9 12 12.9C13.99 12.9 17.97 13.99 18 15.98C16.71 17.92 14.5 19.2 12 19.2Z"
                fill="#3b82f6"
              />
            </svg>
          </div>
          <h1>Annotator / Expert Login</h1>
          <p className="login-subtitle">Welcome back! Sign in to continue.</p>
        </div>

        <form onSubmit={handleSubmit} className="login-form">
          <div className="form-group">
            <label htmlFor="email">Email Address</label>
            <input
              type="email"
              id="email"
              name="email"
              value={formData.email}
              onChange={handleInputChange}
              placeholder="your.email@example.com"
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              type="password"
              id="password"
              name="password"
              value={formData.password}
              onChange={handleInputChange}
              placeholder="Enter your password"
              required
            />
          </div>

          <Button
            type="submit"
            disabled={loading}
            style={{
              backgroundColor: "#3b82f6",
              width: "100%",
              padding: "14px",
              fontSize: "16px",
              marginTop: "8px",
            }}
          >
            {loading ? "Logging in..." : "Sign In"}
          </Button>
        </form>

        <div className="login-footer">
          <p>
            Don't have an account?{" "}
            <a
              href="/annotators/signup"
              onClick={(e) => {
                e.preventDefault();
                history.push("/annotators/signup");
              }}
            >
              Sign up
            </a>
          </p>
          <p className="help-text">
            Need help?{" "}
            <a href="mailto:support@Synapse.com">Contact Support</a>
          </p>
        </div>
      </div>
    </div>
  );
};

