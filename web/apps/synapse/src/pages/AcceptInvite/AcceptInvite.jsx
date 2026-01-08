import { useEffect, useState } from "react";
import { useHistory, useLocation } from "react-router-dom";
import { Button, Spinner } from "@synapse/ui";
import { useAPI } from "../../providers/ApiProvider";
import { cn } from "../../utils/bem";
import "./AcceptInvite.scss";

export const AcceptInvite = () => {
  const api = useAPI();
  const history = useHistory();
  const location = useLocation();
  const [isProcessing, setIsProcessing] = useState(true);
  const [error, setError] = useState(null);
  const [organization, setOrganization] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  const rootClass = cn("accept-invite");
  // Parse token from query string
  const queryParams = new URLSearchParams(location.search);
  const token = queryParams.get("token");

  useEffect(() => {
    checkAuthAndProcessInvite();
  }, [token]);

  const checkAuthAndProcessInvite = async () => {
    if (!token) {
      setError("Invalid invitation link - no token provided");
      setIsProcessing(false);
      return;
    }

    try {
      // Check if user is logged in
      const userResponse = await api.callApi("me");
      
      if (userResponse && userResponse.id) {
        // User is logged in, accept the invite
        setIsAuthenticated(true);
        await acceptInvite(token);
      } else {
        // User is not logged in, redirect to signup with token
        setIsAuthenticated(false);
        setIsProcessing(false);
        // Redirect to signup page with token
        window.location.href = `/user/signup?token=${token}`;
      }
    } catch (error) {
      console.error("Error checking authentication:", error);
      // If API call fails, assume not authenticated and redirect to signup
      setIsAuthenticated(false);
      setIsProcessing(false);
      window.location.href = `/user/signup?token=${token}`;
    }
  };

  const acceptInvite = async (inviteToken) => {
    try {
      const response = await fetch('/api/invite/accept', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          token: inviteToken,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.error || `Failed to accept invite: ${response.status}`);
      }

      const org = await response.json();
      setOrganization(org);
      
      // Wait a moment to show success message, then redirect
      setTimeout(() => {
        window.location.replace('/projects');
      }, 1500);
    } catch (error) {
      console.error("Failed to accept invite:", error);
      setError(error.message || "Failed to accept invitation. The link may be invalid or expired.");
      setIsProcessing(false);
    }
  };

  if (isProcessing) {
    return (
      <div className={rootClass.toString()}>
        <div className={rootClass.elem("container")}>
          <Spinner size={48} className={rootClass.elem("spinner")} />
          <h2 className={rootClass.elem("title")}>Processing Invitation...</h2>
          <p className={rootClass.elem("message")}>
            {isAuthenticated 
              ? "Adding you to the organization..." 
              : "Checking your account..."}
          </p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={rootClass.toString()}>
        <div className={rootClass.elem("container")}>
          <div className={rootClass.elem("error-icon")}>⚠️</div>
          <h2 className={rootClass.elem("title")}>Invitation Error</h2>
          <p className={rootClass.elem("error")}>{error}</p>
          <div className={rootClass.elem("actions")}>
            <Button onClick={() => history.push('/projects')}>
              Go to Projects
            </Button>
          </div>
        </div>
      </div>
    );
  }

  if (organization) {
    return (
      <div className={rootClass.toString()}>
        <div className={rootClass.elem("container")}>
          <div className={rootClass.elem("success-icon")}>✓</div>
          <h2 className={rootClass.elem("title")}>Welcome!</h2>
          <p className={rootClass.elem("message")}>
            You've successfully joined <strong>{organization.title}</strong>
          </p>
          <p className={rootClass.elem("submessage")}>
            Redirecting to projects...
          </p>
        </div>
      </div>
    );
  }

  return null;
};

