import React, { useState, useEffect, useCallback } from "react";
import { useHistory } from "react-router-dom";
import { Button, useToast, ToastType } from "@synapse/ui";
import "./ExpertEarnings.css";

interface ExpertEarningsSummary {
  total_reviews: number;
  total_earned: number;
  pending_payout: number;
  available_balance: number;
  total_withdrawn: number;
  weekly_earnings: number;
  monthly_earnings: number;
  average_review_time: number;
  approval_rate: number;
  recent_transactions: Transaction[];
}

interface Transaction {
  id: number;
  type: string;
  amount: number;
  description: string;
  created_at: string;
  review_task_id?: number;
}

export const ExpertEarnings: React.FC = () => {
  const history = useHistory();
  const toast = useToast();

  const [loading, setLoading] = useState(true);
  const [summary, setSummary] = useState<ExpertEarningsSummary | null>(null);
  const [activeTab, setActiveTab] = useState<"overview" | "transactions">(
    "overview"
  );

  const fetchEarnings = useCallback(async () => {
    try {
      const response = await fetch("/api/annotators/expert/earnings", {
        credentials: "include",
      });

      if (response.status === 403) {
        history.push("/user/login");
        return;
      }

      const data = await response.json();
      setSummary(data);
    } catch (error) {
      console.error("Failed to fetch earnings:", error);
      toast?.show({
        message: "Failed to load earnings data",
        type: ToastType.error,
        duration: 3000,
      });
    } finally {
      setLoading(false);
    }
  }, [history, toast]);

  useEffect(() => {
    fetchEarnings();
  }, [fetchEarnings]);

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      minimumFractionDigits: 2,
    }).format(amount);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-IN", {
      day: "numeric",
      month: "short",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  if (loading) {
    return (
      <div className="expert-earnings-container">
        <div className="loading-spinner">
          <div className="spinner"></div>
          <p>Loading earnings...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="expert-earnings-container">
      <div className="earnings-header">
        <h1>Expert Earnings</h1>
        <p className="subtitle">Track your review earnings and payouts</p>
      </div>

      {/* Summary Cards */}
      <div className="summary-cards">
        <div className="summary-card available">
          <div className="card-icon">💰</div>
          <div className="card-content">
            <h3>Available Balance</h3>
            <p className="amount">
              {formatCurrency(summary?.available_balance || 0)}
            </p>
          </div>
          <Button
            look="filled"
            size="small"
            onClick={() => history.push("/expert/payouts")}
          >
            Request Payout
          </Button>
        </div>

        <div className="summary-card pending">
          <div className="card-icon">⏳</div>
          <div className="card-content">
            <h3>Pending Payout</h3>
            <p className="amount">
              {formatCurrency(summary?.pending_payout || 0)}
            </p>
          </div>
        </div>

        <div className="summary-card total">
          <div className="card-icon">💎</div>
          <div className="card-content">
            <h3>Total Earned</h3>
            <p className="amount">
              {formatCurrency(summary?.total_earned || 0)}
            </p>
          </div>
        </div>

        <div className="summary-card withdrawn">
          <div className="card-icon">✅</div>
          <div className="card-content">
            <h3>Total Withdrawn</h3>
            <p className="amount">
              {formatCurrency(summary?.total_withdrawn || 0)}
            </p>
          </div>
        </div>
      </div>

      {/* Stats Row */}
      <div className="stats-row">
        <div className="stat-item">
          <span className="stat-label">Total Reviews</span>
          <span className="stat-value">{summary?.total_reviews || 0}</span>
        </div>
        <div className="stat-item">
          <span className="stat-label">Approval Rate</span>
          <span className="stat-value">
            {(summary?.approval_rate || 0).toFixed(1)}%
          </span>
        </div>
        <div className="stat-item">
          <span className="stat-label">Avg Review Time</span>
          <span className="stat-value">
            {Math.round((summary?.average_review_time || 0) / 60)} min
          </span>
        </div>
        <div className="stat-item">
          <span className="stat-label">This Week</span>
          <span className="stat-value">
            {formatCurrency(summary?.weekly_earnings || 0)}
          </span>
        </div>
        <div className="stat-item">
          <span className="stat-label">This Month</span>
          <span className="stat-value">
            {formatCurrency(summary?.monthly_earnings || 0)}
          </span>
        </div>
      </div>

      {/* Tabs */}
      <div className="tabs">
        <button
          className={`tab ${activeTab === "overview" ? "active" : ""}`}
          onClick={() => setActiveTab("overview")}
        >
          Overview
        </button>
        <button
          className={`tab ${activeTab === "transactions" ? "active" : ""}`}
          onClick={() => setActiveTab("transactions")}
        >
          Transactions
        </button>
      </div>

      {/* Tab Content */}
      {activeTab === "overview" && (
        <div className="overview-content">
          <div className="info-card">
            <h3>How Expert Earnings Work</h3>
            <ul>
              <li>
                <strong>Per Review:</strong> You earn a fixed amount for each
                review completed
              </li>
              <li>
                <strong>Correction Bonus:</strong> Extra earnings when you
                correct annotations
              </li>
              <li>
                <strong>Quality Bonus:</strong> Monthly bonus based on review
                quality
              </li>
              <li>
                <strong>Payouts:</strong> Request payouts when your available
                balance exceeds ₹500
              </li>
            </ul>
          </div>
        </div>
      )}

      {activeTab === "transactions" && (
        <div className="transactions-content">
          <h3>Recent Transactions</h3>
          {summary?.recent_transactions &&
          summary.recent_transactions.length > 0 ? (
            <table className="transactions-table">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Type</th>
                  <th>Description</th>
                  <th>Amount</th>
                </tr>
              </thead>
              <tbody>
                {summary.recent_transactions.map((tx) => (
                  <tr key={tx.id}>
                    <td>{formatDate(tx.created_at)}</td>
                    <td>
                      <span className={`tx-type ${tx.type}`}>
                        {tx.type.replace(/_/g, " ")}
                      </span>
                    </td>
                    <td>{tx.description}</td>
                    <td
                      className={
                        tx.amount >= 0 ? "amount-positive" : "amount-negative"
                      }
                    >
                      {tx.amount >= 0 ? "+" : ""}
                      {formatCurrency(tx.amount)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <p className="no-transactions">No transactions yet</p>
          )}
        </div>
      )}
    </div>
  );
};

export default ExpertEarnings;

