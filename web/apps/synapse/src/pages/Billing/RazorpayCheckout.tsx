import React, { useEffect, useState } from 'react';
import { billingApi, CreateOrderResponse } from '../../services/billingApi';
import './RazorpayCheckout.css';

interface RazorpayCheckoutProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  itemId: number;
  itemType: 'subscription' | 'credits';
}

// Declare Razorpay on window object
declare global {
  interface Window {
    Razorpay: any;
  }
}

export const RazorpayCheckout: React.FC<RazorpayCheckoutProps> = ({
  isOpen,
  onClose,
  onSuccess,
  itemId,
  itemType,
}) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [orderDetails, setOrderDetails] = useState<CreateOrderResponse | null>(null);
  const [razorpayKey, setRazorpayKey] = useState<string>('');
  const [testMode, setTestMode] = useState<boolean>(false);

  // Fetch Razorpay key on mount
  useEffect(() => {
    const fetchKey = async () => {
      try {
        const config = await billingApi.getRazorpayKey();
        setRazorpayKey(config.key_id);
        setTestMode(config.test_mode);
      } catch (err) {
        console.error('Failed to fetch Razorpay key:', err);
      }
    };
    fetchKey();
  }, []);

  useEffect(() => {
    // Load Razorpay script
    if (isOpen && !window.Razorpay) {
      const script = document.createElement('script');
      script.src = 'https://checkout.razorpay.com/v1/checkout.js';
      script.async = true;
      script.onload = () => {
        console.log('Razorpay script loaded');
      };
      document.body.appendChild(script);

      return () => {
        document.body.removeChild(script);
      };
    }
  }, [isOpen]);

  useEffect(() => {
    if (isOpen && razorpayKey) {
      createOrder();
    }
  }, [isOpen, itemId, itemType, razorpayKey]);

  const createOrder = async () => {
    try {
      setLoading(true);
      setError(null);

      const orderData = itemType === 'subscription'
        ? { payment_for: 'subscription' as const, subscription_plan_id: itemId }
        : { payment_for: 'credits' as const, credit_package_id: itemId };

      const order = await billingApi.createOrder(orderData);
      setOrderDetails(order);
      
      // Open Razorpay checkout after order is created
      setTimeout(() => openRazorpayCheckout(order), 500);
    } catch (err: any) {
      setError(err.message || 'Failed to create order');
      setLoading(false);
    }
  };

  const openRazorpayCheckout = (order: CreateOrderResponse) => {
    if (!window.Razorpay) {
      setError('Payment gateway not loaded. Please refresh and try again.');
      setLoading(false);
      return;
    }

    if (!razorpayKey) {
      setError('Payment configuration error. Please refresh and try again.');
      setLoading(false);
      return;
    }

    const options: any = {
      key: razorpayKey,
      name: 'Synapse',
      description: order.description,
      order_id: order.order_id,
      handler: async function (response: any) {
        await handlePaymentSuccess(response);
      },
      prefill: {
        // Only set if we have user info, otherwise let Razorpay ask
      },
      theme: {
        color: '#4299e1',
      },
      modal: {
        ondismiss: function () {
          setLoading(false);
          onClose();
        },
        confirm_close: true,
      },
      retry: {
        enabled: true,
        max_count: 3,
      },
    };

    // Add customer_id if present to link payment to the customer
    if (order.customer_id) {
      options.customer_id = order.customer_id;
    }

    const razorpayInstance = new window.Razorpay(options);
    razorpayInstance.open();
    setLoading(false);
  };

  const handlePaymentSuccess = async (response: any) => {
    try {
      console.log('Razorpay payment success:', response);
      setLoading(true);
      
      await billingApi.verifyPayment({
        razorpay_order_id: response.razorpay_order_id,
        razorpay_payment_id: response.razorpay_payment_id,
        razorpay_signature: response.razorpay_signature,
      });

      console.log('Payment verification successful');
      // Success!
      onSuccess();
      onClose();
    } catch (err: any) {
      console.error('Payment verification failed:', err);
      setError(err.message || 'Payment verification failed');
      // alerts are bad UX usually but helpful for debugging right now
      alert(`Payment verification failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="razorpay-modal-overlay">
      <div className="razorpay-modal">
        <div className="razorpay-modal-header">
          <h2>Complete Payment</h2>
          <button className="close-btn" onClick={onClose} disabled={loading}>
            ×
          </button>
        </div>

        <div className="razorpay-modal-body">
          {loading && (
            <div className="loading-state">
              <div className="spinner"></div>
              <p>Processing your payment...</p>
            </div>
          )}

          {error && (
            <div className="error-state">
              <div className="error-icon">⚠️</div>
              <h3>Payment Error</h3>
              <p>{error}</p>
              <button className="retry-btn" onClick={createOrder}>
                Retry Payment
              </button>
            </div>
          )}

          {!loading && !error && orderDetails && (
            <div className="order-summary">
              {testMode && (
                <div className="test-mode-banner" style={{
                  backgroundColor: '#fff3cd',
                  border: '1px solid #ffc107',
                  borderRadius: '4px',
                  padding: '12px',
                  marginBottom: '16px',
                  textAlign: 'center'
                }}>
                  <strong>🧪 TEST MODE</strong> - Use test card: 4111 1111 1111 1111, CVV: any 3 digits, Expiry: any future date
                </div>
              )}
              <h3>Order Summary</h3>
              <div className="summary-item">
                <span>Description:</span>
                <span>{orderDetails.description}</span>
              </div>
              <div className="summary-item total">
                <span>Total Amount:</span>
                <span className="amount">
                  ₹{(orderDetails.amount / 100).toLocaleString()}
                </span>
              </div>
              <p className="payment-note">
                Redirecting to Razorpay payment gateway...
              </p>
            </div>
          )}
        </div>

        <div className="razorpay-modal-footer">
          <div className="security-badges">
            <span className="badge">🔒 Secure Payment</span>
            <span className="badge">✓ SSL Encrypted</span>
          </div>
        </div>
      </div>
    </div>
  );
};

