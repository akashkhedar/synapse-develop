import React, { useState, useEffect, useCallback, useMemo } from "react";
import { useHistory } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { Button, useToast, ToastType, Spinner } from "@synapse/ui";
import { ExpertiseSection } from "./components";
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
  daily_earnings?: { date: string; amount: number }[];
  activity_streak?: number;
  activity_days?: string[];
}

const LEVEL_CONFIG: Record<
  string,
  {
    color: string;
    icon: string;
    next: string | null;
    tasksReq: number;
    accuracyReq: number;
  }
> = {
  new: {
    color: "#6b7280",
    icon: "◇",
    next: "junior",
    tasksReq: 0,
    accuracyReq: 0,
  },
  junior: {
    color: "#22c55e",
    icon: "◆",
    next: "regular",
    tasksReq: 50,
    accuracyReq: 70,
  },
  regular: {
    color: "#3b82f6",
    icon: "★",
    next: "senior",
    tasksReq: 200,
    accuracyReq: 80,
  },
  senior: {
    color: "#a855f7",
    icon: "✦",
    next: "expert",
    tasksReq: 500,
    accuracyReq: 90,
  },
  expert: {
    color: "#f59e0b",
    icon: "✧",
    next: null,
    tasksReq: 1000,
    accuracyReq: 95,
  },
};

const LEVEL_ORDER = ["new", "junior", "regular", "senior", "expert"];

// Floating pixels decoration - matching landing page
const FloatingPixels = () => {
  const pixels = [
    { x: "5%", y: "15%", size: 3, opacity: 0.2 },
    { x: "12%", y: "45%", size: 4, opacity: 0.3 },
    { x: "20%", y: "70%", size: 3, opacity: 0.15 },
    { x: "85%", y: "20%", size: 4, opacity: 0.25 },
    { x: "90%", y: "55%", size: 3, opacity: 0.2 },
    { x: "75%", y: "80%", size: 4, opacity: 0.3 },
  ];

  return (
    <div className="floating-pixels">
      {pixels.map((p, i) => (
        <motion.div
          key={i}
          className="pixel"
          style={{
            left: p.x,
            top: p.y,
            width: p.size,
            height: p.size,
            opacity: p.opacity,
          }}
          animate={{
            opacity: [p.opacity * 0.5, p.opacity, p.opacity * 0.5],
            scale: [0.9, 1, 0.9],
          }}
          transition={{
            duration: 4 + Math.random() * 2,
            repeat: Infinity,
            ease: "linear",
          }}
        />
      ))}
    </div>
  );
};

export const EarningsDashboard: React.FC = () => {
  const history = useHistory();
  const toast = useToast();

  const [loading, setLoading] = useState(true);
  const [summary, setSummary] = useState<EarningsSummary | null>(null);
  const [selectedMonth, setSelectedMonth] = useState(new Date());

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

      // Ensure trust_level exists with defaults
      if (!data.trust_level) {
        data.trust_level = {
          level: "new",
          multiplier: 1,
          tasks_completed: 0,
          accuracy_score: 0,
          honeypot_pass_rate: 0,
          total_honeypots: 0,
          passed_honeypots: 0,
          fraud_flags: 0,
          is_suspended: false,
        };
      }

      // Generate mock daily earnings for the chart if not provided
      if (!data.daily_earnings) {
        const days = 30;
        data.daily_earnings = Array.from({ length: days }, (_, i) => {
          const date = new Date();
          date.setDate(date.getDate() - (days - 1 - i));
          return {
            date: date.toISOString().split("T")[0],
            amount: Math.random() * 500 + 100,
          };
        });
      }

      // Generate mock activity days for streak calendar if not provided
      if (!data.activity_days) {
        const today = new Date();
        data.activity_days = [];
        data.activity_streak = 0;
        let streak = 0;
        for (let i = 0; i < 60; i++) {
          const date = new Date(today);
          date.setDate(date.getDate() - i);
          if (Math.random() > 0.3) {
            data.activity_days.push(date.toISOString().split("T")[0]);
            if (i === streak) streak++;
          }
        }
        data.activity_streak = streak;
      }

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

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString("en-IN", {
      day: "numeric",
      month: "short",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  // Calculate level progress
  const levelProgress = useMemo(() => {
    if (!summary)
      return {
        percentage: 0,
        nextLevel: null,
        tasksNeeded: 0,
        accuracyNeeded: 0,
      };

    const currentLevelIndex = LEVEL_ORDER.indexOf(summary.trust_level.level);
    const nextLevel = LEVEL_CONFIG[summary.trust_level.level].next;

    if (!nextLevel)
      return {
        percentage: 100,
        nextLevel: null,
        tasksNeeded: 0,
        accuracyNeeded: 0,
      };

    const nextConfig = LEVEL_CONFIG[nextLevel];
    const taskProgress = Math.min(
      100,
      (summary.trust_level.tasks_completed / nextConfig.tasksReq) * 100
    );
    const accuracyProgress = Math.min(
      100,
      (summary.trust_level.accuracy_score / nextConfig.accuracyReq) * 100
    );

    return {
      percentage: Math.min(taskProgress, accuracyProgress),
      nextLevel,
      tasksNeeded: Math.max(
        0,
        nextConfig.tasksReq - summary.trust_level.tasks_completed
      ),
      accuracyNeeded: nextConfig.accuracyReq,
    };
  }, [summary]);

  // Generate calendar data
  const calendarData = useMemo(() => {
    const year = selectedMonth.getFullYear();
    const month = selectedMonth.getMonth();
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const startPadding = firstDay.getDay();
    const days: {
      date: Date;
      isActive: boolean;
      isToday: boolean;
      inMonth: boolean;
    }[] = [];

    for (let i = 0; i < startPadding; i++) {
      const date = new Date(year, month, -startPadding + i + 1);
      days.push({ date, isActive: false, isToday: false, inMonth: false });
    }

    const activitySet = new Set(summary?.activity_days || []);
    const today = new Date().toISOString().split("T")[0];

    for (let d = 1; d <= lastDay.getDate(); d++) {
      const date = new Date(year, month, d);
      const dateStr = date.toISOString().split("T")[0];
      days.push({
        date,
        isActive: activitySet.has(dateStr),
        isToday: dateStr === today,
        inMonth: true,
      });
    }

    const remaining = 42 - days.length;
    for (let i = 1; i <= remaining; i++) {
      const date = new Date(year, month + 1, i);
      days.push({ date, isActive: false, isToday: false, inMonth: false });
    }

    return days;
  }, [selectedMonth, summary?.activity_days]);

  // Chart data for earnings - bar chart format
  const chartData = useMemo(() => {
    if (!summary?.daily_earnings) return { bars: [], max: 0, avg: 0 };

    const earnings = summary.daily_earnings.slice(-14);
    const max = Math.max(...earnings.map((e) => e.amount), 1);
    const avg =
      earnings.reduce((sum, e) => sum + e.amount, 0) / earnings.length;

    const bars = earnings.map((e, i) => ({
      amount: e.amount,
      date: new Date(e.date),
      height: (e.amount / max) * 100,
      isAboveAvg: e.amount >= avg,
    }));

    return { bars, max, avg };
  }, [summary?.daily_earnings]);

  if (loading) {
    return (
      <div className="earnings-page">
        <div className="earnings-loading">
          <Spinner size={64} />
          <span className="loader-text">Loading earnings data...</span>
        </div>
      </div>
    );
  }

  if (!summary) {
    return (
      <div className="earnings-page">
        <div className="earnings-error">
          <span className="error-code">ERROR_404</span>
          <h2>Unable to load earnings</h2>
          <p className="error-desc">
            Something went wrong while fetching your data.
          </p>
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            className="retry-btn"
            onClick={fetchEarnings}
          >
            Try Again
          </motion.button>
        </div>
      </div>
    );
  }

  const levelConfig =
    LEVEL_CONFIG[summary.trust_level?.level || "new"] || LEVEL_CONFIG.new;
  const currentLevelIndex = LEVEL_ORDER.indexOf(
    summary.trust_level?.level || "new"
  );

  return (
    <div className="earnings-page">
      <FloatingPixels />

      {/* Background grid pattern - matching landing */}
      <div className="bg-grid" />

      {/* Gradient glow */}
      <div className="bg-glow" />

      <div className="earnings-container">
        {/* Header Section */}
        <motion.header
          className="earnings-header"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <div className="header-left">
            <span className="header-tag">// DASHBOARD</span>
            <h1 className="header-title">Earnings</h1>
            <p className="header-subtitle">
              Track your performance and revenue
            </p>
          </div>
          <motion.button
            whileHover={{
              scale: 1.02,
              boxShadow: "0 0 30px rgba(139, 92, 246, 0.3)",
            }}
            whileTap={{ scale: 0.98 }}
            className="payout-btn"
            onClick={() => history.push("/annotators/payouts")}
          >
            Request Payout →
          </motion.button>
        </motion.header>

        {/* Stats Row - Lambda style */}
        <motion.div
          className="stats-row bg-black"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.1 }}
        >
          <div className="stat-card available">
            <div className="stat-label">AVAILABLE BALANCE</div>
            <div className="stat-value primary">
              {formatCurrency(summary.available_balance)}
            </div>
            <div className="stat-hint">Ready to withdraw</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">PENDING</div>
            <div className="stat-value">
              {formatCurrency(summary.pending_approval)}
            </div>
            <div className="stat-hint">Awaiting approval</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">TOTAL EARNED</div>
            <div className="stat-value">
              {formatCurrency(summary.total_earned)}
            </div>
            <div className="stat-hint">Lifetime earnings</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">TASKS COMPLETED</div>
            <div className="stat-value">
              {summary.total_tasks.toLocaleString()}
            </div>
            <div className="stat-hint">All time</div>
          </div>
        </motion.div>

        {/* Main Content Grid */}
        <div className="main-grid">
          {/* Left Column */}
          <div className="left-col">
            {/* Trust Level Section */}
            <motion.section
              className="section-card trust-section"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.2 }}
            >
              <div className="section-header">
                <span className="section-number">01/</span>
                <h2 className="section-title">Trust Level</h2>
              </div>

              <div className="trust-content">
                <div className="trust-main">
                  <div className="level-display">
                    <span
                      className="level-icon"
                      style={{ color: levelConfig.color }}
                    >
                      {levelConfig.icon}
                    </span>
                    <div className="level-info">
                      <span className="level-name">
                        {summary.trust_level.level.toUpperCase()}
                      </span>
                      <span className="level-multiplier">
                        {summary.trust_level.multiplier}x earnings multiplier
                      </span>
                    </div>
                  </div>

                  {levelProgress.nextLevel && (
                    <div className="progress-section">
                      <div className="progress-meta">
                        <span>
                          Progress to {levelProgress.nextLevel.toUpperCase()}
                        </span>
                        <span>{Math.round(levelProgress.percentage)}%</span>
                      </div>
                      <div className="progress-track">
                        <motion.div
                          className="progress-fill"
                          initial={{ width: 0 }}
                          animate={{ width: `${levelProgress.percentage}%` }}
                          transition={{ duration: 1, ease: "easeOut" }}
                          style={{ backgroundColor: levelConfig.color }}
                        />
                      </div>
                      <p className="progress-hint">
                        {levelProgress.tasksNeeded > 0 &&
                          `${levelProgress.tasksNeeded} more tasks needed`}
                        {levelProgress.tasksNeeded > 0 &&
                          summary.trust_level.accuracy_score <
                            levelProgress.accuracyNeeded &&
                          " • "}
                        {summary.trust_level.accuracy_score <
                          levelProgress.accuracyNeeded &&
                          `${levelProgress.accuracyNeeded}% accuracy required`}
                      </p>
                    </div>
                  )}
                </div>

                {/* Level progression visual */}
                <div className="level-progression">
                  {LEVEL_ORDER.map((level, index) => {
                    const config = LEVEL_CONFIG[level];
                    const isCurrent = index === currentLevelIndex;
                    const isPast = index < currentLevelIndex;
                    return (
                      <React.Fragment key={level}>
                        <div
                          className={`level-node ${
                            isCurrent ? "current" : ""
                          } ${isPast ? "past" : ""}`}
                        >
                          <span
                            className="node-icon"
                            style={{
                              color:
                                isPast || isCurrent ? config.color : "#333",
                            }}
                          >
                            {config.icon}
                          </span>
                          <span className="node-label">{level}</span>
                        </div>
                        {index < LEVEL_ORDER.length - 1 && (
                          <div
                            className={`level-connector ${
                              isPast ? "filled" : ""
                            }`}
                          />
                        )}
                      </React.Fragment>
                    );
                  })}
                </div>
              </div>

              {/* Trust Stats Grid */}
              <div className="trust-stats">
                <div className="trust-stat">
                  <span className="stat-num">
                    {summary.trust_level.tasks_completed}
                  </span>
                  <span className="stat-lbl">Tasks</span>
                </div>
                <div className="trust-stat">
                  <span className="stat-num">
                    {summary.trust_level.accuracy_score.toFixed(1)}%
                  </span>
                  <span className="stat-lbl">Accuracy</span>
                </div>
                <div className="trust-stat">
                  <span
                    className={`stat-num ${
                      summary.trust_level.fraud_flags > 0 ? "warning" : ""
                    }`}
                  >
                    {summary.trust_level.fraud_flags}
                  </span>
                  <span className="stat-lbl">Flags</span>
                </div>
              </div>

              {summary.trust_level.fraud_flags > 0 && (
                <div className="fraud-warning">
                  <span className="warning-icon">!</span>
                  <span>
                    {summary.trust_level.fraud_flags} quality flag(s) detected.
                    Maintain high accuracy to remove.
                  </span>
                </div>
              )}
            </motion.section>

            {/* Earnings Chart Section */}
            <motion.section
              className="section-card chart-section"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.3 }}
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
                  <div
                    className="avg-line"
                    style={{
                      bottom: `${(chartData.avg / chartData.max) * 100}%`,
                    }}
                  >
                    <span className="avg-label">avg</span>
                  </div>

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
                          className={`bar ${
                            bar.isAboveAvg ? "above" : "below"
                          }`}
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
                      {formatCurrency(summary.weekly_earnings)}
                    </span>
                  </div>
                  <div className="summary-item">
                    <span className="summary-label">THIS MONTH</span>
                    <span className="summary-value">
                      {formatCurrency(summary.monthly_earnings)}
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
          </div>

          {/* Right Column */}
          <div className="right-col">
            {/* Activity Calendar */}
            <motion.section
              className="section-card calendar-section"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.25 }}
            >
              <div className="section-header">
                <span className="section-number">03/</span>
                <h2 className="section-title">Activity</h2>
                <div className="streak-display">
                  <span className="streak-num">
                    {summary.activity_streak || 0}
                  </span>
                  <span className="streak-text">day streak</span>
                </div>
              </div>

              <div className="calendar-nav">
                <button
                  className="nav-btn"
                  onClick={() =>
                    setSelectedMonth(
                      new Date(
                        selectedMonth.getFullYear(),
                        selectedMonth.getMonth() - 1
                      )
                    )
                  }
                >
                  ←
                </button>
                <span className="nav-month">
                  {selectedMonth.toLocaleDateString("en-US", {
                    month: "short",
                    year: "numeric",
                  })}
                </span>
                <button
                  className="nav-btn"
                  onClick={() =>
                    setSelectedMonth(
                      new Date(
                        selectedMonth.getFullYear(),
                        selectedMonth.getMonth() + 1
                      )
                    )
                  }
                >
                  →
                </button>
              </div>

              <div className="calendar">
                <div className="calendar-header">
                  {["S", "M", "T", "W", "T", "F", "S"].map((d, i) => (
                    <span key={i} className="cal-day-label">
                      {d}
                    </span>
                  ))}
                </div>
                <div className="calendar-body">
                  {calendarData.map((day, i) => (
                    <div
                      key={i}
                      className={`cal-day ${day.isActive ? "active" : ""} ${
                        day.isToday ? "today" : ""
                      } ${!day.inMonth ? "outside" : ""}`}
                    >
                      {day.date.getDate()}
                    </div>
                  ))}
                </div>
              </div>
            </motion.section>

            {/* Recent Transactions */}
            <motion.section
              className="section-card transactions-section"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.35 }}
            >
              <div className="section-header">
                <span className="section-number">04/</span>
                <h2 className="section-title">Recent Activity</h2>
                <button
                  className="view-all"
                  onClick={() => history.push("/annotators/transactions")}
                >
                  View all
                </button>
              </div>

              <div className="transactions-list">
                {summary.recent_transactions.length === 0 ? (
                  <div className="empty-state">
                    <span className="empty-text">No transactions yet</span>
                    <span className="empty-hint">
                      Complete tasks to start earning
                    </span>
                  </div>
                ) : (
                  summary.recent_transactions.slice(0, 5).map((tx) => (
                    <div key={tx.id} className="tx-row">
                      <div className="tx-info">
                        <span className={`tx-indicator ${tx.type}`} />
                        <div className="tx-details">
                          <span className="tx-desc">{tx.description}</span>
                          <span className="tx-time">
                            {formatDate(tx.created_at)}
                          </span>
                        </div>
                      </div>
                      <span
                        className={`tx-amount ${
                          tx.amount >= 0 ? "positive" : "negative"
                        }`}
                      >
                        {tx.amount >= 0 ? "+" : ""}
                        {formatCurrency(tx.amount)}
                      </span>
                    </div>
                  ))
                )}
              </div>
            </motion.section>

            {/* Payment Structure */}
            <motion.section
              className="section-card payment-section"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.4 }}
            >
              <div className="section-header">
                <span className="section-number">05/</span>
                <h2 className="section-title">Payment Structure</h2>
              </div>

              <div className="payment-flow">
                <div className="payment-stage">
                  <span className="stage-percent">40%</span>
                  <span className="stage-label">Immediate</span>
                  <span className="stage-desc">On submission</span>
                </div>
                <div className="stage-arrow">→</div>
                <div className="payment-stage">
                  <span className="stage-percent">40%</span>
                  <span className="stage-label">Consensus</span>
                  <span className="stage-desc">Quality check</span>
                </div>
                <div className="stage-arrow">→</div>
                <div className="payment-stage">
                  <span className="stage-percent">20%</span>
                  <span className="stage-label">Review</span>
                  <span className="stage-desc">Expert approval</span>
                </div>
              </div>

              <div className="multiplier-note">
                Your{" "}
                <span className="highlight">
                  {summary.trust_level.multiplier}x
                </span>{" "}
                multiplier applies to all stages
              </div>
            </motion.section>

            {/* Expertise & Badges */}
            <ExpertiseSection />
          </div>
        </div>
      </div>
    </div>
  );
};
