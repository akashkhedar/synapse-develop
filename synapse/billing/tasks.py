"""
Periodic tasks for billing operations.
These should be scheduled via Celery, RQ, or cron.

Recommended schedule:
- process_project_lifecycle: Daily at 00:30 UTC
- charge_api_overage: Daily at 00:15 UTC
- charge_storage_billing: Monthly on 1st at 01:00 UTC
- expire_credits: Daily at 00:45 UTC
- cleanup_deleted_projects: Weekly on Sunday at 02:00 UTC
"""

import logging
from datetime import timedelta
from django.utils import timezone
from django.db import transaction
from django_rq import job

logger = logging.getLogger(__name__)


@job("default", timeout=1800)
def process_project_lifecycle():
    """
    Daily task to check and update project lifecycle states.

    This task:
    1. Marks inactive projects as dormant (30 days)
    2. Sends warning emails for low-credit projects
    3. Starts grace period for zero-credit organizations
    4. Deletes projects after grace period expires

    Returns:
        dict: Processing summary
    """
    from billing.services import ProjectLifecycleService

    logger.info("Starting project lifecycle processing...")

    try:
        summary = ProjectLifecycleService.process_all_projects()
        logger.info(f"Project lifecycle processing complete: {summary}")
        return summary
    except Exception as e:
        logger.error(f"Error in project lifecycle processing: {e}", exc_info=True)
        return {"error": str(e)}


@job("default", timeout=600)
def charge_api_overage():
    """
    Daily task to charge organizations for API overage from previous day.

    Should run shortly after midnight to process previous day's usage.

    Returns:
        dict: Charging summary
    """
    from billing.services import APIRateLimitService
    from billing.models import APIUsageTracking
    from organizations.models import Organization

    logger.info("Starting API overage billing...")

    yesterday = (timezone.now() - timedelta(days=1)).date()

    summary = {
        "date": str(yesterday),
        "organizations_processed": 0,
        "total_charged": 0,
        "errors": [],
    }

    # Get all organizations with usage yesterday
    usage_records = APIUsageTracking.objects.filter(
        date=yesterday, charged_at__isnull=True
    ).select_related("organization")

    for usage in usage_records:
        try:
            result = APIRateLimitService.charge_daily_overage(
                usage.organization, yesterday
            )

            summary["organizations_processed"] += 1
            if result.get("success") and result.get("credits_charged", 0) > 0:
                summary["total_charged"] += result["credits_charged"]

        except Exception as e:
            summary["errors"].append(
                {"organization_id": usage.organization.id, "error": str(e)}
            )
            logger.error(
                f"Error charging API overage for org {usage.organization.id}: {e}"
            )

    logger.info(f"API overage billing complete: {summary}")
    return summary


@job("default", timeout=1800)
def charge_storage_billing():
    """
    Monthly task to charge organizations for storage usage.

    Should run on 1st of each month.

    Returns:
        dict: Billing summary
    """
    from billing.services import StorageService
    from organizations.models import Organization

    logger.info("Starting monthly storage billing...")

    # Get first day of current month
    today = timezone.now().date()
    billing_month = today.replace(day=1)

    summary = {
        "billing_month": str(billing_month),
        "organizations_processed": 0,
        "total_storage_gb": 0,
        "total_charged": 0,
        "errors": [],
    }

    # Process all organizations
    organizations = Organization.objects.filter(is_active=True)

    for org in organizations:
        try:
            credits_charged = StorageService.charge_storage(org, billing_month)

            summary["organizations_processed"] += 1
            summary["total_charged"] += float(credits_charged)

        except Exception as e:
            summary["errors"].append({"organization_id": org.id, "error": str(e)})
            logger.error(f"Error charging storage for org {org.id}: {e}")

    logger.info(f"Monthly storage billing complete: {summary}")
    return summary


@job("default", timeout=600)
def expire_credits():
    """
    Daily task to expire bonus/promotional credits.

    Credit expiry policy:
    - Purchased credits: Never expire
    - Bonus credits: 90 days
    - Rollover credits: 30 days

    Returns:
        dict: Expiry summary
    """
    from billing.models import CreditExpiry, OrganizationBilling, CreditTransaction
    from decimal import Decimal

    logger.info("Starting credit expiry processing...")

    now = timezone.now()

    summary = {
        "credits_expired": 0,
        "organizations_affected": set(),
        "total_expired_amount": Decimal("0"),
        "errors": [],
    }

    # Find expiring credits
    expiring = CreditExpiry.objects.filter(
        expires_at__lte=now, is_expired=False, remaining__gt=0
    ).select_related("organization")

    for credit in expiring:
        try:
            with transaction.atomic():
                # Get organization billing
                billing = credit.organization.billing

                # Calculate amount to expire
                expire_amount = min(credit.remaining, billing.available_credits)

                if expire_amount > 0:
                    # Deduct from organization
                    billing.available_credits -= expire_amount
                    billing.save()

                    # Create transaction record
                    CreditTransaction.objects.create(
                        organization=credit.organization,
                        transaction_type="debit",
                        category="rollover",  # Using rollover for expiry
                        amount=expire_amount,
                        balance_after=billing.available_credits,
                        description=f"Credit expiry: {credit.credit_type} credits expired",
                        metadata={
                            "credit_type": credit.credit_type,
                            "original_amount": float(credit.amount),
                            "expired_amount": float(expire_amount),
                        },
                    )

                    summary["total_expired_amount"] += expire_amount
                    summary["organizations_affected"].add(credit.organization.id)

                # Mark as expired
                credit.is_expired = True
                credit.expired_amount = credit.remaining
                credit.remaining = Decimal("0")
                credit.save()

                summary["credits_expired"] += 1

        except Exception as e:
            summary["errors"].append({"credit_id": credit.id, "error": str(e)})
            logger.error(f"Error expiring credit {credit.id}: {e}")

    summary["organizations_affected"] = len(summary["organizations_affected"])
    summary["total_expired_amount"] = float(summary["total_expired_amount"])

    logger.info(f"Credit expiry processing complete: {summary}")
    return summary


@job("default", timeout=1800)
def cleanup_deleted_projects():
    """
    Weekly task to permanently delete projects marked for deletion.

    This actually removes data after projects have been in DELETED state
    for a configured retention period (e.g., 7 days after state change).

    Returns:
        dict: Cleanup summary
    """
    from billing.models import ProjectBilling
    from projects.models import Project

    logger.info("Starting deleted project cleanup...")

    # Projects deleted more than 7 days ago
    cutoff = timezone.now() - timedelta(days=7)

    summary = {"projects_cleaned": 0, "storage_freed_gb": 0, "errors": []}

    deleted_billings = ProjectBilling.objects.filter(
        state=ProjectBilling.ProjectState.DELETED, state_changed_at__lte=cutoff
    ).select_related("project")

    for pb in deleted_billings:
        try:
            project = pb.project
            storage_gb = float(pb.storage_used_gb)

            logger.info(f"Cleaning up project {project.id}: {project.title}")

            # TODO: Implement actual data deletion
            # - Delete tasks
            # - Delete files from storage
            # - Delete annotations
            # - Archive or delete project

            # For now, we just mark as cleaned
            # project.delete()  # Uncomment to actually delete

            summary["projects_cleaned"] += 1
            summary["storage_freed_gb"] += storage_gb

        except Exception as e:
            summary["errors"].append({"project_id": pb.project.id, "error": str(e)})
            logger.error(f"Error cleaning up project {pb.project.id}: {e}")

    logger.info(f"Deleted project cleanup complete: {summary}")
    return summary


@job("default", timeout=600)
def send_billing_reminders():
    """
    Daily task to send billing-related reminder emails.

    Sends reminders for:
    - Low credit balance
    - Approaching storage limits
    - Projects in warning/grace state
    - Upcoming subscription renewal

    Returns:
        dict: Reminder summary
    """
    from billing.models import ProjectBilling, OrganizationBilling
    from organizations.models import Organization

    logger.info("Starting billing reminder processing...")

    summary = {
        "low_credit_reminders": 0,
        "grace_period_reminders": 0,
        "storage_warnings": 0,
        "errors": [],
    }

    # Find organizations with low credits
    low_credit_orgs = OrganizationBilling.objects.filter(
        available_credits__lt=100, available_credits__gt=0
    ).select_related("organization")

    for billing in low_credit_orgs:
        try:
            # TODO: Implement email sending
            # send_low_credit_reminder_email(billing.organization, billing.available_credits)
            logger.info(
                f"[REMINDER] Low credits for {billing.organization.title}: "
                f"₹{billing.available_credits} remaining"
            )
            summary["low_credit_reminders"] += 1
        except Exception as e:
            summary["errors"].append({"type": "low_credit", "error": str(e)})

    # Find projects in grace period
    grace_projects = ProjectBilling.objects.filter(
        state=ProjectBilling.ProjectState.GRACE
    ).select_related("project", "project__organization")

    for pb in grace_projects:
        try:
            days_remaining = 0
            if pb.scheduled_deletion_at:
                days_remaining = (pb.scheduled_deletion_at - timezone.now()).days

            # TODO: Implement email sending
            # send_grace_period_reminder_email(pb.project, days_remaining)
            logger.info(
                f"[REMINDER] Project {pb.project.title} in grace period: "
                f"{days_remaining} days until deletion"
            )
            summary["grace_period_reminders"] += 1
        except Exception as e:
            summary["errors"].append({"type": "grace_period", "error": str(e)})

    logger.info(f"Billing reminder processing complete: {summary}")
    return summary


# RQ/Celery compatible task wrappers
def run_daily_billing_tasks():
    """
    Master task that runs all daily billing tasks.
    Schedule this once at midnight.
    """
    logger.info("Running all daily billing tasks...")

    results = {
        "api_overage": charge_api_overage(),
        "project_lifecycle": process_project_lifecycle(),
        "credit_expiry": expire_credits(),
        "reminders": send_billing_reminders(),
    }

    logger.info(f"Daily billing tasks complete: {results}")
    return results


def run_monthly_billing_tasks():
    """
    Master task that runs all monthly billing tasks.
    Schedule this on the 1st of each month.
    """
    logger.info("Running all monthly billing tasks...")

    results = {
        "storage_billing": charge_storage_billing(),
    }

    logger.info(f"Monthly billing tasks complete: {results}")
    return results


def run_weekly_cleanup_tasks():
    """
    Master task that runs all weekly cleanup tasks.
    Schedule this on Sundays.
    """
    logger.info("Running all weekly cleanup tasks...")

    results = {
        "deleted_projects": cleanup_deleted_projects(),
    }

    logger.info(f"Weekly cleanup tasks complete: {results}")
    return results





