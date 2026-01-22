import React, { useState, useEffect } from 'react';
import { billingApi, SubscriptionPlan, CreditPackage } from '../../services/billingApi';
import { Spinner } from "@synapse/ui";
import './PricingPage.css';

// SVG Icons for Features
const MedicalIcon = () => (
  <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#8b5cf6" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
  </svg>
);

const SecurityIcon = () => (
  <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#8b5cf6" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
  </svg>
);

const SpeedIcon = () => (
  <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#8b5cf6" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
  </svg>
);

const TeamIcon = () => (
  <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#8b5cf6" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2" />
    <circle cx="9" cy="7" r="4" />
    <path d="M23 21v-2a4 4 0 00-3-3.87M16 3.13a4 4 0 010 7.75" />
  </svg>
);

const AnalyticsIcon = () => (
  <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#8b5cf6" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <line x1="18" y1="20" x2="18" y2="10" />
    <line x1="12" y1="20" x2="12" y2="4" />
    <line x1="6" y1="20" x2="6" y2="14" />
  </svg>
);

const ExportIcon = () => (
  <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#8b5cf6" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4" />
    <polyline points="17 8 12 3 7 8" />
    <line x1="12" y1="3" x2="12" y2="15" />
  </svg>
);

const CheckIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="20 6 9 17 4 12" />
  </svg>
);

interface PricingPageProps {
  onPurchase?: (planId: number, type: 'subscription' | 'credits') => void;
}

export const PricingPage: React.FC<PricingPageProps> = ({ onPurchase }) => {
  const [plans, setPlans] = useState<SubscriptionPlan[]>([]);
  const [packages, setPackages] = useState<CreditPackage[]>([]);
  const [billingCycle, setBillingCycle] = useState<'monthly' | 'annual'>('monthly');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Demo/fallback data when API returns empty
  const demoPlans: SubscriptionPlan[] = [
    {
      id: 1,
      name: 'Starter - Monthly',
      plan_type: 'starter',
      billing_cycle: 'monthly',
      price_inr: 2999,
      credits_per_month: 3000,
      effective_rate: 1.00,
      storage_gb: 10,
      max_users: 3,
      priority_support: false,
      api_access: true,
      credit_rollover: false,
      max_rollover_months: 0,
      is_active: true,
    },
    {
      id: 2,
      name: 'Growth - Monthly',
      plan_type: 'growth',
      billing_cycle: 'monthly',
      price_inr: 7999,
      credits_per_month: 10000,
      effective_rate: 0.80,
      storage_gb: 50,
      max_users: 10,
      priority_support: true,
      api_access: true,
      credit_rollover: true,
      max_rollover_months: 1,
      is_active: true,
    },
    {
      id: 3,
      name: 'Scale - Monthly',
      plan_type: 'scale',
      billing_cycle: 'monthly',
      price_inr: 19999,
      credits_per_month: 35000,
      effective_rate: 0.57,
      storage_gb: 200,
      max_users: null,
      priority_support: true,
      api_access: true,
      credit_rollover: true,
      max_rollover_months: 2,
      is_active: true,
    },
    {
      id: 4,
      name: 'Starter - Annual',
      plan_type: 'starter',
      billing_cycle: 'annual',
      price_inr: 29990,
      credits_per_month: 3000,
      effective_rate: 0.83,
      storage_gb: 10,
      max_users: 3,
      priority_support: false,
      api_access: true,
      credit_rollover: false,
      max_rollover_months: 0,
      is_active: true,
    },
    {
      id: 5,
      name: 'Growth - Annual',
      plan_type: 'growth',
      billing_cycle: 'annual',
      price_inr: 79990,
      credits_per_month: 10000,
      effective_rate: 0.67,
      storage_gb: 50,
      max_users: 10,
      priority_support: true,
      api_access: true,
      credit_rollover: true,
      max_rollover_months: 1,
      is_active: true,
    },
    {
      id: 6,
      name: 'Scale - Annual',
      plan_type: 'scale',
      billing_cycle: 'annual',
      price_inr: 199990,
      credits_per_month: 35000,
      effective_rate: 0.48,
      storage_gb: 200,
      max_users: null,
      priority_support: true,
      api_access: true,
      credit_rollover: true,
      max_rollover_months: 2,
      is_active: true,
    },
  ];

  const demoPackages: CreditPackage[] = [
    {
      id: 1,
      name: 'Starter Pack',
      credits: 500,
      price_inr: 749,
      rate_per_credit: 1.50,
      is_active: true,
    },
    {
      id: 2,
      name: 'Basic Pack',
      credits: 2000,
      price_inr: 2599,
      rate_per_credit: 1.30,
      is_active: true,
    },
    {
      id: 3,
      name: 'Pro Pack',
      credits: 5000,
      price_inr: 5999,
      rate_per_credit: 1.20,
      is_active: true,
    },
  ];

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
      // Use demo data if API returns empty arrays
      setPlans(plansData.length > 0 ? plansData : demoPlans);
      setPackages(packagesData.length > 0 ? packagesData : demoPackages);
      setError(null);
    } catch (err: any) {
      // On error, use demo data
      console.warn('Failed to load pricing from API, using demo data:', err);
      setPlans(demoPlans);
      setPackages(demoPackages);
      setError(null);
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
        <div className="pricing-loading">
          <Spinner size={64} />
        </div>
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
        <div className="section-header" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center' }}>
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
                    <span className="icon"><CheckIcon /></span>
                    <strong>{plan.credits_per_month.toLocaleString()}</strong> credits per month
                  </li>
                  <li>
                    <span className="icon"><CheckIcon /></span>
                    <strong>{plan.storage_gb} GB</strong> storage
                  </li>
                  <li>
                    <span className="icon"><CheckIcon /></span>
                    {plan.max_users ? `Up to ${plan.max_users} users` : 'Unlimited users'}
                  </li>
                  {plan.credit_rollover && (
                    <li>
                      <span className="icon"><CheckIcon /></span>
                      Credit rollover ({plan.max_rollover_months} month)
                    </li>
                  )}
                  {plan.priority_support && (
                    <li>
                      <span className="icon"><CheckIcon /></span>
                      Priority support
                    </li>
                  )}
                  {plan.api_access && (
                    <li>
                      <span className="icon"><CheckIcon /></span>
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
        <div className="section-header" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center' }}>
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
            <strong>Pro tip:</strong> Subscriptions offer better rates (₹0.56-1.00/credit) compared to PAYG (₹1.20-1.50/credit).
            Subscribe to save up to 60%!
          </p>
        </div>
      </section>

      {/* Features Comparison */}
      <section className="features-section">
        <h2>What's included in all plans</h2>
        <div className="features-grid">
          <div className="feature-item">
            <div className="feature-icon"><MedicalIcon /></div>
            <h4>Medical AI Annotations</h4>
            <p>X-ray, CT, MRI, ECG, and 20+ modalities</p>
          </div>
          <div className="feature-item">
            <div className="feature-icon"><SecurityIcon /></div>
            <h4>Secure & Compliant</h4>
            <p>HIPAA-ready data handling</p>
          </div>
          <div className="feature-item">
            <div className="feature-icon"><SpeedIcon /></div>
            <h4>Fast Processing</h4>
            <p>Real-time annotation and export</p>
          </div>
          <div className="feature-item">
            <div className="feature-icon"><TeamIcon /></div>
            <h4>Team Collaboration</h4>
            <p>Manage teams and assign tasks</p>
          </div>
          <div className="feature-item">
            <div className="feature-icon"><AnalyticsIcon /></div>
            <h4>Analytics Dashboard</h4>
            <p>Track usage and performance</p>
          </div>
          <div className="feature-item">
            <div className="feature-icon"><ExportIcon /></div>
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

