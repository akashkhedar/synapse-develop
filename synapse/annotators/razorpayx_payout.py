"""
RazorpayX Payout Integration for Annotator Payments

RazorpayX is Razorpay's business banking platform for sending money.
This module handles payouts to annotators via bank transfer or UPI.

API Documentation: https://razorpay.com/docs/razorpayx/api/payouts/

Required Settings:
    RAZORPAY_KEY_ID: Your Razorpay API Key ID
    RAZORPAY_KEY_SECRET: Your Razorpay API Key Secret
    RAZORPAYX_ACCOUNT_NUMBER: Your RazorpayX business account number

TEST MODE:
    - Test API keys start with 'rzp_test_'
    - Use test bank account numbers for testing payouts
    - No real money is transferred in test mode
"""

import razorpay
import logging
import uuid
from decimal import Decimal
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


# ============================================================================
# TEST MODE CONFIGURATION
# ============================================================================

# Razorpay Test Bank Accounts for testing payouts
# These are provided by Razorpay for testing purposes
TEST_BANK_ACCOUNTS = {
    "success": {
        "account_number": "1111111111111",
        "ifsc_code": "RATN0VAAPIS",
        "account_holder_name": "Test Account Success",
        "description": "Payout will be processed successfully",
    },
    "pending": {
        "account_number": "1111111111112",
        "ifsc_code": "RATN0VAAPIS",
        "account_holder_name": "Test Account Pending",
        "description": "Payout will remain in processing state",
    },
    "failed": {
        "account_number": "1111111111113",
        "ifsc_code": "RATN0VAAPIS",
        "account_holder_name": "Test Account Failed",
        "description": "Payout will fail with insufficient balance",
    },
    "reversed": {
        "account_number": "1111111111114",
        "ifsc_code": "RATN0VAAPIS",
        "account_holder_name": "Test Account Reversed",
        "description": "Payout will be reversed after processing",
    },
}

# Razorpay Test UPI IDs for testing payouts
TEST_UPI_IDS = {
    "success": "success@razorpay",
    "pending": "pending@razorpay",
    "failed": "failed@razorpay",
}


def is_test_mode():
    """Check if Razorpay is running in test mode"""
    key_id = getattr(settings, "RAZORPAY_KEY_ID", "")
    return key_id.startswith("rzp_test_")


def get_test_mode_info():
    """Get test mode configuration info"""
    return {
        "is_test_mode": is_test_mode(),
        "test_bank_accounts": TEST_BANK_ACCOUNTS,
        "test_upi_ids": TEST_UPI_IDS,
        "note": "In test mode, use these test bank accounts/UPI IDs for testing. No real money is transferred.",
    }


class RazorpayXPayoutError(Exception):
    """Exception for RazorpayX payout errors"""

    def __init__(self, message, error_code=None, razorpay_response=None):
        self.message = message
        self.error_code = error_code
        self.razorpay_response = razorpay_response
        super().__init__(self.message)


def get_razorpayx_client():
    """Initialize and return Razorpay client for RazorpayX"""
    key_id = getattr(settings, "RAZORPAY_KEY_ID", "")
    key_secret = getattr(settings, "RAZORPAY_KEY_SECRET", "")

    if not key_id or not key_secret:
        raise RazorpayXPayoutError("Razorpay credentials not configured")

    return razorpay.Client(auth=(key_id, key_secret))


def get_razorpayx_account_number():
    """Get RazorpayX account number from settings"""
    account_number = getattr(settings, "RAZORPAYX_ACCOUNT_NUMBER", "")
    if not account_number:
        raise RazorpayXPayoutError("RazorpayX account number not configured")
    return account_number


def create_fund_account_bank(
    contact_id, account_holder_name, account_number, ifsc_code
):
    """
    Create a fund account for bank transfer

    Args:
        contact_id: RazorpayX contact ID
        account_holder_name: Name on the bank account
        account_number: Bank account number
        ifsc_code: Bank IFSC code

    Returns:
        dict: Fund account details with fund_account_id
    """
    client = get_razorpayx_client()

    try:
        fund_account = client.fund_account.create(
            {
                "contact_id": contact_id,
                "account_type": "bank_account",
                "bank_account": {
                    "name": account_holder_name,
                    "ifsc": ifsc_code,
                    "account_number": account_number,
                },
            }
        )
        logger.info(f"Created bank fund account: {fund_account.get('id')}")
        return fund_account
    except razorpay.errors.BadRequestError as e:
        logger.error(f"Failed to create bank fund account: {e}")
        raise RazorpayXPayoutError(
            f"Invalid bank details: {e}", razorpay_response=str(e)
        )


def create_fund_account_vpa(contact_id, vpa_address):
    """
    Create a fund account for UPI/VPA transfer

    Args:
        contact_id: RazorpayX contact ID
        vpa_address: UPI VPA address (e.g., user@upi)

    Returns:
        dict: Fund account details with fund_account_id
    """
    client = get_razorpayx_client()

    try:
        fund_account = client.fund_account.create(
            {
                "contact_id": contact_id,
                "account_type": "vpa",
                "vpa": {
                    "address": vpa_address,
                },
            }
        )
        logger.info(f"Created VPA fund account: {fund_account.get('id')}")
        return fund_account
    except razorpay.errors.BadRequestError as e:
        logger.error(f"Failed to create VPA fund account: {e}")
        raise RazorpayXPayoutError(
            f"Invalid UPI address: {e}", razorpay_response=str(e)
        )


def create_contact(name, email, contact_type="employee", reference_id=None, notes=None):
    """
    Create a RazorpayX contact (payee)

    Args:
        name: Contact name
        email: Contact email
        contact_type: Type of contact (employee, vendor, customer, self)
        reference_id: Your internal reference ID
        notes: Additional notes dict

    Returns:
        dict: Contact details with contact_id
    """
    client = get_razorpayx_client()

    contact_data = {
        "name": name,
        "email": email,
        "type": contact_type,
    }

    if reference_id:
        contact_data["reference_id"] = reference_id

    if notes:
        contact_data["notes"] = notes

    try:
        contact = client.contact.create(contact_data)
        logger.info(f"Created contact: {contact.get('id')} for {email}")
        return contact
    except razorpay.errors.BadRequestError as e:
        logger.error(f"Failed to create contact: {e}")
        raise RazorpayXPayoutError(
            f"Failed to create contact: {e}", razorpay_response=str(e)
        )


def get_or_create_contact(name, email, reference_id=None):
    """
    Get existing contact or create a new one

    Args:
        name: Contact name
        email: Contact email
        reference_id: Your internal reference ID

    Returns:
        dict: Contact details
    """
    client = get_razorpayx_client()

    # Try to find existing contact by reference_id or email
    try:
        if reference_id:
            contacts = client.contact.all({"reference_id": reference_id})
            if contacts.get("items"):
                return contacts["items"][0]

        # Search by email in notes or create new
        # RazorpayX doesn't support email search, so we create with reference_id
        return create_contact(
            name=name,
            email=email,
            contact_type="employee",
            reference_id=reference_id or f"annotator_{email.replace('@', '_at_')}",
            notes={"email": email},
        )
    except Exception as e:
        logger.warning(f"Error finding contact, creating new: {e}")
        return create_contact(
            name=name,
            email=email,
            contact_type="employee",
            reference_id=reference_id or f"annotator_{email.replace('@', '_at_')}",
        )


def create_payout(
    fund_account_id,
    amount_inr,
    purpose="payout",
    mode="IMPS",
    reference_id=None,
    narration=None,
    notes=None,
    queue_if_low_balance=True,
):
    """
    Create a payout to transfer money

    Args:
        fund_account_id: RazorpayX fund account ID
        amount_inr: Amount in INR (Decimal or float)
        purpose: Purpose of payout (payout, salary, refund, cashback, vendor_bill, vendor_advance)
        mode: Transfer mode (IMPS, NEFT, RTGS, UPI)
        reference_id: Your internal reference ID
        narration: Description that appears on bank statement
        notes: Additional notes dict
        queue_if_low_balance: If True, queue the payout if insufficient balance

    Returns:
        dict: Payout details with payout_id and status
    """
    client = get_razorpayx_client()
    account_number = get_razorpayx_account_number()

    # Convert to paise
    amount_paise = int(float(amount_inr) * 100)

    payout_data = {
        "account_number": account_number,
        "fund_account_id": fund_account_id,
        "amount": amount_paise,
        "currency": "INR",
        "mode": mode,
        "purpose": purpose,
        "queue_if_low_balance": queue_if_low_balance,
    }

    if reference_id:
        payout_data["reference_id"] = reference_id

    if narration:
        payout_data["narration"] = narration[:30]  # Max 30 chars

    if notes:
        payout_data["notes"] = notes

    try:
        payout = client.payout.create(payout_data)
        logger.info(f"Created payout: {payout.get('id')} for ₹{amount_inr}")
        return payout
    except razorpay.errors.BadRequestError as e:
        logger.error(f"Failed to create payout: {e}")
        raise RazorpayXPayoutError(f"Payout failed: {e}", razorpay_response=str(e))


def get_payout(payout_id):
    """
    Fetch payout details

    Args:
        payout_id: RazorpayX payout ID

    Returns:
        dict: Payout details with status
    """
    client = get_razorpayx_client()
    return client.payout.fetch(payout_id)


def cancel_payout(payout_id):
    """
    Cancel a queued payout

    Args:
        payout_id: RazorpayX payout ID

    Returns:
        dict: Updated payout details
    """
    client = get_razorpayx_client()
    return client.payout.cancel(payout_id)


def process_annotator_payout(payout_request):
    """
    Process an annotator payout request via RazorpayX

    Args:
        payout_request: PayoutRequest model instance

    Returns:
        dict: Result with success status and details
    """
    annotator = payout_request.annotator
    user = annotator.user
    amount = payout_request.amount
    payout_method = payout_request.payout_method
    bank_details = payout_request.bank_details

    try:
        # Step 1: Get or create contact
        contact = get_or_create_contact(
            name=user.get_full_name() or user.email,
            email=user.email,
            reference_id=f"annotator_{annotator.id}",
        )
        contact_id = contact["id"]

        # Step 2: Create fund account based on payout method
        if payout_method == "upi":
            upi_id = bank_details.get("upi_id")
            if not upi_id:
                return {"success": False, "error": "UPI ID not found"}

            fund_account = create_fund_account_vpa(contact_id, upi_id)
            transfer_mode = "UPI"
        else:
            # Bank transfer
            account_number = bank_details.get("account_number")
            ifsc_code = bank_details.get("ifsc_code")
            account_holder_name = bank_details.get(
                "account_holder_name", user.get_full_name()
            )

            if not account_number or not ifsc_code:
                return {"success": False, "error": "Bank details incomplete"}

            fund_account = create_fund_account_bank(
                contact_id=contact_id,
                account_holder_name=account_holder_name,
                account_number=account_number,
                ifsc_code=ifsc_code,
            )
            transfer_mode = "IMPS"

        fund_account_id = fund_account["id"]

        # Step 3: Create payout
        payout = create_payout(
            fund_account_id=fund_account_id,
            amount_inr=amount,
            purpose="payout",
            mode=transfer_mode,
            reference_id=f"payout_{payout_request.id}_{uuid.uuid4().hex[:8]}",
            narration=f"Synapse Payout #{payout_request.id}",
            notes={
                "payout_request_id": str(payout_request.id),
                "annotator_id": str(annotator.id),
                "email": user.email,
            },
        )

        # Update payout request with transaction details
        payout_request.transaction_id = payout["id"]
        payout_request.status = "processing"
        payout_request.save(update_fields=["transaction_id", "status"])

        return {
            "success": True,
            "payout_id": payout["id"],
            "status": payout.get("status"),
            "utr": payout.get("utr"),
        }

    except RazorpayXPayoutError as e:
        logger.error(f"Payout failed for request {payout_request.id}: {e}")
        return {
            "success": False,
            "error": str(e),
        }
    except Exception as e:
        logger.error(f"Unexpected error in payout {payout_request.id}: {e}")
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}",
        }


def create_test_payout(email, name, upi_id=None, bank_details=None, amount_inr=1):
    """
    Create a test payout of ₹1 to verify the integration

    Args:
        email: Recipient email
        name: Recipient name
        upi_id: UPI ID (if using UPI)
        bank_details: Dict with account_number, ifsc_code, account_holder_name (if using bank)
        amount_inr: Amount in INR (default ₹1)

    Returns:
        dict: Payout result
    """
    try:
        # Create contact
        contact = get_or_create_contact(
            name=name,
            email=email,
            reference_id=f"test_{email.replace('@', '_at_')}_{uuid.uuid4().hex[:6]}",
        )
        contact_id = contact["id"]

        # Create fund account
        if upi_id:
            fund_account = create_fund_account_vpa(contact_id, upi_id)
            mode = "UPI"
        elif bank_details:
            fund_account = create_fund_account_bank(
                contact_id=contact_id,
                account_holder_name=bank_details.get("account_holder_name", name),
                account_number=bank_details["account_number"],
                ifsc_code=bank_details["ifsc_code"],
            )
            mode = "IMPS"
        else:
            return {"success": False, "error": "Provide either upi_id or bank_details"}

        fund_account_id = fund_account["id"]

        # Create payout
        payout = create_payout(
            fund_account_id=fund_account_id,
            amount_inr=amount_inr,
            purpose="payout",
            mode=mode,
            reference_id=f"test_payout_{uuid.uuid4().hex[:8]}",
            narration="Synapse Test Payout",
            notes={"type": "test_payout", "email": email},
        )

        return {
            "success": True,
            "payout_id": payout["id"],
            "status": payout.get("status"),
            "amount": amount_inr,
            "mode": mode,
        }

    except RazorpayXPayoutError as e:
        return {"success": False, "error": str(e)}
    except Exception as e:
        return {"success": False, "error": f"Unexpected error: {str(e)}"}


def get_account_balance():
    """
    Get RazorpayX account balance

    Returns:
        dict: Balance details
    """
    client = get_razorpayx_client()
    account_number = get_razorpayx_account_number()

    try:
        balance = client.balance.fetch(account_number)
        return {
            "balance": balance.get("balance", 0) / 100,  # Convert from paise
            "currency": balance.get("currency", "INR"),
        }
    except Exception as e:
        logger.error(f"Failed to fetch balance: {e}")
        return {"balance": 0, "currency": "INR", "error": str(e)}





