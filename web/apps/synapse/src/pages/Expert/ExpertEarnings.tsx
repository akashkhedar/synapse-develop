import React, { useState, useEffect, useCallback, useMemo } from "react";
import { useHistory } from "react-router-dom";
import { motion } from "framer-motion";
import { useToast, ToastType, Spinner } from "@synapse/ui";
import "./ExpertEarnings.css";

interface DailyEarning {
  date: string;
  amount: number;
}

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
  daily_earnings: DailyEarning[];
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

// Floating pixels decoration
const FloatingPixels = () => {
  const pixels = [
    { x: "5%", y: "15%", size: 3, opacity: 0.2 },
    { x: "90%", y: "30%", size: 4, opacity: 0.25 },
    { x: "12%", y: "75%", size: 3, opacity: 0.2 },
  ];
  
  return (
    <div className="floating-pixels">
      {pixels.map((p, i) => (
        <motion.div
          key={i}
          className="pixel"
          style={{ left: p.x, top: p.y, width: p.size, height: p.size, opacity: p.opacity }}
          animate={{ opacity: [p.opacity * 0.5, p.opacity, p.opacity * 0.5], scale: [0.9, 1, 0.9] }}
          transition={{ duration: 4 + Math.random() * 2, repeat: Infinity, ease: "linear" }}
        />
      ))}
    </div>
  );
};

export const ExpertEarnings: React.FC = () => {
  const history = useHistory();
  const toast = useToast();

  const [loading, setLoading] = useState(true);
  const [summary, setSummary] = useState<ExpertEarningsSummary | null>(null);
  console.log(summary);
  const [activeTab, setActiveTab] = useState<"overview" | "transactions">("overview");

  const fetchEarnings = useCallback(async () => {
    try {
      const response = await fetch("/api/annotators/expert/earnings", {
        credentials: "include",
      });

      if (response.status === 403) {
        history.push("/annotators/login");
        return;
      }
      
      if (response.status === 401) {
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
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffDays = Math.floor(diffMs / 86400000);
    
    if (diffDays === 0) return "Today";
    if (diffDays === 1) return "Yesterday";
    if (diffDays < 7) return `${diffDays}d ago`;
    
    return date.toLocaleDateString("en-IN", {
      day: "numeric",
      month: "short",
    });
  };

  // Chart data for earnings trend
  const chartData = useMemo(() => {
    if (!summary?.daily_earnings) return { bars: [], max: 0, avg: 0 };

    const earnings = summary.daily_earnings.slice(-14);
    const max = Math.max(...earnings.map((e) => e.amount), 1);
    const avg = earnings.reduce((sum, e) => sum + e.amount, 0) / (earnings.length || 1);

    const bars = earnings.map((e) => ({
      amount: e.amount,
      date: new Date(e.date),
      height: (e.amount / max) * 100,
      isAboveAvg: e.amount >= avg,
    }));

    return { bars, max, avg };
  }, [summary?.daily_earnings]);

  if (loading) {
    return (
      <div className="expert-earnings-page">
        <div className="earnings-loading">
          <Spinner size={64} />
          <span className="loader-text">Loading earnings...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="expert-earnings-page">
      <FloatingPixels />
      <div className="bg-grid" />
      <div className="bg-glow" />

      <div className="earnings-container">
        {/* Header */}
        <motion.header
          className="earnings-header"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <div className="header-left">
            <span className="header-tag">// EXPERT EARNINGS</span>
            <h1 className="header-title">Earnings</h1>
          </div>
          <div className="header-actions">
            <motion.button
              whileHover={{
                scale: 1.02,
                boxShadow: "0 0 30px rgba(34, 197, 94, 0.3)",
              }}
              whileTap={{ scale: 0.98 }}
              className="action-btn primary green"
              onClick={() => history.push("/expert/payouts")}
            >
              Request Payout →
            </motion.button>
          </div>
        </motion.header>

        {/* Balance Cards */}
        <motion.div
          className="balance-cards"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.1 }}
        >
          <div className="balance-card available">
            <div className="balance-label">AVAILABLE BALANCE</div>
            <div className="balance-value">
              {formatCurrency(summary?.available_balance || 0)}
            </div>
            <div className="balance-hint">Ready to withdraw</div>
          </div>
          <div className="balance-card pending">
            <div className="balance-label">PENDING PAYOUT</div>
            <div className="balance-value">
              {formatCurrency(summary?.pending_payout || 0)}
            </div>
            <div className="balance-hint">Processing</div>
          </div>
          <div className="balance-card total">
            <div className="balance-label">TOTAL EARNED</div>
            <div className="balance-value">
              {formatCurrency(summary?.total_earned || 0)}
            </div>
            <div className="balance-hint">Lifetime</div>
          </div>
          <div className="balance-card withdrawn">
            <div className="balance-label">WITHDRAWN</div>
            <div className="balance-value">
              {formatCurrency(summary?.total_withdrawn || 0)}
            </div>
            <div className="balance-hint">Paid out</div>
          </div>
        </motion.div>

        {/* Earnings Summary */}
        <motion.section
          className="section-card stats-section"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.2 }}
        >
          <div className="section-header">
            <span className="section-number">01/</span>
            <h2 className="section-title">Performance Stats</h2>
          </div>

          <div className="stats-grid">
            <div className="stat-item">
              <span className="stat-value">{summary?.total_reviews || 0}</span>
              <span className="stat-label">Total Reviews</span>
            </div>
            <div className="stat-item">
              <span className="stat-value accent">
                {formatCurrency(summary?.weekly_earnings || 0)}
              </span>
              <span className="stat-label">This Week</span>
            </div>
            <div className="stat-item">
              <span className="stat-value accent">
                {formatCurrency(summary?.monthly_earnings || 0)}
              </span>
              <span className="stat-label">This Month</span>
            </div>
          </div>
        </motion.section>

        {/* Earnings Trend Chart */}
        <motion.section
          className="section-card chart-section"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.25 }}
        >
          <div className="section-header">
            <span className="section-number">02/</span>
            <h2 className="section-title">Earnings Trend</h2>
            <span className="section-period">Last 14 days</span>
          </div>

          <div className="chart-wrapper">
            {/* Bar Chart */}
            <div className="bar-chart">
              {/* Average line */}
              {chartData.avg > 0 && (
                <div
                  className="avg-line"
                  style={{
                    bottom: `${(chartData.avg / chartData.max) * 100}%`,
                  }}
                >
                  <span className="avg-label">avg</span>
                </div>
              )}

              {/* Bars */}
              <div className="bars-container">
                {chartData.bars.map((bar, i) => (
                  <motion.div
                    key={i}
                    className="bar-wrapper"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: i * 0.03 }}
                  >
                    {/* Hover tooltip */}
                    <div className="bar-tooltip">
                      <span className="tooltip-date">
                        {bar.date.toLocaleDateString("en-US", {
                          month: "short",
                          day: "numeric",
                        })}
                      </span>
                      <span className="tooltip-amount">
                        {formatCurrency(bar.amount)}
                      </span>
                    </div>
                    <motion.div
                      className={`bar ${bar.isAboveAvg ? "above" : "below"}`}
                      initial={{ height: 0 }}
                      animate={{ height: `${bar.height}%` }}
                      transition={{
                        duration: 0.5,
                        delay: i * 0.03,
                        ease: "easeOut",
                      }}
                    />
                    <span className="bar-day">
                      {bar.date.toLocaleDateString("en-US", {
                        weekday: "narrow",
                      })}
                    </span>
                  </motion.div>
                ))}
              </div>
            </div>

            {/* Chart Stats */}
            <div className="chart-summary">
              <div className="summary-item">
                <span className="summary-label">THIS WEEK</span>
                <span className="summary-value">
                  {formatCurrency(summary?.weekly_earnings || 0)}
                </span>
              </div>
              <div className="summary-item">
                <span className="summary-label">THIS MONTH</span>
                <span className="summary-value">
                  {formatCurrency(summary?.monthly_earnings || 0)}
                </span>
              </div>
              <div className="summary-item">
                <span className="summary-label">DAILY AVG</span>
                <span className="summary-value accent">
                  {formatCurrency(chartData.avg)}
                </span>
              </div>
            </div>
          </div>
        </motion.section>

        {/* Tabs */}
        <div className="tabs-container">
          <button
            className={`tab-btn ${activeTab === "overview" ? "active" : ""}`}
            onClick={() => setActiveTab("overview")}
          >
            Overview
          </button>
          <button
            className={`tab-btn ${activeTab === "transactions" ? "active" : ""}`}
            onClick={() => setActiveTab("transactions")}
          >
            Transactions
          </button>
        </div>

        {/* Tab Content */}
        {activeTab === "overview" && (
          <motion.section
            className="section-card info-section"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.3 }}
          >
            <div className="section-header">
              <span className="section-number">03/</span>
              <h2 className="section-title">How Earnings Work</h2>
            </div>

            <div className="info-grid">
              <div className="info-item">
                <span className="info-icon">◈</span>
                <div className="info-content">
                  <h4>Per Review</h4>
                  <p>Fixed amount for each review completed</p>
                </div>
              </div>
              <div className="info-item">
                <span className="info-icon">◈</span>
                <div className="info-content">
                  <h4>Correction Bonus</h4>
                  <p>Extra earnings when you correct annotations</p>
                </div>
              </div>
              <div className="info-item">
                <span className="info-icon">◈</span>
                <div className="info-content">
                  <h4>Quality Bonus</h4>
                  <p>Monthly bonus based on review quality</p>
                </div>
              </div>
              <div className="info-item">
                <span className="info-icon">◈</span>
                <div className="info-content">
                  <h4>Payouts</h4>
                  <p>Request when balance exceeds ₹500</p>
                </div>
              </div>
            </div>
          </motion.section>
        )}

        {activeTab === "transactions" && (
          <motion.section
            className="section-card transactions-section"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.3 }}
          >
            <div className="section-header">
              <span className="section-number">03/</span>
              <h2 className="section-title">Recent Transactions</h2>
            </div>

            <div className="transactions-list">
              {summary?.recent_transactions &&
              summary.recent_transactions.length > 0 ? (
                summary.recent_transactions.map((tx) => (
                  <div key={tx.id} className="transaction-item">
                    <div className="tx-left">
                      <span
                        className={`tx-indicator ${tx.amount >= 0 ? "positive" : "negative"}`}
                      />
                      <div className="tx-info">
                        <span className="tx-type">
                          {tx.type.replace(/_/g, " ")}
                        </span>
                        <span className="tx-desc">{tx.description}</span>
                      </div>
                    </div>
                    <div className="tx-right">
                      <span
                        className={`tx-amount ${tx.amount >= 0 ? "positive" : "negative"}`}
                      >
                        {tx.amount >= 0 ? "+" : ""}
                        {formatCurrency(tx.amount)}
                      </span>
                      <span className="tx-date">
                        {formatDate(tx.created_at)}
                      </span>
                    </div>
                  </div>
                ))
              ) : (
                <div className="empty-transactions">
                  <span className="empty-icon">○</span>
                  <span className="empty-text">No transactions yet</span>
                </div>
              )}
            </div>
          </motion.section>
        )}
      </div>
    </div>
  );
};

export default ExpertEarnings;

