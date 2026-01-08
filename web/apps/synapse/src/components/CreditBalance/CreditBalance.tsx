import React, { useState, useEffect } from 'react';
import { billingApi, OrganizationBilling } from '../../services/billingApi';
import './CreditBalance.css';

interface CreditBalanceProps {
  onClick?: () => void;
}

export const CreditBalance: React.FC<CreditBalanceProps> = ({ onClick }) => {
  const [billing, setBilling] = useState<OrganizationBilling | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadBilling();
    // Refresh every 30 seconds
    const interval = setInterval(loadBilling, 30000);
    return () => clearInterval(interval);
  }, []);

  const loadBilling = async () => {
    try {
      const dashboard = await billingApi.getDashboard();
      setBilling(dashboard.billing);
    } catch (error) {
      console.error('Failed to load billing info:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading || !billing) {
    return (
      <div className="credit-balance-widget loading">
        <div className="loading-spinner"></div>
      </div>
    );
  }

  const credits = billing.available_credits;
  const isLow = credits < 100;

  return (
    <div 
      className={`credit-balance-widget ${isLow ? 'low-balance' : ''}`}
      onClick={onClick}
      title="Click to view billing dashboard"
    >
      <div className="credit-icon">💰</div>
      <div className="credit-info">
        <div className="credit-label">Credits</div>
        <div className="credit-amount">{credits.toLocaleString()}</div>
      </div>
      {isLow && <div className="low-badge">!</div>}
    </div>
  );
};

