import React, { useState } from 'react';
import { PricingPage } from './PricingPage';
import { CreditDashboard } from './CreditDashboard';
import { RazorpayCheckout } from './RazorpayCheckout';
import './BillingPage.css';

type ViewMode = 'dashboard' | 'pricing';

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
          📊 Dashboard
        </button>
        <button
          className={viewMode === 'pricing' ? 'active' : ''}
          onClick={() => setViewMode('pricing')}
        >
          💳 Plans & Pricing
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

