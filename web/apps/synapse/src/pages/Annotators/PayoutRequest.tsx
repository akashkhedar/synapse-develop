import React, { useState, useEffect, useCallback } from "react";
import { useHistory } from "react-router-dom";
import { Button, useToast, ToastType } from "@synapse/ui";
import "./PayoutRequest.css";

interface BankDetails {
  bank_name: string;
  account_number: string;
  ifsc_code: string;
  account_holder_name: string;
  upi_id: string;
  has_bank_details: boolean;
  has_upi: boolean;
}

interface PayoutHistory {
  id: number;
  amount: number;
  status: string;
  payout_method: string;
  transaction_id: string;
  failure_reason: string;
  requested_at: string;
  processed_at: string | null;
}

interface EarningsSummary {
  available_balance: number;
  pending_approval: number;
}

const MINIMUM_PAYOUT = 100;

const STATUS_COLORS: Record<string, string> = {
  pending: "#ff9800",
  processing: "#2196f3",
  completed: "#4caf50",
  failed: "#f44336",
  cancelled: "#9e9e9e",
};

const STATUS_ICONS: Record<string, string> = {
  pending: "⏳",
  processing: "🔄",
  completed: "✅",
  failed: "❌",
  cancelled: "🚫",
};

export const PayoutRequest: React.FC = () => {
  const history = useHistory();
  const toast = useToast();

  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [bankDetails, setBankDetails] = useState<BankDetails | null>(null);
  const [payoutHistory, setPayoutHistory] = useState<PayoutHistory[]>([]);
  const [earnings, setEarnings] = useState<EarningsSummary | null>(null);

  const [amount, setAmount] = useState("");
  const [payoutMethod, setPayoutMethod] = useState<"bank_transfer" | "upi">(
    "bank_transfer"
  );
  const [showBankForm, setShowBankForm] = useState(false);

  const [bankForm, setBankForm] = useState({
    bank_name: "",
    account_number: "",
    ifsc_code: "",
    account_holder_name: "",
    upi_id: "",
  });

  const fetchData = useCallback(async () => {
    try {
      const [bankRes, payoutRes, earningsRes] = await Promise.all([
        fetch("/api/annotators/bank-details", { credentials: "include" }),
        fetch("/api/annotators/payouts", { credentials: "include" }),
        fetch("/api/annotators/earnings", { credentials: "include" }),
      ]);

      if (bankRes.status === 403) {
        history.push("/annotators/login");
        return;
      }

      const bankData = await bankRes.json();
      const payoutData = await payoutRes.json();
      const earningsData = await earningsRes.json();

      setBankDetails(bankData);
      setPayoutHistory(payoutData.payouts || []);
      setEarnings(earningsData);

      // Pre-fill bank form
      setBankForm({
        bank_name: bankData.bank_name || "",
        account_number: "",
        ifsc_code: bankData.ifsc_code || "",
        account_holder_name: bankData.account_holder_name || "",
        upi_id: bankData.upi_id || "",
      });
    } catch (error) {
      console.error("Failed to fetch data:", error);
      toast?.show({
        message: "Failed to load data",
        type: ToastType.error,
        duration: 3000,
      });
    } finally {
      setLoading(false);
    }
  }, [history, toast]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

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

  const handleBankFormChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setBankForm({ ...bankForm, [name]: value });
  };

  const saveBankDetails = async () => {
    try {
      const response = await fetch("/api/annotators/bank-details", {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(bankForm),
      });

      if (response.ok) {
        toast?.show({
          message: "Bank details saved successfully",
          type: ToastType.info,
          duration: 3000,
        });
        setShowBankForm(false);
        fetchData();
      } else {
        throw new Error("Failed to save");
      }
    } catch (error) {
      toast?.show({
        message: "Failed to save bank details",
        type: ToastType.error,
        duration: 3000,
      });
    }
  };

  const submitPayoutRequest = async () => {
    const numAmount = parseFloat(amount);

    if (isNaN(numAmount) || numAmount < MINIMUM_PAYOUT) {
      toast?.show({
        message: `Minimum payout amount is ${formatCurrency(MINIMUM_PAYOUT)}`,
        type: ToastType.error,
        duration: 3000,
      });
      return;
    }

    if (earnings && numAmount > earnings.available_balance) {
      toast?.show({
        message: "Insufficient balance",
        type: ToastType.error,
        duration: 3000,
      });
      return;
    }

    if (payoutMethod === "bank_transfer" && !bankDetails?.has_bank_details) {
      toast?.show({
        message: "Please add bank details first",
        type: ToastType.error,
        duration: 3000,
      });
      return;
    }

    if (payoutMethod === "upi" && !bankDetails?.has_upi) {
      toast?.show({
        message: "Please add UPI ID first",
        type: ToastType.error,
        duration: 3000,
      });
      return;
    }

    setSubmitting(true);

    try {
      const response = await fetch("/api/annotators/payouts", {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          amount: numAmount,
          payout_method: payoutMethod,
        }),
      });

      const data = await response.json();

      if (response.ok && data.success) {
        toast?.show({
          message: "Payout request submitted successfully!",
          type: ToastType.info,
          duration: 3000,
        });
        setAmount("");
        fetchData();
      } else {
        toast?.show({
          message: data.errors?.[0] || "Failed to submit request",
          type: ToastType.error,
          duration: 4000,
        });
      }
    } catch (error) {
      toast?.show({
        message: "Failed to submit payout request",
        type: ToastType.error,
        duration: 3000,
      });
    } finally {
      setSubmitting(false);
    }
  };

  const cancelPayout = async (payoutId: number) => {
    if (
      !window.confirm("Are you sure you want to cancel this payout request?")
    ) {
      return;
    }

    try {
      const response = await fetch(
        `/api/annotators/payouts/${payoutId}/cancel`,
        {
          method: "POST",
          credentials: "include",
        }
      );

      if (response.ok) {
        toast?.show({
          message: "Payout request cancelled",
          type: ToastType.info,
          duration: 3000,
        });
        fetchData();
      } else {
        throw new Error("Failed to cancel");
      }
    } catch (error) {
      toast?.show({
        message: "Failed to cancel payout",
        type: ToastType.error,
        duration: 3000,
      });
    }
  };

  if (loading) {
    return (
      <div className="payout-loading">
        <div className="spinner" />
        <p>Loading...</p>
      </div>
    );
  }

  const hasPendingPayout = payoutHistory.some(
    (p) => p.status === "pending" || p.status === "processing"
  );

  return (
    <div className="payout-page">
      <header className="payout-header">
        <button
          className="back-btn"
          onClick={() => history.push("/annotators/earnings")}
        >
          ← Back to Earnings
        </button>
        <h1>💸 Request Payout</h1>
      </header>

      {/* Balance Info */}
      <div className="balance-info-card">
        <div className="balance-item">
          <span className="label">Available Balance</span>
          <span className="value">
            {formatCurrency(earnings?.available_balance || 0)}
          </span>
        </div>
        <div className="balance-item">
          <span className="label">Pending Approval</span>
          <span className="value pending">
            {formatCurrency(earnings?.pending_approval || 0)}
          </span>
        </div>
        <div className="balance-item">
          <span className="label">Minimum Payout</span>
          <span className="value">{formatCurrency(MINIMUM_PAYOUT)}</span>
        </div>
      </div>

      {/* Payout Request Form */}
      <div className="payout-form-card">
        <h3>New Payout Request</h3>

        {hasPendingPayout && (
          <div className="pending-notice">
            ⏳ You have a pending payout request. Please wait for it to be
            processed.
          </div>
        )}

        {!hasPendingPayout && (
          <>
            <div className="form-group">
              <label>Amount (₹)</label>
              <input
                type="number"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                placeholder={`Min: ${MINIMUM_PAYOUT}`}
                min={MINIMUM_PAYOUT}
                max={earnings?.available_balance || 0}
              />
              {amount &&
                parseFloat(amount) > (earnings?.available_balance || 0) && (
                  <span className="error-text">Exceeds available balance</span>
                )}
            </div>

            <div className="form-group">
              <label>Payout Method</label>
              <div className="method-options">
                <label
                  className={`method-option ${
                    payoutMethod === "bank_transfer" ? "selected" : ""
                  }`}
                >
                  <input
                    type="radio"
                    name="payout_method"
                    value="bank_transfer"
                    checked={payoutMethod === "bank_transfer"}
                    onChange={() => setPayoutMethod("bank_transfer")}
                  />
                  <span className="method-icon">🏦</span>
                  <span className="method-label">Bank Transfer</span>
                  {bankDetails?.has_bank_details && (
                    <span className="method-check">✓</span>
                  )}
                </label>
                <label
                  className={`method-option ${
                    payoutMethod === "upi" ? "selected" : ""
                  }`}
                >
                  <input
                    type="radio"
                    name="payout_method"
                    value="upi"
                    checked={payoutMethod === "upi"}
                    onChange={() => setPayoutMethod("upi")}
                  />
                  <span className="method-icon">📱</span>
                  <span className="method-label">UPI</span>
                  {bankDetails?.has_upi && (
                    <span className="method-check">✓</span>
                  )}
                </label>
              </div>
            </div>

            {/* Bank Details Summary */}
            <div className="bank-details-summary">
              {payoutMethod === "bank_transfer" &&
                (bankDetails?.has_bank_details ? (
                  <div className="details-display">
                    <p>
                      <strong>Bank:</strong> {bankDetails.bank_name}
                    </p>
                    <p>
                      <strong>Account:</strong> {bankDetails.account_number}
                    </p>
                    <p>
                      <strong>IFSC:</strong> {bankDetails.ifsc_code}
                    </p>
                    <Button
                      look="outlined"
                      size="small"
                      onClick={() => setShowBankForm(true)}
                    >
                      Edit Details
                    </Button>
                  </div>
                ) : (
                  <div className="no-details">
                    <p>No bank details on file</p>
                    <Button onClick={() => setShowBankForm(true)}>
                      Add Bank Details
                    </Button>
                  </div>
                ))}

              {payoutMethod === "upi" &&
                (bankDetails?.has_upi ? (
                  <div className="details-display">
                    <p>
                      <strong>UPI ID:</strong> {bankDetails.upi_id}
                    </p>
                    <Button
                      look="outlined"
                      size="small"
                      onClick={() => setShowBankForm(true)}
                    >
                      Edit UPI
                    </Button>
                  </div>
                ) : (
                  <div className="no-details">
                    <p>No UPI ID on file</p>
                    <Button onClick={() => setShowBankForm(true)}>
                      Add UPI ID
                    </Button>
                  </div>
                ))}
            </div>

            <Button
              onClick={submitPayoutRequest}
              disabled={
                submitting ||
                !amount ||
                parseFloat(amount) > (earnings?.available_balance || 0)
              }
              style={{ width: "100%", marginTop: "1rem" }}
            >
              {submitting ? "Submitting..." : "Submit Payout Request"}
            </Button>
          </>
        )}
      </div>

      {/* Bank Details Form Modal */}
      {showBankForm && (
        <div className="modal-overlay" onClick={() => setShowBankForm(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h3>💳 Update Payment Details</h3>

            <div className="bank-form">
              <h4>Bank Account</h4>
              <div className="form-group">
                <label>Bank Name</label>
                <input
                  type="text"
                  name="bank_name"
                  value={bankForm.bank_name}
                  onChange={handleBankFormChange}
                  placeholder="e.g., State Bank of India"
                />
              </div>
              <div className="form-group">
                <label>Account Number</label>
                <input
                  type="text"
                  name="account_number"
                  value={bankForm.account_number}
                  onChange={handleBankFormChange}
                  placeholder="Enter full account number"
                />
              </div>
              <div className="form-group">
                <label>IFSC Code</label>
                <input
                  type="text"
                  name="ifsc_code"
                  value={bankForm.ifsc_code}
                  onChange={handleBankFormChange}
                  placeholder="e.g., SBIN0001234"
                />
              </div>
              <div className="form-group">
                <label>Account Holder Name</label>
                <input
                  type="text"
                  name="account_holder_name"
                  value={bankForm.account_holder_name}
                  onChange={handleBankFormChange}
                  placeholder="Name as per bank records"
                />
              </div>

              <h4>UPI</h4>
              <div className="form-group">
                <label>UPI ID</label>
                <input
                  type="text"
                  name="upi_id"
                  value={bankForm.upi_id}
                  onChange={handleBankFormChange}
                  placeholder="e.g., name@upi"
                />
              </div>

              <div className="modal-actions">
                <Button look="outlined" onClick={() => setShowBankForm(false)}>
                  Cancel
                </Button>
                <Button onClick={saveBankDetails}>Save Details</Button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Payout History */}
      <div className="payout-history">
        <h3>Payout History</h3>

        {payoutHistory.length === 0 ? (
          <div className="no-history">
            <p>No payout requests yet</p>
          </div>
        ) : (
          <div className="history-list">
            {payoutHistory.map((payout) => (
              <div key={payout.id} className="history-item">
                <div
                  className="history-icon"
                  style={{ color: STATUS_COLORS[payout.status] }}
                >
                  {STATUS_ICONS[payout.status]}
                </div>
                <div className="history-details">
                  <div className="history-amount">
                    {formatCurrency(payout.amount)}
                  </div>
                  <div className="history-meta">
                    <span className="method">
                      {payout.payout_method === "bank_transfer"
                        ? "🏦 Bank"
                        : "📱 UPI"}
                    </span>
                    <span className="date">
                      {formatDate(payout.requested_at)}
                    </span>
                  </div>
                  {payout.transaction_id && (
                    <div className="tx-id">Ref: {payout.transaction_id}</div>
                  )}
                  {payout.failure_reason && (
                    <div className="failure-reason">
                      ⚠️ {payout.failure_reason}
                    </div>
                  )}
                </div>
                <div className="history-status">
                  <span
                    className="status-badge"
                    style={{ backgroundColor: STATUS_COLORS[payout.status] }}
                  >
                    {payout.status}
                  </span>
                  {payout.status === "pending" && (
                    <button
                      className="cancel-btn"
                      onClick={() => cancelPayout(payout.id)}
                    >
                      Cancel
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

