"""
Razorpay payment integration utilities
"""

import razorpay
import logging
from django.conf import settings
import hmac
import hashlib

logger = logging.getLogger(__name__)


def get_razorpay_client():
    """Initialize and return Razorpay client"""
    key_id = getattr(settings, "RAZORPAY_KEY_ID", "")
    key_secret = getattr(settings, "RAZORPAY_KEY_SECRET", "")

    if not key_id or not key_secret:
        raise ValueError("Razorpay credentials not configured")

    return razorpay.Client(auth=(key_id, key_secret))


def create_razorpay_order(amount_inr, currency="INR", receipt=None, notes=None):
    """
    Create a Razorpay order

    Args:
        amount_inr: Amount in INR
        currency: Currency code (default: INR)
        receipt: Receipt ID for reference
        notes: Additional notes dictionary

    Returns:
        dict: Razorpay order details
    """
    client = get_razorpay_client()

    # Razorpay expects amount in paise (smallest currency unit)
    amount_paise = int(float(amount_inr) * 100)

    order_data = {
        "amount": amount_paise,
        "currency": currency,
        "receipt": receipt or "",
        "notes": notes or {},
    }

    order = client.order.create(data=order_data)
    return order


def verify_payment_signature(order_id, payment_id, signature):
    """
    Verify Razorpay payment signature

    Args:
        order_id: Razorpay order ID
        payment_id: Razorpay payment ID
        signature: Signature to verify

    Returns:
        bool: True if signature is valid
    """
    client = get_razorpay_client()

    params_dict = {
        "razorpay_order_id": order_id,
        "razorpay_payment_id": payment_id,
        "razorpay_signature": signature,
    }

    try:
        client.utility.verify_payment_signature(params_dict)
        return True
    except razorpay.errors.SignatureVerificationError:
        return False


def create_razorpay_customer(email, name, contact=None):
    """
    Create a Razorpay customer or fetch existing one

    Args:
        email: Customer email
        name: Customer name
        contact: Customer phone number

    Returns:
        dict: Customer details with customer_id
    """
    client = get_razorpay_client()

    # First try to find existing customer by email
    try:
        # Search for existing customers with this email
        customers = client.customer.all({"count": 100})
        for customer in customers.get("items", []):
            if customer.get("email", "").lower() == email.lower():
                logger.info(f"Found existing Razorpay customer: {customer['id']}")
                return customer
    except Exception as e:
        logger.warning(f"Error searching for existing customer: {e}")

    # Create new customer if not found
    customer_data = {
        "email": email,
        "name": name,
        "fail_existing": "0",  # String '0' for false
    }

    if contact:
        customer_data["contact"] = contact

    try:
        customer = client.customer.create(data=customer_data)
        return customer
    except razorpay.errors.BadRequestError as e:
        # If customer already exists error, try to fetch by email
        error_msg = str(e)
        if "already exists" in error_msg.lower():
            logger.info(f"Customer exists, searching for email: {email}")
            customers = client.customer.all({"count": 100})
            for customer in customers.get("items", []):
                if customer.get("email", "").lower() == email.lower():
                    return customer
        raise


def create_razorpay_subscription(
    plan_id, customer_id, total_count=None, start_at=None, notes=None
):
    """
    Create a Razorpay subscription

    Args:
        plan_id: Razorpay plan ID
        customer_id: Razorpay customer ID
        total_count: Total billing cycles
        start_at: Subscription start timestamp
        notes: Additional notes

    Returns:
        dict: Subscription details
    """
    client = get_razorpay_client()

    subscription_data = {
        "plan_id": plan_id,
        "customer_id": customer_id,
        "quantity": 1,
        "notes": notes or {},
    }

    if total_count:
        subscription_data["total_count"] = total_count

    if start_at:
        subscription_data["start_at"] = start_at

    subscription = client.subscription.create(data=subscription_data)
    return subscription


def fetch_payment(payment_id):
    """Fetch payment details from Razorpay"""
    client = get_razorpay_client()
    return client.payment.fetch(payment_id)


def capture_payment(payment_id, amount_inr):
    """
    Capture authorized payment

    Args:
        payment_id: Razorpay payment ID
        amount_inr: Amount to capture in INR

    Returns:
        dict: Payment details
    """
    client = get_razorpay_client()
    amount_paise = int(float(amount_inr) * 100)
    return client.payment.capture(payment_id, amount_paise)


def refund_payment(payment_id, amount_inr=None):
    """
    Refund a payment

    Args:
        payment_id: Razorpay payment ID
        amount_inr: Amount to refund (None for full refund)

    Returns:
        dict: Refund details
    """
    client = get_razorpay_client()

    refund_data = {}
    if amount_inr:
        refund_data["amount"] = int(float(amount_inr) * 100)

    return client.payment.refund(payment_id, refund_data)


def fetch_order(order_id):
    """
    Fetch order details from Razorpay

    Args:
        order_id: Razorpay order ID

    Returns:
        dict: Order details with notes
    """
    client = get_razorpay_client()
    return client.order.fetch(order_id)


def cancel_subscription(subscription_id):
    """Cancel a Razorpay subscription"""
    client = get_razorpay_client()
    return client.subscription.cancel(subscription_id)





