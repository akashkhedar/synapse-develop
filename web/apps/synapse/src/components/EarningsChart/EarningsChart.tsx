import React, { useMemo } from "react";
import { motion } from "framer-motion";
import { formatCurrency, formatShortDate } from "../../utils/formatters";
import "./EarningsChart.css";

interface DailyEarning {
  date: string;
  amount: number;
}

interface EarningsChartProps {
  /** Array of daily earnings data */
  dailyEarnings: DailyEarning[];
  /** Number of days to display (default: 14) */
  daysToShow?: number;
  /** Weekly earnings total for summary */
  weeklyEarnings?: number;
  /** Monthly earnings total for summary */
  monthlyEarnings?: number;
  /** Title of the chart section */
  title?: string;
  /** Section number prefix (e.g., "02/") */
  sectionNumber?: string;
  /** Accent color for bars above average */
  accentColor?: string;
}

/**
 * Bar chart component showing earnings trend over time
 * Used by both Annotator and Expert earnings pages
 */
export const EarningsChart: React.FC<EarningsChartProps> = ({
  dailyEarnings,
  daysToShow = 14,
  weeklyEarnings = 0,
  monthlyEarnings = 0,
  title = "Earnings Trend",
  sectionNumber = "02/",
  accentColor = "#22c55e",
}) => {
  const chartData = useMemo(() => {
    if (!dailyEarnings?.length) return { bars: [], max: 0, avg: 0 };

    const earnings = dailyEarnings.slice(-daysToShow);
    const max = Math.max(...earnings.map((e) => e.amount), 1);
    const avg =
      earnings.reduce((sum, e) => sum + e.amount, 0) / (earnings.length || 1);

    const bars = earnings.map((e) => ({
      amount: e.amount,
      date: new Date(e.date),
      height: (e.amount / max) * 100,
      isAboveAvg: e.amount >= avg,
    }));

    return { bars, max, avg };
  }, [dailyEarnings, daysToShow]);

  return (
    <div className="earnings-chart">
      <div className="earnings-chart__header">
        <span className="section-number">{sectionNumber}</span>
        <h2 className="section-title">{title}</h2>
        <span className="section-period">Last {daysToShow} days</span>
      </div>

      <div className="earnings-chart__wrapper">
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
                    {formatShortDate(bar.date)}
                  </span>
                  <span
                    className="tooltip-amount"
                    style={{ color: accentColor }}
                  >
                    {formatCurrency(bar.amount)}
                  </span>
                </div>
                <motion.div
                  className={`bar ${bar.isAboveAvg ? "above" : "below"}`}
                  style={
                    bar.isAboveAvg
                      ? {
                          background: `linear-gradient(180deg, ${accentColor} 0%, ${accentColor}dd 100%)`,
                        }
                      : undefined
                  }
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

        {/* Chart Summary */}
        <div className="chart-summary">
          <div className="summary-item">
            <span className="summary-label">THIS WEEK</span>
            <span className="summary-value">
              {formatCurrency(weeklyEarnings)}
            </span>
          </div>
          <div className="summary-item">
            <span className="summary-label">THIS MONTH</span>
            <span className="summary-value">
              {formatCurrency(monthlyEarnings)}
            </span>
          </div>
          <div className="summary-item">
            <span className="summary-label">DAILY AVG</span>
            <span className="summary-value" style={{ color: accentColor }}>
              {formatCurrency(chartData.avg)}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default EarningsChart;
