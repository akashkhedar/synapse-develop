import React, { useState, useEffect } from 'react';
import { billingApi, SubscriptionPlan, CreditPackage } from '../../services/billingApi';
import './PricingPage.css';

interface PricingPageProps {
  onPurchase?: (planId: number, type: 'subscription' | 'credits') => void;
}

export const PricingPage: React.FC<PricingPageProps> = ({ onPurchase }) => {
  const [plans, setPlans] = useState<SubscriptionPlan[]>([]);
  const [packages, setPackages] = useState<CreditPackage[]>([]);
  const [billingCycle, setBillingCycle] = useState<'monthly' | 'annual'>('monthly');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadPricingData();
  }, []);

  const loadPricingData = async () => {
    try {
      setLoading(true);
      const [plansData, packagesData] = await Promise.all([
        billingApi.getSubscriptionPlans(),
        billingApi.getCreditPackages(),
      ]);
      setPlans(plansData);
      setPackages(packagesData);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to load pricing data');
    } finally {
      setLoading(false);
    }
  };

  const filteredPlans = plans.filter(plan => plan.billing_cycle === billingCycle);

  const handleSelectPlan = (planId: number) => {
    if (onPurchase) {
      onPurchase(planId, 'subscription');
    }
  };

  const handleSelectPackage = (packageId: number) => {
    if (onPurchase) {
      onPurchase(packageId, 'credits');
    }
  };

  if (loading) {
    return (
      <div className="pricing-page">
        <div className="pricing-loading">Loading pricing information...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="pricing-page">
        <div className="pricing-error">
          <h3>Error loading pricing</h3>
          <p>{error}</p>
          <button onClick={loadPricingData}>Retry</button>
        </div>
      </div>
    );
  }

  return (
    <div className="pricing-page">
      <div className="pricing-header">
        <h1>Choose Your Plan</h1>
        <p className="pricing-subtitle">
          Flexible pricing for teams of all sizes. Pay as you go or subscribe for better rates.
        </p>
      </div>

      {/* Subscription Plans Section */}
      <section className="pricing-section">
        <div className="section-header">
          <h2>Subscription Plans</h2>
          <div className="billing-cycle-toggle">
            <button
              className={billingCycle === 'monthly' ? 'active' : ''}
              onClick={() => setBillingCycle('monthly')}
            >
              Monthly
            </button>
            <button
              className={billingCycle === 'annual' ? 'active' : ''}
              onClick={() => setBillingCycle('annual')}
            >
              Annual <span className="badge">Save 15-20%</span>
            </button>
          </div>
        </div>

        <div className="pricing-cards">
          {filteredPlans.map((plan) => (
            <div key={plan.id} className={`pricing-card ${plan.plan_type}`}>
              <div className="card-header">
                <h3>{plan.name.replace(` - ${billingCycle === 'monthly' ? 'Monthly' : 'Annual'}`, '')}</h3>
                <div className="price">
                  <span className="currency">₹</span>
                  <span className="amount">{plan.price_inr.toLocaleString()}</span>
                  <span className="period">/{billingCycle === 'monthly' ? 'month' : 'year'}</span>
                </div>
                <div className="effective-rate">
                  ₹{plan.effective_rate.toFixed(2)} per credit
                </div>
              </div>

              <div className="card-body">
                <ul className="features">
                  <li>
                    <span className="icon">✓</span>
                    <strong>{plan.credits_per_month.toLocaleString()}</strong> credits per month
                  </li>
                  <li>
                    <span className="icon">✓</span>
                    <strong>{plan.storage_gb} GB</strong> storage
                  </li>
                  <li>
                    <span className="icon">✓</span>
                    {plan.max_users ? `Up to ${plan.max_users} users` : 'Unlimited users'}
                  </li>
                  {plan.credit_rollover && (
                    <li>
                      <span className="icon">✓</span>
                      Credit rollover ({plan.max_rollover_months} month)
                    </li>
                  )}
                  {plan.priority_support && (
                    <li>
                      <span className="icon">✓</span>
                      Priority support
                    </li>
                  )}
                  {plan.api_access && (
                    <li>
                      <span className="icon">✓</span>
                      Full API access
                    </li>
                  )}
                </ul>
              </div>

              <div className="card-footer">
                <button
                  className="btn-select-plan"
                  onClick={() => handleSelectPlan(plan.id)}
                >
                  Choose {plan.plan_type.charAt(0).toUpperCase() + plan.plan_type.slice(1)}
                </button>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Pay As You Go Section */}
      <section className="pricing-section payg-section">
        <div className="section-header">
          <h2>Pay As You Go</h2>
          <p>One-time credit purchases. Perfect for trying out or occasional use.</p>
        </div>

        <div className="pricing-cards payg-cards">
          {packages.map((pkg) => (
            <div key={pkg.id} className="pricing-card payg-card">
              <div className="card-header">
                <h3>{pkg.credits.toLocaleString()} Credits</h3>
                <div className="price">
                  <span className="currency">₹</span>
                  <span className="amount">{pkg.price_inr.toLocaleString()}</span>
                </div>
                <div className="rate">
                  ₹{pkg.rate_per_credit.toFixed(2)} per credit
                </div>
              </div>

              <div className="card-body">
                <div className="package-info">
                  <p>One-time purchase</p>
                  <p className="note">Credits never expire</p>
                </div>
              </div>

              <div className="card-footer">
                <button
                  className="btn-select-package"
                  onClick={() => handleSelectPackage(pkg.id)}
                >
                  Buy {pkg.credits.toLocaleString()} Credits
                </button>
              </div>
            </div>
          ))}
        </div>

        <div className="payg-note">
          <p>
            💡 <strong>Tip:</strong> Subscriptions offer better rates (₹0.56-1.00/credit) compared to PAYG (₹1.20-1.50/credit).
            Subscribe to save up to 60%!
          </p>
        </div>
      </section>

      {/* Features Comparison */}
      <section className="features-section">
        <h2>What's included in all plans</h2>
        <div className="features-grid">
          <div className="feature-item">
            <div className="feature-icon">📊</div>
            <h4>Medical AI Annotations</h4>
            <p>X-ray, CT, MRI, ECG, and 20+ modalities</p>
          </div>
          <div className="feature-item">
            <div className="feature-icon">🔒</div>
            <h4>Secure & Compliant</h4>
            <p>HIPAA-ready data handling</p>
          </div>
          <div className="feature-item">
            <div className="feature-icon">⚡</div>
            <h4>Fast Processing</h4>
            <p>Real-time annotation and export</p>
          </div>
          <div className="feature-item">
            <div className="feature-icon">👥</div>
            <h4>Team Collaboration</h4>
            <p>Manage teams and assign tasks</p>
          </div>
          <div className="feature-item">
            <div className="feature-icon">📈</div>
            <h4>Analytics Dashboard</h4>
            <p>Track usage and performance</p>
          </div>
          <div className="feature-item">
            <div className="feature-icon">🔄</div>
            <h4>Export Formats</h4>
            <p>JSON, COCO, YOLO, and more</p>
          </div>
        </div>
      </section>

      {/* FAQ Section */}
      <section className="faq-section">
        <h2>Frequently Asked Questions</h2>
        <div className="faq-grid">
          <div className="faq-item">
            <h4>How do credits work?</h4>
            <p>
              Credits are deducted based on annotation type and data complexity. For example, a bounding box
              on a chest X-ray costs 6 credits (1 base + 5 for bounding box).
            </p>
          </div>
          <div className="faq-item">
            <h4>Can I change plans?</h4>
            <p>
              Yes! You can upgrade or downgrade anytime. Unused credits from subscriptions can be rolled over
              to the next month.
            </p>
          </div>
          <div className="faq-item">
            <h4>Do credits expire?</h4>
            <p>
              PAYG credits never expire. Subscription credits rollover for 1 month if unused.
            </p>
          </div>
          <div className="faq-item">
            <h4>What payment methods?</h4>
            <p>
              We accept all major credit/debit cards, UPI, net banking, and wallets via Razorpay.
            </p>
          </div>
        </div>
      </section>
    </div>
  );
};

