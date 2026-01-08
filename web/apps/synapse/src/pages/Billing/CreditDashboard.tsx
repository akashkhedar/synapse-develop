import React, { useState, useEffect } from 'react';
import { billingApi, BillingDashboard, CreditTransaction, Payment } from '../../services/billingApi';
import './CreditDashboard.css';

export const CreditDashboard: React.FC = () => {
  const [dashboard, setDashboard] = useState<BillingDashboard | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'overview' | 'transactions' | 'payments'>('overview');

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
      if (category === 'purchase' || category === 'subscription') return '💳';
      if (category === 'bonus') return '🎁';
      if (category === 'refund') return '↩️';
      return '➕';
    }
    if (category === 'annotation') return '🏷️';
    if (category === 'storage') return '💾';
    return '➖';
  };

  const getStatusBadge = (status: string) => {
    const statusConfig: Record<string, { color: string; label: string }> = {
      pending: { color: '#ed8936', label: 'Pending' },
      authorized: { color: '#4299e1', label: 'Authorized' },
      captured: { color: '#48bb78', label: 'Completed' },
      refunded: { color: '#a0aec0', label: 'Refunded' },
      failed: { color: '#e53e3e', label: 'Failed' },
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
          <div className="spinner"></div>
          <p>Loading billing information...</p>
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
          🔄 Refresh
        </button>
      </div>

      {/* Credit Balance Cards */}
      <div className="balance-cards">
        <div className="balance-card primary">
          <div className="card-icon">💰</div>
          <div className="card-content">
            <div className="card-label">Available Credits</div>
            <div className="card-value">{billing.available_credits.toLocaleString()}</div>
            <div className="card-note">Ready to use</div>
          </div>
        </div>

        {billing.rollover_credits > 0 && (
          <div className="balance-card">
            <div className="card-icon">🔄</div>
            <div className="card-content">
              <div className="card-label">Rollover Credits</div>
              <div className="card-value">{billing.rollover_credits.toLocaleString()}</div>
              <div className="card-note">From previous month</div>
            </div>
          </div>
        )}

        <div className="balance-card">
          <div className="card-icon">📦</div>
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
          <div className="card-icon">💾</div>
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
              {recent_payments.length === 0 ? (
                <p className="empty-state">No payments found</p>
              ) : (
                <div className="payments-table">
                  <table>
                    <thead>
                      <tr>
                        <th>Date</th>
                        <th>Description</th>
                        <th>Order ID</th>
                        <th>Method</th>
                        <th>Amount</th>
                        <th>Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {recent_payments.map((payment) => (
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

