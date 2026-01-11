import React, { useState } from 'react';
import { PricingPage } from './PricingPage';
import { CreditDashboard } from './CreditDashboard';
import { RazorpayCheckout } from './RazorpayCheckout';
import './BillingPage.css';

type ViewMode = 'dashboard' | 'pricing';

const DashboardIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <rect x="3" y="3" width="7" height="7" rx="1" />
    <rect x="14" y="3" width="7" height="7" rx="1" />
    <rect x="3" y="14" width="7" height="7" rx="1" />
    <rect x="14" y="14" width="7" height="7" rx="1" />
  </svg>
);

const PricingIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <rect x="1" y="4" width="22" height="16" rx="2" ry="2" />
    <line x1="1" y1="10" x2="23" y2="10" />
  </svg>
);

export const BillingPage: React.FC = () => {
  const [viewMode, setViewMode] = useState<ViewMode>('dashboard');
  const [checkoutOpen, setCheckoutOpen] = useState(false);
  const [selectedItem, setSelectedItem] = useState<{ id: number; type: 'subscription' | 'credits' } | null>(null);

  const handlePurchase = (itemId: number, type: 'subscription' | 'credits') => {
    setSelectedItem({ id: itemId, type });
    setCheckoutOpen(true);
  };

  const handlePaymentSuccess = () => {
    // Refresh the dashboard
    setViewMode('dashboard');
    // Show success message (you can implement a toast notification here)
    alert('Payment successful! Your credits have been added.');
  };

  return (
    <div className="billing-page-container">
      {/* Navigation */}
      <div className="billing-nav">
        <button
          className={viewMode === 'dashboard' ? 'active' : ''}
          onClick={() => setViewMode('dashboard')}
        >
          <DashboardIcon /> Dashboard
        </button>
        <button
          className={viewMode === 'pricing' ? 'active' : ''}
          onClick={() => setViewMode('pricing')}
        >
          <PricingIcon /> Plans & Pricing
        </button>
      </div>

      {/* Content */}
      <div className="billing-content">
        {viewMode === 'dashboard' && <CreditDashboard />}
        {viewMode === 'pricing' && <PricingPage onPurchase={handlePurchase} />}
      </div>

      {/* Checkout Modal */}
      {checkoutOpen && selectedItem && (
        <RazorpayCheckout
          isOpen={checkoutOpen}
          onClose={() => {
            setCheckoutOpen(false);
            setSelectedItem(null);
          }}
          onSuccess={handlePaymentSuccess}
          itemId={selectedItem.id}
          itemType={selectedItem.type}
        />
      )}
    </div>
  );
};

