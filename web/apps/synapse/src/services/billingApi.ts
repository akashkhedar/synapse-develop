/**
 * Billing and Payment API Service
 */

// Helper function to make raw HTTP calls for billing endpoints
// These endpoints are at /api/billing/... and don't go through the API proxy gateway
const fetchApi = async <T>(
  url: string,
  options: RequestInit = {}
): Promise<T> => {
  // Direct fetch without using the API gateway prefix
  const response = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
    credentials: "include",
  });

  if (!response.ok) {
    const error = await response
      .json()
      .catch(() => ({ detail: "Request failed" }));
    throw new Error(error.detail || error.message || `HTTP ${response.status}`);
  }

  return response.json();
};

export interface SubscriptionPlan {
  id: number;
  name: string;
  plan_type: "starter" | "growth" | "scale" | "enterprise";
  billing_cycle: "monthly" | "annual";
  price_inr: number;
  credits_per_month: number;
  effective_rate: number;
  storage_gb: number;
  extra_storage_rate_per_gb: number;
  max_users: number | null;
  priority_support: boolean;
  api_access: boolean;
  credit_rollover: boolean;
  max_rollover_months: number;
  is_active: boolean;
}

export interface CreditPackage {
  id: number;
  name: string;
  credits: number;
  price_inr: number;
  rate_per_credit: number;
  is_active: boolean;
}

export interface OrganizationBilling {
  id: number;
  organization: number;
  organization_name: string;
  billing_type: "payg" | "subscription";
  available_credits: number;
  rollover_credits: number;
  storage_used_gb: number;
  active_subscription: number | null;
  active_subscription_details: any;
  billing_email: string;
  gstin: string;
  created_at: string;
}

export interface CreditTransaction {
  id: number;
  organization: number;
  organization_name: string;
  transaction_type: "credit" | "debit";
  category:
    | "purchase"
    | "subscription"
    | "annotation"
    | "storage"
    | "refund"
    | "rollover"
    | "bonus";
  amount: number;
  balance_after: number;
  description: string;
  metadata: any;
  created_at: string;
  created_by: number | null;
  created_by_email: string | null;
}

export interface Payment {
  id: number;
  organization: number;
  organization_name: string;
  payment_for: "credits" | "subscription";
  credit_package: number | null;
  credit_package_details: CreditPackage | null;
  subscription: number | null;
  amount_inr: number;
  status: "pending" | "authorized" | "captured" | "refunded" | "failed";
  razorpay_order_id: string;
  razorpay_payment_id: string;
  payment_method: string;
  created_at: string;
  paid_at: string | null;
}

export interface AnnotationPricing {
  id: number;
  data_type: string;
  modality: string;
  base_credit: number;
  unit_description: string;
  classification_credit: number | null;
  bounding_box_credit: number | null;
  segmentation_credit: number | null;
  keypoint_credit: number | null;
  polygon_credit: number | null;
  time_sequence_credit: number | null;
  is_active: boolean;
}

export interface BillingDashboard {
  billing: OrganizationBilling;
  recent_transactions: CreditTransaction[];
  recent_payments: Payment[];
}

export interface CreateOrderRequest {
  payment_for: "credits" | "subscription";
  credit_package_id?: number;
  subscription_plan_id?: number;
}

export interface CreateOrderResponse {
  order_id: string;
  amount: number;
  currency: string;
  payment_id: number;
  description: string;
  customer_id: string;
}

export interface VerifyPaymentRequest {
  razorpay_order_id: string;
  razorpay_payment_id: string;
  razorpay_signature: string;
}

export interface VerifyPaymentResponse {
  success: boolean;
  message: string;
  payment: Payment;
}

export const billingApi = {
  /**
   * Get Razorpay public key
   */
  getRazorpayKey: async (): Promise<{ key_id: string; test_mode: boolean }> => {
    return fetchApi<{ key_id: string; test_mode: boolean }>(
      "/api/billing/razorpay_key/"
    );
  },

  /**
   * Get all subscription plans
   */
  getSubscriptionPlans: async (): Promise<SubscriptionPlan[]> => {
    return fetchApi<SubscriptionPlan[]>("/api/billing/plans/");
  },

  /**
   * Get all credit packages
   */
  getCreditPackages: async (): Promise<CreditPackage[]> => {
    return fetchApi<CreditPackage[]>("/api/billing/packages/");
  },

  /**
   * Get billing dashboard data
   */
  getDashboard: async (organizationId?: number): Promise<BillingDashboard> => {
    const params = organizationId ? `?organization=${organizationId}` : "";
    return fetchApi<BillingDashboard>(
      `/api/billing/dashboard/${params}`
    );
  },

  /**
   * Create Razorpay order
   */
  createOrder: async (
    data: CreateOrderRequest
  ): Promise<CreateOrderResponse> => {
    return fetchApi<CreateOrderResponse>("/api/billing/create_order/", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  /**
   * Verify payment
   */
  verifyPayment: async (
    data: VerifyPaymentRequest
  ): Promise<VerifyPaymentResponse> => {
    return fetchApi<VerifyPaymentResponse>(
      "/api/billing/verify_payment/",
      {
        method: "POST",
        body: JSON.stringify(data),
      }
    );
  },

  /**
   * Get credit transaction history
   */
  getTransactions: async (
    organizationId?: number,
    type?: string,
    category?: string
  ): Promise<CreditTransaction[]> => {
    const params = new URLSearchParams();
    if (organizationId)
      params.append("organization", organizationId.toString());
    if (type) params.append("type", type);
    if (category) params.append("category", category);

    const queryString = params.toString();
    const url = `/api/billing/transactions/${
      queryString ? `?${queryString}` : ""
    }`;
    return fetchApi<CreditTransaction[]>(url);
  },

  /**
   * Get payment history with pagination
   */
  getPayments: async (
    organizationId?: number,
    limit: number = 20,
    offset: number = 0
  ): Promise<{
    results: Payment[];
    count: number;
    has_more: boolean;
  }> => {
    const params = new URLSearchParams();
    if (organizationId) params.append("organization", organizationId.toString());
    params.append("limit", limit.toString());
    params.append("offset", offset.toString());

    return fetchApi<{
      results: Payment[];
      count: number;
      has_more: boolean;
    }>(`/api/billing/payments/?${params.toString()}`);
  },

  /**
   * Get annotation pricing rules
   */
  getPricingRules: async (): Promise<AnnotationPricing[]> => {
    return fetchApi<AnnotationPricing[]>("/api/billing/pricing/");
  },

  /**
   * Calculate annotation cost
   */
  calculateCost: async (
    dataType: string,
    modality: string,
    annotationType: string,
    volume: number
  ): Promise<any> => {
    return fetchApi<any>("/api/billing/pricing/calculate/", {
      method: "POST",
      body: JSON.stringify({
        data_type: dataType,
        modality: modality,
        annotation_type: annotationType,
        volume: volume,
      }),
    });
  },
};

