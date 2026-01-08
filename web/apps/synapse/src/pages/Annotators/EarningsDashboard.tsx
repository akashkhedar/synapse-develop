import React, { useState, useEffect, useCallback } from "react";
import { useHistory } from "react-router-dom";
import { Button, useToast, ToastType } from "@synapse/ui";
import "./EarningsDashboard.css";

interface TrustLevel {
  level: string;
  multiplier: number;
  tasks_completed: number;
  accuracy_score: number;
  honeypot_pass_rate: number;
  total_honeypots: number;
  passed_honeypots: number;
  fraud_flags: number;
  is_suspended: boolean;
}

interface Transaction {
  id: number;
  type: string;
  stage: string | null;
  amount: number;
  balance_after: number;
  description: string;
  created_at: string;
}

interface EarningsSummary {
  total_tasks: number;
  total_earned: number;
  pending_approval: number;
  available_balance: number;
  total_withdrawn: number;
  weekly_earnings: number;
  monthly_earnings: number;
  trust_level: TrustLevel;
  recent_transactions: Transaction[];
}

const LEVEL_COLORS: Record<string, string> = {
  new: "#9e9e9e",
  junior: "#4caf50",
  regular: "#2196f3",
  senior: "#9c27b0",
  expert: "#ff9800",
};

const LEVEL_ICONS: Record<string, string> = {
  new: "🌱",
  junior: "⭐",
  regular: "🔷",
  senior: "💎",
  expert: "👑",
};

export const EarningsDashboard: React.FC = () => {
  const history = useHistory();
  const toast = useToast();

  const [loading, setLoading] = useState(true);
  const [summary, setSummary] = useState<EarningsSummary | null>(null);
  const [activeTab, setActiveTab] = useState<
    "overview" | "transactions" | "trust"
  >("overview");

  const fetchEarnings = useCallback(async () => {
    try {
      const response = await fetch("/api/annotators/earnings", {
        credentials: "include",
      });

      if (response.status === 403) {
        history.push("/annotators/login");
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

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString("en-IN", {
      day: "numeric",
      month: "short",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  if (loading) {
    return (
      <div className="earnings-loading">
        <div className="spinner" />
        <p>Loading earnings...</p>
      </div>
    );
  }

  if (!summary) {
    return (
      <div className="earnings-error">
        <h2>Unable to load earnings</h2>
        <Button onClick={fetchEarnings}>Retry</Button>
      </div>
    );
  }

  return (
    <div className="earnings-dashboard">
      <header className="earnings-header">
        <h1>💰 My Earnings</h1>
        <Button onClick={() => history.push("/annotators/payouts")}>
          Request Payout
        </Button>
      </header>

      {/* Balance Cards */}
      <div className="balance-cards">
        <div className="balance-card available">
          <div className="balance-icon">💵</div>
          <div className="balance-info">
            <span className="balance-label">Available Balance</span>
            <span className="balance-amount">
              {formatCurrency(summary.available_balance)}
            </span>
          </div>
        </div>

        <div className="balance-card pending">
          <div className="balance-icon">⏳</div>
          <div className="balance-info">
            <span className="balance-label">Pending Approval</span>
            <span className="balance-amount">
              {formatCurrency(summary.pending_approval)}
            </span>
          </div>
        </div>

        <div className="balance-card total">
          <div className="balance-icon">📊</div>
          <div className="balance-info">
            <span className="balance-label">Total Earned</span>
            <span className="balance-amount">
              {formatCurrency(summary.total_earned)}
            </span>
          </div>
        </div>

        <div className="balance-card withdrawn">
          <div className="balance-icon">🏦</div>
          <div className="balance-info">
            <span className="balance-label">Total Withdrawn</span>
            <span className="balance-amount">
              {formatCurrency(summary.total_withdrawn)}
            </span>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="earnings-tabs">
        <button
          className={`tab ${activeTab === "overview" ? "active" : ""}`}
          onClick={() => setActiveTab("overview")}
        >
          📈 Overview
        </button>
        <button
          className={`tab ${activeTab === "transactions" ? "active" : ""}`}
          onClick={() => setActiveTab("transactions")}
        >
          📋 Transactions
        </button>
        <button
          className={`tab ${activeTab === "trust" ? "active" : ""}`}
          onClick={() => setActiveTab("trust")}
        >
          🏆 Trust Level
        </button>
      </div>

      {/* Tab Content */}
      <div className="tab-content">
        {activeTab === "overview" && (
          <div className="overview-section">
            <div className="stats-grid">
              <div className="stat-card">
                <span className="stat-value">{summary.total_tasks}</span>
                <span className="stat-label">Tasks Completed</span>
              </div>
              <div className="stat-card">
                <span className="stat-value">
                  {formatCurrency(summary.weekly_earnings)}
                </span>
                <span className="stat-label">This Week</span>
              </div>
              <div className="stat-card">
                <span className="stat-value">
                  {formatCurrency(summary.monthly_earnings)}
                </span>
                <span className="stat-label">This Month</span>
              </div>
              <div className="stat-card">
                <span className="stat-value">
                  {LEVEL_ICONS[summary.trust_level.level]}{" "}
                  {summary.trust_level.level}
                </span>
                <span className="stat-label">Trust Level</span>
              </div>
            </div>

            <div className="payment-info-card">
              <h3>💡 How Payments Work</h3>
              <div className="payment-stages">
                <div className="stage">
                  <div className="stage-percent">40%</div>
                  <div className="stage-name">Immediate</div>
                  <div className="stage-desc">Paid when you submit</div>
                </div>
                <div className="stage-arrow">→</div>
                <div className="stage">
                  <div className="stage-percent">40%</div>
                  <div className="stage-name">Consensus</div>
                  <div className="stage-desc">After quality check</div>
                </div>
                <div className="stage-arrow">→</div>
                <div className="stage">
                  <div className="stage-percent">20%</div>
                  <div className="stage-name">Review</div>
                  <div className="stage-desc">After expert review</div>
                </div>
              </div>
              <p className="multiplier-note">
                Your current trust multiplier:{" "}
                <strong>{summary.trust_level.multiplier}x</strong>
              </p>
            </div>
          </div>
        )}

        {activeTab === "transactions" && (
          <div className="transactions-section">
            <h3>Recent Transactions</h3>
            {summary.recent_transactions.length === 0 ? (
              <div className="no-transactions">
                <p>No transactions yet. Complete tasks to start earning!</p>
              </div>
            ) : (
              <div className="transactions-list">
                {summary.recent_transactions.map((tx) => (
                  <div key={tx.id} className={`transaction-item ${tx.type}`}>
                    <div className="tx-icon">
                      {tx.type === "earning" && "💰"}
                      {tx.type === "bonus" && "🎁"}
                      {tx.type === "penalty" && "⚠️"}
                      {tx.type === "withdrawal" && "🏦"}
                      {tx.type === "adjustment" && "🔧"}
                    </div>
                    <div className="tx-details">
                      <div className="tx-description">{tx.description}</div>
                      <div className="tx-meta">
                        {tx.stage && (
                          <span className="tx-stage">{tx.stage}</span>
                        )}
                        <span className="tx-date">
                          {formatDate(tx.created_at)}
                        </span>
                      </div>
                    </div>
                    <div
                      className={`tx-amount ${
                        tx.amount >= 0 ? "positive" : "negative"
                      }`}
                    >
                      {tx.amount >= 0 ? "+" : ""}
                      {formatCurrency(tx.amount)}
                    </div>
                  </div>
                ))}
              </div>
            )}
            <Button
              onClick={() => history.push("/annotators/transactions")}
              look="outlined"
            >
              View All Transactions
            </Button>
          </div>
        )}

        {activeTab === "trust" && (
          <div className="trust-section">
            <div
              className="trust-level-card"
              style={{ borderColor: LEVEL_COLORS[summary.trust_level.level] }}
            >
              <div className="level-badge">
                <span className="level-icon">
                  {LEVEL_ICONS[summary.trust_level.level]}
                </span>
                <span className="level-name">
                  {summary.trust_level.level.toUpperCase()}
                </span>
              </div>
              <div className="multiplier-display">
                <span className="multiplier-value">
                  {summary.trust_level.multiplier}x
                </span>
                <span className="multiplier-label">Payment Multiplier</span>
              </div>
            </div>

            <div className="trust-stats">
              <div className="trust-stat">
                <span className="stat-label">Tasks Completed</span>
                <span className="stat-value">
                  {summary.trust_level.tasks_completed}
                </span>
              </div>
              <div className="trust-stat">
                <span className="stat-label">Accuracy Score</span>
                <span className="stat-value">
                  {summary.trust_level.accuracy_score.toFixed(1)}%
                </span>
              </div>
              <div className="trust-stat">
                <span className="stat-label">Honeypot Pass Rate</span>
                <span className="stat-value">
                  {summary.trust_level.honeypot_pass_rate.toFixed(1)}%
                </span>
              </div>
              <div className="trust-stat">
                <span className="stat-label">Quality Checks</span>
                <span className="stat-value">
                  {summary.trust_level.passed_honeypots}/
                  {summary.trust_level.total_honeypots}
                </span>
              </div>
            </div>

            {summary.trust_level.fraud_flags > 0 && (
              <div className="fraud-warning">
                ⚠️ You have {summary.trust_level.fraud_flags} quality flag(s).
                Maintain high quality to avoid account restrictions.
              </div>
            )}

            <div className="level-progression">
              <h4>Trust Level Progression</h4>
              <div className="levels-list">
                {["new", "junior", "regular", "senior", "expert"].map(
                  (level) => (
                    <div
                      key={level}
                      className={`level-item ${
                        level === summary.trust_level.level ? "current" : ""
                      }`}
                      style={{ borderColor: LEVEL_COLORS[level] }}
                    >
                      <span className="level-icon">{LEVEL_ICONS[level]}</span>
                      <span className="level-name">{level}</span>
                    </div>
                  )
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

