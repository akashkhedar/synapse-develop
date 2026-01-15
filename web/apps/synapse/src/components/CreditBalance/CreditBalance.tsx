import React, { useState, useEffect } from "react";
import { billingApi, OrganizationBilling } from "../../services/billingApi";
import "./CreditBalance.css";

interface CreditBalanceProps {
  onClick?: () => void;
}

export const CreditBalance: React.FC<CreditBalanceProps> = ({ onClick }) => {
  const [billing, setBilling] = useState<OrganizationBilling | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadBilling();
    // Refresh every 5 minutes (reduced from 30 seconds to decrease server load)
    const interval = setInterval(loadBilling, 300000);
    return () => clearInterval(interval);
  }, []);

  const loadBilling = async () => {
    try {
      const dashboard = await billingApi.getDashboard();
      setBilling(dashboard.billing);
    } catch (error) {
      console.error("Failed to load billing info:", error);
    } finally {
      setLoading(false);
    }
  };

  if (loading || !billing) {
    return (
      <div className="credit-balance-widget loading">
        <div className="credit-skeleton">
          <div className="skeleton-line short"></div>
          <div className="skeleton-line long"></div>
        </div>
      </div>
    );
  }

  const credits = billing.available_credits;
  const isLow = credits < 100;

  return (
    <div
      className={`credit-balance-widget ${isLow ? "low-balance" : ""}`}
      onClick={onClick}
      title="Click to view billing dashboard"
    >
      <div className="credit-icon">
        <svg
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <circle cx="12" cy="12" r="10" />
          <path d="M12 6v12M9 9h6M9 15h6" />
        </svg>
      </div>
      <div className="credit-info">
        <div className="credit-label">Credits</div>
        <div className="credit-amount">{credits.toLocaleString()}</div>
      </div>
      {isLow && <div className="low-badge">!</div>}
    </div>
  );
};
