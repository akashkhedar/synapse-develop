import { useEffect, useState } from "react";
import { useHistory, useLocation } from "react-router-dom";
import { Button, Spinner } from "@synapse/ui";
import { useAPI } from "../../providers/ApiProvider";
import { cn } from "../../utils/bem";

export const AcceptInvite = () => {
  const api = useAPI();
  const history = useHistory();
  const location = useLocation();
  const [isProcessing, setIsProcessing] = useState(true);
  const [error, setError] = useState(null);
  const [organization, setOrganization] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

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

  // Blog-inspired styles
  const pageStyle = {
    minHeight: '100vh',
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#000000',
    position: 'relative',
    overflow: 'hidden',
    fontFamily: "'Space Grotesk', system-ui, sans-serif",
  };

  const gridOverlayStyle = {
    position: 'absolute',
    inset: 0,
    opacity: 0.03,
    backgroundImage: `
      linear-gradient(to right, #ffffff 1px, transparent 1px),
      linear-gradient(to bottom, #ffffff 1px, transparent 1px)
    `,
    backgroundSize: '60px 60px',
    pointerEvents: 'none',
  };

  const containerStyle = {
    position: 'relative',
    zIndex: 10,
    maxWidth: '800px',
    width: '100%',
    padding: '0 24px',
    textAlign: 'center',
  };

  // "// INVITATION" style label
  const labelStyle = {
    color: '#6b7280', // gray-500
    fontFamily: 'ui-monospace, SF Mono, monospace',
    fontSize: '14px',
    letterSpacing: '0.05em',
    textTransform: 'uppercase',
    marginBottom: '24px',
    display: 'block',
  };

  const titleStyle = {
    fontSize: '48px', // md:text-6xl equivalent-ish
    fontWeight: 800,
    color: '#ffffff',
    lineHeight: 1.1,
    marginBottom: '32px',
    letterSpacing: '-0.02em',
  };

  const gradientTextStyle = {
    background: 'linear-gradient(to right, #c084fc, #db2777, #60a5fa)', // purple-400 via pink-400 to blue-400
    WebkitBackgroundClip: 'text',
    WebkitTextFillColor: 'transparent',
    backgroundClip: 'text',
    color: 'transparent',
  };

  const messageStyle = {
    fontSize: '18px',
    color: '#9ca3af', // gray-400
    fontFamily: 'ui-monospace, SF Mono, monospace',
    maxWidth: '600px',
    margin: '0 auto 40px auto',
    lineHeight: 1.6,
  };

  const buttonStyle = {
    background: '#ffffff',
    color: '#000000',
    border: 'none',
    padding: '0 32px',
    height: '48px',
    borderRadius: '4px',
    fontSize: '14px',
    fontWeight: 600,
    cursor: 'pointer',
    transition: 'transform 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
    fontFamily: 'ui-monospace, SF Mono, monospace',
    textTransform: 'uppercase',
    letterSpacing: '0.05em',
    display: 'inline-flex',
    alignItems: 'center',
    gap: '8px',
  };

  if (isProcessing) {
    return (
      <div style={pageStyle}>
        <div style={gridOverlayStyle} />
        <div style={containerStyle}>
          <span style={labelStyle}>// Processing</span>
          <h1 style={titleStyle}>
            Joining the <br />
            <span style={gradientTextStyle}>Organization</span>
          </h1>
          <div style={{ display: 'flex', justifyContent: 'center', marginTop: '32px' }}>
            <Spinner size={32} style={{ color: '#ffffff' }} />
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={pageStyle}>
        <div style={gridOverlayStyle} />
        <div style={containerStyle}>
          <span style={{ ...labelStyle, color: '#ef4444' }}>// Error</span>
          <h1 style={titleStyle}>
            Invitation <br />
            <span style={{ color: '#ef4444' }}>Expired or Invalid</span>
          </h1>
          <p style={messageStyle}>
            {error}
          </p>
          <button 
            onClick={() => history.push('/projects')}
            style={buttonStyle}
            onMouseEnter={(e) => e.currentTarget.style.transform = 'translateY(-2px)'}
            onMouseLeave={(e) => e.currentTarget.style.transform = 'translateY(0)'}
          >
            Return to Projects →
          </button>
        </div>
      </div>
    );
  }

  if (organization) {
    return (
      <div style={pageStyle}>
        <div style={gridOverlayStyle} />
        <div style={containerStyle}>
          <span style={labelStyle}>// Welcome Aboard</span>
          <h1 style={titleStyle}>
            You have joined <br />
            <span style={gradientTextStyle}>{organization.title}</span>
          </h1>
          <p style={messageStyle}>
            Access to shared projects, datasets, and team resources has been granted.
            Redirecting you to the workspace...
          </p>
          <div style={{ 
            marginTop: '24px',
            fontFamily: 'ui-monospace, SF Mono, monospace',
            fontSize: '12px',
            color: '#4b5563',
            textTransform: 'uppercase',
            letterSpacing: '0.1em'
          }}>
            Redirecting in 1.5s...
          </div>
        </div>
      </div>
    );
  }

  return null;
};

