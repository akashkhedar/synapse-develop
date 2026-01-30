import React, { useState, useEffect, useMemo } from 'react';
import { billingApi, BillingDashboard, CreditTransaction, Payment } from '../../services/billingApi';
import { Spinner } from "@synapse/ui";
import './CreditDashboard.css';

// SVG Icons
const CreditIcon = () => (
  <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#8b5cf6" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="10" />
    <path d="M12 6v12M9 9c0-1 1-2 3-2s3 1 3 2-1 2-3 2-3 1-3 2 1 2 3 2 3-1 3-2" />
  </svg>
);

const RolloverIcon = () => (
  <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#10b981" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M21 12a9 9 0 11-3-6.7" />
    <path d="M21 3v6h-6" />
  </svg>
);

const PlanIcon = () => (
  <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#e8e4d9" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <rect x="3" y="4" width="18" height="16" rx="2" />
    <path d="M7 8h10M7 12h6M7 16h8" />
  </svg>
);

const StorageIcon = () => (
  <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#f59e0b" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <ellipse cx="12" cy="5" rx="9" ry="3" />
    <path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3" />
    <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5" />
  </svg>
);

const RefreshIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M21 12a9 9 0 11-3-6.7" />
    <path d="M21 3v6h-6" />
  </svg>
);

const CardIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <rect x="1" y="4" width="22" height="16" rx="2" />
    <line x1="1" y1="10" x2="23" y2="10" />
  </svg>
);

const TagIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M20.59 13.41l-7.17 7.17a2 2 0 01-2.83 0L2 12V2h10l8.59 8.59a2 2 0 010 2.82z" />
    <circle cx="7" cy="7" r="1" />
  </svg>
);

const GiftIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#10b981" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <rect x="3" y="8" width="18" height="14" rx="2" />
    <path d="M12 8V22M3 12h18M12 8c-2 0-4-2-4-4s2-2 4 0c2-2 4-2 4 0s-2 4-4 4z" />
  </svg>
);

const MinusIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#ef4444" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="10" />
    <line x1="8" y1="12" x2="16" y2="12" />
  </svg>
);

const PlusIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#10b981" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="10" />
    <line x1="12" y1="8" x2="12" y2="16" />
    <line x1="8" y1="12" x2="16" y2="12" />
  </svg>
);

// Line Chart Component
const LineChart: React.FC<{
  data: { date: string; credits: number; debits: number }[];
}> = ({ data }) => {
  const [hoveredPoint, setHoveredPoint] = useState<{ x: number; y: number; label: string; value: number; type: 'credit' | 'debit' } | null>(null);
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null);

  if (data.length === 0) {
    return (
      <div style={{
        height: '320px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        color: 'var(--color-neutral-content-subtle)',
        fontFamily: "'Space Grotesk', system-ui, sans-serif",
      }}>
        No transaction data available
      </div>
    );
  }

  const width = 100;
  const height = 50;
  const padding = { top: 5, right: 5, bottom: 15, left: 15 };

  const maxCredits = Math.max(...data.map(d => d.credits), 0);
  const maxDebits = Math.max(...data.map(d => d.debits), 0);
  const maxValue = Math.max(maxCredits, maxDebits, 1);

  const xScale = (index: number) => {
    return padding.left + (index / (data.length - 1 || 1)) * (width - padding.left - padding.right);
  };

  const yScale = (value: number) => {
    return height - padding.bottom - ((value / maxValue) * (height - padding.top - padding.bottom));
  };

  const creditPath = data
    .map((d, i) => {
      const x = xScale(i);
      const y = yScale(d.credits);
      return i === 0 ? `M ${x} ${y}` : `L ${x} ${y}`;
    })
    .join(' ');

  const debitPath = data
    .map((d, i) => {
      const x = xScale(i);
      const y = yScale(d.debits);
      return i === 0 ? `M ${x} ${y}` : `L ${x} ${y}`;
    })
    .join(' ');

  const creditAreaPath = `${creditPath} L ${xScale(data.length - 1)} ${height - padding.bottom} L ${xScale(0)} ${height - padding.bottom} Z`;
  const debitAreaPath = `${debitPath} L ${xScale(data.length - 1)} ${height - padding.bottom} L ${xScale(0)} ${height - padding.bottom} Z`;

  return (
    <div style={{ position: 'relative', width: '100%', height: '320px' }}>
      <svg
        viewBox={`0 0 ${width} ${height}`}
        style={{ width: '100%', height: '100%' }}
        onMouseLeave={() => { setHoveredPoint(null); setHoveredIndex(null); }}
      >
        <defs>
          <linearGradient id="creditGradient" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="#10b981" stopOpacity="0.3" />
            <stop offset="100%" stopColor="#10b981" stopOpacity="0.05" />
          </linearGradient>
          <linearGradient id="debitGradient" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="#ef4444" stopOpacity="0.3" />
            <stop offset="100%" stopColor="#ef4444" stopOpacity="0.05" />
          </linearGradient>
          <filter id="glow">
            <feGaussianBlur stdDeviation="1.5" result="coloredBlur"/>
            <feMerge>
              <feMergeNode in="coloredBlur"/>
              <feMergeNode in="SourceGraphic"/>
            </feMerge>
          </filter>
        </defs>

        {/* Grid lines */}
        {[0, 0.25, 0.5, 0.75, 1].map((ratio, i) => {
          const y = height - padding.bottom - (ratio * (height - padding.top - padding.bottom));
          return (
            <g key={i}>
              <line
                x1={padding.left}
                y1={y}
                x2={width - padding.right}
                y2={y}
                stroke="rgba(255, 255, 255, 0.05)"
                strokeWidth="0.2"
              />
              <text
                x={padding.left - 2}
                y={y}
                fill="rgba(255, 255, 255, 0.4)"
                fontSize="2.5"
                textAnchor="end"
                dominantBaseline="middle"
                fontFamily="'Space Grotesk', system-ui, sans-serif"
              >
                {Math.round(maxValue * ratio)}
              </text>
            </g>
          );
        })}

        {/* Area fills */}
        <path d={creditAreaPath} fill="url(#creditGradient)" />
        <path d={debitAreaPath} fill="url(#debitGradient)" />

        {/* Debit line */}
        <path
          d={debitPath}
          fill="none"
          stroke="#ef4444"
          strokeWidth="0.5"
          strokeLinecap="round"
          strokeLinejoin="round"
          style={{ filter: 'url(#glow)' }}
        />

        {/* Credit line */}
        <path
          d={creditPath}
          fill="none"
          stroke="#10b981"
          strokeWidth="0.5"
          strokeLinecap="round"
          strokeLinejoin="round"
          style={{ filter: 'url(#glow)' }}
        />

        {/* Hover line */}
        {hoveredIndex !== null && (
          <line
            x1={xScale(hoveredIndex)}
            y1={padding.top}
            x2={xScale(hoveredIndex)}
            y2={height - padding.bottom}
            stroke="rgba(139, 92, 246, 0.3)"
            strokeWidth="0.3"
            strokeDasharray="1,1"
          />
        )}

        {/* Data points */}
        {data.map((d, i) => (
          <g key={i}>
            {/* Credit point */}
            <circle
              cx={xScale(i)}
              cy={yScale(d.credits)}
              r={hoveredIndex === i ? "1.2" : "0.8"}
              fill="#10b981"
              stroke="#0f172a"
              strokeWidth="0.3"
              style={{
                cursor: 'pointer',
                transition: 'all 0.2s ease',
                filter: hoveredIndex === i ? 'url(#glow)' : 'none',
              }}
              onMouseEnter={(e) => {
                const rect = e.currentTarget.getBoundingClientRect();
                setHoveredPoint({
                  x: rect.left + rect.width / 2,
                  y: rect.top,
                  label: d.date,
                  value: d.credits,
                  type: 'credit',
                });
                setHoveredIndex(i);
              }}
            />
            {/* Debit point */}
            <circle
              cx={xScale(i)}
              cy={yScale(d.debits)}
              r={hoveredIndex === i ? "1.2" : "0.8"}
              fill="#ef4444"
              stroke="#0f172a"
              strokeWidth="0.3"
              style={{
                cursor: 'pointer',
                transition: 'all 0.2s ease',
                filter: hoveredIndex === i ? 'url(#glow)' : 'none',
              }}
              onMouseEnter={(e) => {
                const rect = e.currentTarget.getBoundingClientRect();
                setHoveredPoint({
                  x: rect.left + rect.width / 2,
                  y: rect.top,
                  label: d.date,
                  value: d.debits,
                  type: 'debit',
                });
                setHoveredIndex(i);
              }}
            />
          </g>
        ))}

        {/* X-axis labels */}
        {data.map((d, i) => {
          // Show only first, last, and middle labels to avoid crowding
          if (i === 0 || i === data.length - 1 || i === Math.floor(data.length / 2)) {
            return (
              <text
                key={i}
                x={xScale(i)}
                y={height - padding.bottom + 4}
                fill="rgba(255, 255, 255, 0.5)"
                fontSize="2.2"
                textAnchor="middle"
                fontFamily="'Space Grotesk', system-ui, sans-serif"
              >
                {d.date}
              </text>
            );
          }
          return null;
        })}
      </svg>

      {/* Tooltip */}
      {hoveredPoint && (
        <div
          style={{
            position: 'fixed',
            left: hoveredPoint.x,
            top: hoveredPoint.y - 80,
            transform: 'translateX(-50%)',
            background: 'linear-gradient(135deg, rgba(15, 23, 42, 0.98), rgba(30, 41, 59, 0.98))',
            border: `1px solid ${hoveredPoint.type === 'credit' ? '#10b981' : '#ef4444'}`,
            borderRadius: '8px',
            padding: '12px 16px',
            pointerEvents: 'none',
            zIndex: 1000,
            boxShadow: `0 8px 24px ${hoveredPoint.type === 'credit' ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.3)'}`,
            fontFamily: "'Space Grotesk', system-ui, sans-serif",
          }}
        >
          <div style={{
            fontSize: '11px',
            color: 'rgba(255, 255, 255, 0.6)',
            marginBottom: '4px',
          }}>
            {hoveredPoint.label}
          </div>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
          }}>
            <div style={{
              width: '8px',
              height: '8px',
              borderRadius: '50%',
              background: hoveredPoint.type === 'credit' ? '#10b981' : '#ef4444',
              boxShadow: `0 0 8px ${hoveredPoint.type === 'credit' ? '#10b981' : '#ef4444'}`,
            }} />
            <div>
              <div style={{
                fontSize: '10px',
                color: 'rgba(255, 255, 255, 0.7)',
                textTransform: 'uppercase',
                letterSpacing: '0.05em',
                marginBottom: '2px',
              }}>
                {hoveredPoint.type === 'credit' ? 'Credits Added' : 'Credits Used'}
              </div>
              <div style={{
                fontSize: '18px',
                fontWeight: 700,
                color: hoveredPoint.type === 'credit' ? '#10b981' : '#ef4444',
              }}>
                {hoveredPoint.value.toLocaleString()}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export const CreditDashboard: React.FC = () => {
  const [dashboard, setDashboard] = useState<BillingDashboard | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'overview' | 'transactions' | 'payments'>('overview');

  // Payments Pagination State
  const [paymentsList, setPaymentsList] = useState<Payment[]>([]);
  const [paymentsOffset, setPaymentsOffset] = useState(0);
  const [hasMorePayments, setHasMorePayments] = useState(true);
  const [loadingPayments, setLoadingPayments] = useState(false);
  const PAYMENTS_LIMIT = 15;

  useEffect(() => {
    if (activeTab === 'payments' && paymentsList.length === 0) {
      loadMorePayments();
    }
  }, [activeTab]);

  const loadMorePayments = async () => {
    if (loadingPayments || !hasMorePayments) return;

    try {
      setLoadingPayments(true);
      const data = await billingApi.getPayments(undefined, PAYMENTS_LIMIT, paymentsOffset);
      
      setPaymentsList(prev => [...prev, ...data.results]);
      setPaymentsOffset(prev => prev + PAYMENTS_LIMIT);
      setHasMorePayments(data.has_more);
    } catch (error) {
      console.error("Failed to load payments", error);
    } finally {
      setLoadingPayments(false);
    }
  };

  const handlePaymentsScroll = (e: React.UIEvent<HTMLDivElement>) => {
    const { scrollTop, scrollHeight, clientHeight } = e.currentTarget;
    if (scrollHeight - scrollTop <= clientHeight + 50) {
      loadMorePayments();
    }
  };

  // Process data for chart
  const chartData = useMemo(() => {
    if (!dashboard) return [];

    // Group transactions by date
    const dataByDate = new Map<string, { credits: number; debits: number }>();

    dashboard.recent_transactions.forEach(txn => {
      const date = new Date(txn.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
      const existing = dataByDate.get(date) || { credits: 0, debits: 0 };
      
      if (txn.transaction_type === 'credit') {
        existing.credits += txn.amount;
      } else {
        existing.debits += Math.abs(txn.amount);
      }
      
      dataByDate.set(date, existing);
    });

    // Convert to array and sort by date
    const sortedData = Array.from(dataByDate.entries())
      .map(([date, values]) => ({
        date,
        credits: values.credits,
        debits: values.debits,
      }))
      .slice(-14); // Last 14 data points

    return sortedData;
  }, [dashboard]);

  useEffect(() => {
    loadDashboard();
  }, []);

  const loadDashboard = async () => {
    try {
      setLoading(true);
      const data = await billingApi.getDashboard();
      setDashboard(data);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to load billing dashboard');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-IN', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const formatCurrency = (amount: number) => {
    return `₹${amount.toLocaleString('en-IN')}`;
  };

  const getTransactionIcon = (type: string, category: string) => {
    if (type === 'credit') {
      if (category === 'purchase' || category === 'subscription') return <CardIcon />;
      if (category === 'bonus') return <GiftIcon />;
      return <PlusIcon />;
    }
    if (category === 'annotation') return <TagIcon />;
    return <MinusIcon />;
  };

  const getStatusBadge = (status: string) => {
    const statusConfig: Record<string, { color: string; label: string }> = {
      pending: { color: '#f59e0b', label: 'Pending' },
      authorized: { color: '#3b82f6', label: 'Authorized' },
      captured: { color: '#10b981', label: 'Completed' },
      refunded: { color: '#6b7280', label: 'Refunded' },
      failed: { color: '#ef4444', label: 'Failed' },
    };

    const config = statusConfig[status] || statusConfig.pending;
    
    return (
      <span className="status-badge" style={{ backgroundColor: config.color }}>
        {config.label}
      </span>
    );
  };

  if (loading) {
    return (
      <div className="credit-dashboard">
        <div className="dashboard-loading">
          <Spinner size={64} />
        </div>
      </div>
    );
  }

  if (error || !dashboard) {
    return (
      <div className="credit-dashboard">
        <div className="dashboard-error">
          <h3>Error Loading Dashboard</h3>
          <p>{error}</p>
          <button onClick={loadDashboard}>Retry</button>
        </div>
      </div>
    );
  }

  const { billing, recent_transactions, recent_payments } = dashboard;

  return (
    <div className="credit-dashboard">
      <div className="dashboard-header">
        <h1>Billing Dashboard</h1>
        <button className="refresh-btn" onClick={loadDashboard}>
          <RefreshIcon /> Refresh
        </button>
      </div>

      {/* Credit Balance Cards */}
      <div className="balance-cards">
        <div className="balance-card primary">
          <div className="card-icon"><CreditIcon /></div>
          <div className="card-content">
            <div className="card-label">Available Credits</div>
            <div className="card-value">{billing.available_credits.toLocaleString()}</div>
            <div className="card-note">Ready to use</div>
          </div>
        </div>

        {billing.rollover_credits > 0 && (
          <div className="balance-card">
            <div className="card-icon"><RolloverIcon /></div>
            <div className="card-content">
              <div className="card-label">Rollover Credits</div>
              <div className="card-value">{billing.rollover_credits.toLocaleString()}</div>
              <div className="card-note">From previous month</div>
            </div>
          </div>
        )}

        <div className="balance-card">
          <div className="card-icon"><PlanIcon /></div>
          <div className="card-content">
            <div className="card-label">Billing Type</div>
            <div className="card-value">
              {billing.billing_type === 'subscription' ? 'Subscription' : 'Pay As You Go'}
            </div>
            {billing.active_subscription_details && (
              <div className="card-note">
                {billing.active_subscription_details.plan_details.name}
              </div>
            )}
          </div>
        </div>

        <div className="balance-card">
          <div className="card-icon"><StorageIcon /></div>
          <div className="card-content">
            <div className="card-label">Storage Used</div>
            <div className="card-value">{billing.storage_used_gb} GB</div>
            <div className="card-note">
              {billing.active_subscription_details
                ? `${billing.active_subscription_details.plan_details.storage_gb} GB included`
                : '5 GB free'}
            </div>
          </div>
        </div>
      </div>

      {/* Subscription Info */}
      {billing.active_subscription_details && (
        <div className="subscription-info">
          <div className="info-header">
            <h3>Active Subscription</h3>
            <span className="subscription-status active">Active</span>
          </div>
          <div className="info-grid">
            <div className="info-item">
              <span className="label">Plan:</span>
              <span className="value">{billing.active_subscription_details.plan_details.name}</span>
            </div>
            <div className="info-item">
              <span className="label">Monthly Credits:</span>
              <span className="value">
                {billing.active_subscription_details.plan_details.credits_per_month.toLocaleString()}
              </span>
            </div>
            <div className="info-item">
              <span className="label">Next Billing:</span>
              <span className="value">
                {formatDate(billing.active_subscription_details.next_billing_date)}
              </span>
            </div>
            <div className="info-item">
              <span className="label">Auto Renew:</span>
              <span className="value">
                {billing.active_subscription_details.auto_renew ? 'Enabled' : 'Disabled'}
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="dashboard-tabs">
        <button
          className={activeTab === 'overview' ? 'active' : ''}
          onClick={() => setActiveTab('overview')}
        >
          Overview
        </button>
        <button
          className={activeTab === 'transactions' ? 'active' : ''}
          onClick={() => setActiveTab('transactions')}
        >
          Transactions
        </button>
        <button
          className={activeTab === 'payments' ? 'active' : ''}
          onClick={() => setActiveTab('payments')}
        >
          Payments
        </button>
      </div>

      {/* Tab Content */}
      <div className="tab-content">
        {activeTab === 'overview' && (
          <div className="overview-section">
            {/* Chart Section */}
            <div className="chart-section">
              <div className="chart-header">
                <h3 style={{
                  fontFamily: "'Space Grotesk', system-ui, sans-serif",
                  fontSize: '18px',
                  fontWeight: 600,
                  color: 'var(--color-neutral-content)',
                  margin: 0,
                }}>
                  Credits Flow
                </h3>
                <div style={{
                  display: 'flex',
                  gap: '24px',
                  alignItems: 'center',
                }}>
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    fontFamily: "'Space Grotesk', system-ui, sans-serif",
                    fontSize: '13px',
                  }}>
                    <div style={{
                      width: '12px',
                      height: '3px',
                      background: '#10b981',
                      borderRadius: '2px',
                      boxShadow: '0 0 8px rgba(16, 185, 129, 0.5)',
                    }} />
                    <span style={{ color: 'rgba(255, 255, 255, 0.7)' }}>Credits Added</span>
                  </div>
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    fontFamily: "'Space Grotesk', system-ui, sans-serif",
                    fontSize: '13px',
                  }}>
                    <div style={{
                      width: '12px',
                      height: '3px',
                      background: '#ef4444',
                      borderRadius: '2px',
                      boxShadow: '0 0 8px rgba(239, 68, 68, 0.5)',
                    }} />
                    <span style={{ color: 'rgba(255, 255, 255, 0.7)' }}>Credits Used</span>
                  </div>
                </div>
              </div>
              <div className="chart-container">
                <LineChart data={chartData} />
              </div>
            </div>

            <div className="section-grid">
              {/* Recent Transactions */}
              <div className="section-card">
                <h3>Recent Transactions</h3>
                {recent_transactions.length === 0 ? (
                  <p className="empty-state">No transactions yet</p>
                ) : (
                  <div className="transaction-list">
                    {recent_transactions.slice(0, 5).map((txn) => (
                      <div key={txn.id} className="transaction-item">
                        <div className="txn-icon">{getTransactionIcon(txn.transaction_type, txn.category)}</div>
                        <div className="txn-details">
                          <div className="txn-description">{txn.description}</div>
                          <div className="txn-date">{formatDate(txn.created_at)}</div>
                        </div>
                        <div className={`txn-amount ${txn.transaction_type}`}>
                          {txn.transaction_type === 'credit' ? '+' : '-'}
                          {Math.abs(txn.amount).toLocaleString()}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Recent Payments */}
              <div className="section-card">
                <h3>Recent Payments</h3>
                {recent_payments.length === 0 ? (
                  <p className="empty-state">No payments yet</p>
                ) : (
                  <div className="payment-list">
                    {recent_payments.slice(0, 5).map((payment) => (
                      <div key={payment.id} className="payment-item">
                        <div className="payment-details">
                          <div className="payment-description">
                            {payment.credit_package_details
                              ? payment.credit_package_details.name
                              : 'Subscription Payment'}
                          </div>
                          <div className="payment-date">{formatDate(payment.created_at)}</div>
                        </div>
                        <div className="payment-right">
                          <div className="payment-amount">{formatCurrency(payment.amount_inr)}</div>
                          {getStatusBadge(payment.status)}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'transactions' && (
          <div className="transactions-section">
            <div className="section-card">
              <h3>All Transactions</h3>
              {recent_transactions.length === 0 ? (
                <p className="empty-state">No transactions found</p>
              ) : (
                <div className="transactions-table">
                  <table>
                    <thead>
                      <tr>
                        <th>Date</th>
                        <th>Description</th>
                        <th>Type</th>
                        <th>Category</th>
                        <th>Amount</th>
                        <th>Balance</th>
                      </tr>
                    </thead>
                    <tbody>
                      {recent_transactions.map((txn) => (
                        <tr key={txn.id}>
                          <td>{formatDate(txn.created_at)}</td>
                          <td>{txn.description}</td>
                          <td>
                            <span className={`type-badge ${txn.transaction_type}`}>
                              {txn.transaction_type}
                            </span>
                          </td>
                          <td>{txn.category}</td>
                          <td className={`amount ${txn.transaction_type}`}>
                            {txn.transaction_type === 'credit' ? '+' : '-'}
                            {Math.abs(txn.amount).toLocaleString()}
                          </td>
                          <td>{txn.balance_after.toLocaleString()}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === 'payments' && (
          <div className="payments-section">
            <div className="section-card">
              <h3>Payment History</h3>
              {paymentsList.length === 0 && !loadingPayments ? (
                <p className="empty-state">No payments found</p>
              ) : (
                <div 
                  className="payments-table" 
                  style={{ maxHeight: '600px', overflowY: 'auto' }}
                  onScroll={handlePaymentsScroll}
                >
                  <table>
                    <thead>
                      <tr>
                        <th style={{ position: 'sticky', top: 0, background: 'var(--color-neutral-surface)', zIndex: 1 }}>Date</th>
                        <th style={{ position: 'sticky', top: 0, background: 'var(--color-neutral-surface)', zIndex: 1 }}>Description</th>
                        <th style={{ position: 'sticky', top: 0, background: 'var(--color-neutral-surface)', zIndex: 1 }}>Order ID</th>
                        <th style={{ position: 'sticky', top: 0, background: 'var(--color-neutral-surface)', zIndex: 1 }}>Method</th>
                        <th style={{ position: 'sticky', top: 0, background: 'var(--color-neutral-surface)', zIndex: 1 }}>Amount</th>
                        <th style={{ position: 'sticky', top: 0, background: 'var(--color-neutral-surface)', zIndex: 1 }}>Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {paymentsList.map((payment) => (
                        <tr key={payment.id}>
                          <td>{formatDate(payment.created_at)}</td>
                          <td>
                            {payment.credit_package_details
                              ? payment.credit_package_details.name
                              : 'Subscription'}
                          </td>
                          <td className="order-id">{payment.razorpay_order_id}</td>
                          <td>{payment.payment_method || '-'}</td>
                          <td className="amount">{formatCurrency(payment.amount_inr)}</td>
                          <td>{getStatusBadge(payment.status)}</td>
                        </tr>
                      ))}
                      {loadingPayments && (
                         <tr>
                           <td colSpan={6} style={{ textAlign: 'center', padding: '20px' }}>
                             <Spinner size={24} />
                           </td>
                         </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

