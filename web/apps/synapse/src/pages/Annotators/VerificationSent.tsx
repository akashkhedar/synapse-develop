import React, { useState } from 'react';
import { useHistory, useLocation } from 'react-router-dom';
import { Button, useToast, ToastType } from '@synapse/ui';
import { Navbar } from '../../components/Navbar/Navbar';
import { Footer } from '../../components/Footer/Footer';
import './VerificationSent.css';

interface LocationState {
  email?: string;
}

export const VerificationSent = () => {
  const history = useHistory();
  const location = useLocation<LocationState>();
  const toast = useToast();
  const [resending, setResending] = useState(false);
  
  const email = location.state?.email || '';

  const handleResendVerification = async () => {
    if (!email) {
      toast?.show({
        message: 'Email not found. Please register again.',
        type: ToastType.error,
        duration: 3000,
      });
      return;
    }

    setResending(true);
    
    try {
      const response = await fetch('/api/annotators/resend-verification', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email }),
      });
      
      if (response.ok) {
        toast?.show({
          message: 'Verification email sent successfully!',
          type: ToastType.info,
          duration: 4000,
        });
      } else {
        const data = await response.json();
        toast?.show({
          message: data.error || 'Failed to resend email. Please try again.',
          type: ToastType.error,
          duration: 4000,
        });
      }
    } catch (error) {
      console.error('Resend error:', error);
      toast?.show({
        message: 'An error occurred. Please try again later.',
        type: ToastType.error,
        duration: 4000,
      });
    } finally {
      setResending(false);
    }
  };

  return (
    <>
      <Navbar />
      <div className="verification-sent-container">
        <div className="verification-sent-card">
        <div className="email-icon">
          <svg width="80" height="80" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M20 4H4C2.9 4 2 4.9 2 6V18C2 19.1 2.9 20 4 20H20C21.1 20 22 19.1 22 18V6C22 4.9 21.1 4 20 4ZM20 8L12 13L4 8V6L12 11L20 6V8Z" fill="#3b82f6"/>
          </svg>
        </div>
        
        <h1>Check Your Email</h1>
        <p className="subtitle">We've sent a verification link to</p>
        <p className="email-display">{email}</p>
        
        <div className="instructions">
          <div className="instruction-item">
            <span className="step-number">1</span>
            <span>Open your email inbox</span>
          </div>
          <div className="instruction-item">
            <span className="step-number">2</span>
            <span>Find the email from Synapse</span>
          </div>
          <div className="instruction-item">
            <span className="step-number">3</span>
            <span>Click the verification link</span>
          </div>
        </div>

        <div className="info-box">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 2C6.48 2 2 6.48 2 12C2 17.52 6.48 22 12 22C17.52 22 22 17.52 22 12C22 6.48 17.52 2 12 2ZM13 17H11V11H13V17ZM13 9H11V7H13V9Z" fill="#3b82f6"/>
          </svg>
          <span>The verification link will expire in 24 hours</span>
        </div>

        <div className="action-section">
          <p className="resend-text">Didn't receive the email?</p>
          <Button
            onClick={handleResendVerification}
            waiting={resending}
            disabled={resending}
            style={{ backgroundColor: '#3b82f6', width: '100%' }}
          >
            {resending ? 'Sending...' : 'Resend Verification Email'}
          </Button>
          
          <Button
            onClick={() => history.push('/annotators/signup')}
            style={{ backgroundColor: '#f3f4f6', color: '#374151', width: '100%', marginTop: '1rem' }}
          >
            Back to Signup
          </Button>
        </div>
      </div>
      </div>
      <Footer />
    </>
  );
};

