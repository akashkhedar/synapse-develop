"""
Periodic tasks for billing operations.
These should be scheduled via Celery, RQ, or cron.

Recommended schedule:
- process_project_lifecycle: Daily at 00:30 UTC
- charge_api_overage: Daily at 00:15 UTC
- charge_storage_billing: Monthly on 1st at 01:00 UTC
- expire_credits: Daily at 00:45 UTC
- cleanup_unpublished_projects: Hourly (fallback for abandoned project creation)
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
        "retention_monitoring": process_project_retention(),
    }

    logger.info(f"Daily billing tasks complete: {results}")
    return results


@job("default", timeout=1800)
def process_project_retention():
    """
    Daily task to process project retention billing.
    
    This task handles:
    1. Projects with annotation completed that are approaching monthly charge
    2. Sending 7-day advance notifications before charge
    3. Auto-charging retention fees
    4. Warning users with insufficient credits
    5. Scheduling project deletion for unpaid retention (3-week grace)
    6. Deleting projects that are past the deletion date
    
    Returns:
        dict: Processing summary
    """
    from billing.models import ProjectBilling, OrganizationBilling, CreditTransaction
    from datetime import timedelta
    
    logger.info("Starting project retention processing...")
    
    summary = {
        "notifications_sent": 0,
        "charges_processed": 0,
        "insufficient_credits_warnings": 0,
        "deletions_scheduled": 0,
        "projects_deleted": 0,
        "total_charged": 0,
        "errors": [],
    }
    
    now = timezone.now()
    seven_days_from_now = now + timedelta(days=7)
    
    # 1. Send 7-day advance notifications for upcoming charges
    upcoming_charges = ProjectBilling.objects.filter(
        retention_billing_started=True,
        annotation_completed=True,
        next_retention_charge_at__lte=seven_days_from_now,
        next_retention_charge_at__gt=now,
        retention_warning_sent_at__isnull=True,
        retention_deletion_scheduled_at__isnull=True,
    ).select_related('project', 'project__organization')
    
    for pb in upcoming_charges:
        try:
            # Get subscription plan for rate calculation
            org_billing = OrganizationBilling.objects.filter(
                organization=pb.project.organization
            ).first()
            subscription_plan = (
                org_billing.active_subscription.plan 
                if org_billing and org_billing.active_subscription and org_billing.active_subscription.status == 'active'
                else None
            )
            
            retention_fee = pb.calculate_monthly_retention_fee(subscription_plan)
            
            # TODO: Send email notification
            logger.info(
                f"[RETENTION NOTICE] Project '{pb.project.title}' will be charged "
                f"₹{retention_fee} for storage retention on {pb.next_retention_charge_at}"
            )
            
            pb.retention_warning_sent_at = now
            pb.save(update_fields=['retention_warning_sent_at'])
            summary["notifications_sent"] += 1
            
        except Exception as e:
            summary["errors"].append({
                "project_id": pb.project.id,
                "error": str(e),
                "type": "notification"
            })
    
    # 2. Process projects due for retention charge
    due_for_charge = ProjectBilling.objects.filter(
        retention_billing_started=True,
        annotation_completed=True,
        next_retention_charge_at__lte=now,
        retention_deletion_scheduled_at__isnull=True,
    ).select_related('project', 'project__organization')
    
    for pb in due_for_charge:
        try:
            org = pb.project.organization
            org_billing = OrganizationBilling.objects.filter(organization=org).first()
            
            if not org_billing:
                continue
                
            subscription_plan = (
                org_billing.active_subscription.plan 
                if org_billing.active_subscription and org_billing.active_subscription.status == 'active'
                else None
            )
            retention_fee = pb.calculate_monthly_retention_fee(subscription_plan)
            
            # Skip if no retention fee needed
            if retention_fee <= 0:
                pb.months_retained += 1
                pb.last_retention_charged_at = now
                pb.current_billing_cycle_start = now
                pb.next_retention_charge_at = now + timedelta(days=30)
                pb.retention_warning_sent_at = None
                pb.save()
                summary["charges_processed"] += 1
                continue
            
            # Check if organization has sufficient credits
            if org_billing.available_credits >= retention_fee:
                # Charge the retention fee
                result = pb.charge_retention_fee(org_billing, subscription_plan)
                
                if result["success"]:
                    summary["charges_processed"] += 1
                    summary["total_charged"] += result["charged"]
                    logger.info(
                        f"[RETENTION CHARGED] Project '{pb.project.title}': "
                        f"₹{result['charged']} charged for month {pb.months_retained}"
                    )
            else:
                # Insufficient credits - send warning or schedule deletion
                if pb.insufficient_credits_warned_at is None:
                    # First warning
                    pb.insufficient_credits_warned_at = now
                    pb.save(update_fields=['insufficient_credits_warned_at'])
                    
                    # TODO: Send warning email
                    logger.warning(
                        f"[INSUFFICIENT CREDITS] Project '{pb.project.title}' cannot be retained. "
                        f"Required: ₹{retention_fee}, Available: ₹{org_billing.available_credits}. "
                        f"User has 3 weeks to add credits."
                    )
                    summary["insufficient_credits_warnings"] += 1
                    
                elif (now - pb.insufficient_credits_warned_at) >= timedelta(weeks=3):
                    # 3 weeks have passed, schedule deletion
                    pb.schedule_deletion_for_unpaid_retention()
                    
                    # TODO: Send final deletion warning email
                    logger.warning(
                        f"[DELETION SCHEDULED] Project '{pb.project.title}' scheduled for deletion "
                        f"on {pb.retention_deletion_scheduled_at} due to unpaid retention fees."
                    )
                    summary["deletions_scheduled"] += 1
                    
        except Exception as e:
            summary["errors"].append({
                "project_id": pb.project.id,
                "error": str(e),
                "type": "charge"
            })
    
    # 3. Delete projects past their deletion date
    past_deletion_date = ProjectBilling.objects.filter(
        retention_deletion_scheduled_at__lte=now,
        state__in=[
            ProjectBilling.ProjectState.ACTIVE,
            ProjectBilling.ProjectState.COMPLETED,
            ProjectBilling.ProjectState.DORMANT,
        ]
    ).select_related('project')
    
    for pb in past_deletion_date:
        try:
            project_title = pb.project.title
            project_id = pb.project.id
            
            # Soft delete the project
            pb.transition_to_state(
                ProjectBilling.ProjectState.DELETED,
                reason="Deleted due to unpaid storage retention fees"
            )
            
            # TODO: Send deletion confirmation email
            logger.warning(
                f"[PROJECT DELETED] Project '{project_title}' (ID: {project_id}) "
                f"deleted due to unpaid storage retention fees after 3-week grace period."
            )
            summary["projects_deleted"] += 1
            
        except Exception as e:
            summary["errors"].append({
                "project_id": pb.project.id,
                "error": str(e),
                "type": "deletion"
            })
    
    logger.info(f"Project retention processing complete: {summary}")
    return summary


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


@job("default", timeout=600)
def cleanup_unpublished_projects():
    """
    Hourly task to cleanup unpublished draft projects.

    Projects that are created but never had deposit paid (is_published=False)
    will be deleted after 1 hour to prevent accumulation of abandoned drafts.
    
    Note: Primary deletion happens immediately when user cancels the wizard.
    This task is a fallback for edge cases (browser crash, network issues, etc.)

    Returns:
        dict: Cleanup summary
    """
    from projects.models import Project

    logger.info("Starting unpublished project cleanup...")

    # Projects created more than 1 hour ago that are still unpublished
    cutoff = timezone.now() - timedelta(hours=1)

    summary = {"projects_deleted": 0, "errors": []}

    unpublished_projects = Project.objects.filter(
        is_published=False,
        created_at__lte=cutoff
    )

    for project in unpublished_projects:
        try:
            logger.info(f"Deleting unpublished project {project.id}: {project.title}")
            project.delete()
            summary["projects_deleted"] += 1
        except Exception as e:
            summary["errors"].append({"project_id": project.id, "error": str(e)})
            logger.error(f"Error deleting unpublished project {project.id}: {e}")

    logger.info(f"Unpublished project cleanup complete: {summary}")
    return summary


def run_weekly_cleanup_tasks():
    """
    Master task that runs all weekly cleanup tasks.
    Schedule this on Sundays.
    """
    logger.info("Running all weekly cleanup tasks...")

    results = {
        "deleted_projects": cleanup_deleted_projects(),
        "unpublished_projects": cleanup_unpublished_projects(),
    }

    logger.info(f"Weekly cleanup tasks complete: {results}")
    return results





