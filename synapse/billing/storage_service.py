"""
Storage Calculation Service for Project Data

This module handles:
1. Calculating storage used by uploaded files during project creation
2. Tracking storage usage per project
3. Updating organization-wide storage totals
4. Storage-based security deposit calculation
"""

import logging
from decimal import Decimal
from django.db import transaction
from django.utils import timezone

logger = logging.getLogger(__name__)


class StorageCalculationService:
    """Service for calculating and tracking storage usage"""
    
    # Storage rate constants
    STORAGE_RATE_PER_GB = Decimal("15.00")  # Base rate per GB per month
    PAYG_STORAGE_RATE = Decimal("20.00")  # Higher rate for PAYG users
    
    # Deposit calculation: Assume 6 months storage in deposit
    DEPOSIT_STORAGE_MONTHS = 6
    
    @classmethod
    def calculate_file_upload_storage(cls, project):
        """
        Calculate total storage from file uploads for a project.
        
        Args:
            project: Project instance
            
        Returns:
            dict: Storage breakdown with bytes, GB, and formatted string
        """
        from data_import.models import FileUpload
        
        total_bytes = 0
        file_count = 0
        
        # Get all file uploads for the project
        file_uploads = FileUpload.objects.filter(project=project)
        
        for fu in file_uploads:
            try:
                if fu.file and hasattr(fu.file, 'size'):
                    total_bytes += fu.file.size
                    file_count += 1
            except Exception as e:
                logger.warning(f"Could not read size for file upload {fu.id}: {e}")
        
        # Convert to GB
        total_gb = Decimal(str(total_bytes)) / Decimal(str(1024 ** 3))
        
        return {
            "total_bytes": total_bytes,
            "total_gb": float(total_gb),
            "total_gb_decimal": total_gb,
            "file_count": file_count,
            "formatted": cls._format_storage_size(total_bytes),
        }
    
    @classmethod
    def calculate_task_storage(cls, project):
        """
        Calculate storage from task data (for tasks already imported).
        
        Args:
            project: Project instance
            
        Returns:
            dict: Storage breakdown
        """
        from tasks.models import Task
        import json
        
        total_bytes = 0
        task_count = 0
        
        tasks = Task.objects.filter(project=project)
        
        for task in tasks.iterator(chunk_size=1000):
            try:
                # Estimate size from task data
                if task.data:
                    data_str = json.dumps(task.data) if isinstance(task.data, dict) else str(task.data)
                    total_bytes += len(data_str.encode('utf-8'))
                    task_count += 1
            except Exception as e:
                logger.warning(f"Could not calculate size for task {task.id}: {e}")
        
        total_gb = Decimal(str(total_bytes)) / Decimal(str(1024 ** 3))
        
        return {
            "total_bytes": total_bytes,
            "total_gb": float(total_gb),
            "total_gb_decimal": total_gb,
            "task_count": task_count,
            "formatted": cls._format_storage_size(total_bytes),
        }
    
    @classmethod
    def calculate_project_total_storage(cls, project):
        """
        Calculate total storage for a project (files + tasks).
        
        Args:
            project: Project instance
            
        Returns:
            dict: Complete storage breakdown
        """
        file_storage = cls.calculate_file_upload_storage(project)
        task_storage = cls.calculate_task_storage(project)
        
        total_bytes = file_storage["total_bytes"] + task_storage["total_bytes"]
        total_gb = Decimal(str(total_bytes)) / Decimal(str(1024 ** 3))
        
        return {
            "file_storage": file_storage,
            "task_storage": task_storage,
            "total_bytes": total_bytes,
            "total_gb": float(total_gb),
            "total_gb_decimal": total_gb,
            "formatted": cls._format_storage_size(total_bytes),
        }
    
    @classmethod
    @transaction.atomic
    def update_project_storage(cls, project):
        """
        Update storage tracking for a project.
        
        Args:
            project: Project instance
            
        Returns:
            ProjectBilling: Updated billing record
        """
        from billing.models import ProjectBilling
        
        storage_info = cls.calculate_project_total_storage(project)
        
        # Get or create project billing
        billing, created = ProjectBilling.objects.get_or_create(project=project)
        
        billing.storage_used_bytes = storage_info["total_bytes"]
        billing.storage_used_gb = storage_info["total_gb_decimal"]
        billing.last_storage_calculated = timezone.now()
        billing.save(update_fields=[
            "storage_used_bytes", 
            "storage_used_gb", 
            "last_storage_calculated"
        ])
        
        logger.info(
            f"Updated storage for project {project.id}: "
            f"{storage_info['formatted']} ({storage_info['total_gb']:.4f} GB)"
        )
        
        return billing
    
    @classmethod
    def calculate_organization_storage(cls, organization):
        """
        Calculate total storage used by an organization across all projects.
        
        Args:
            organization: Organization instance
            
        Returns:
            dict: Organization storage breakdown
        """
        from billing.models import ProjectBilling
        from projects.models import Project
        
        projects = Project.objects.filter(organization=organization)
        
        total_bytes = 0
        project_storage = []
        
        for project in projects:
            try:
                # Try to get cached storage from billing
                billing = getattr(project, 'billing', None)
                if billing and billing.storage_used_bytes > 0:
                    storage_bytes = billing.storage_used_bytes
                else:
                    # Calculate if not cached
                    storage_info = cls.calculate_project_total_storage(project)
                    storage_bytes = storage_info["total_bytes"]
                
                total_bytes += storage_bytes
                project_storage.append({
                    "project_id": project.id,
                    "project_title": project.title,
                    "storage_bytes": storage_bytes,
                    "storage_formatted": cls._format_storage_size(storage_bytes),
                })
            except Exception as e:
                logger.warning(f"Could not calculate storage for project {project.id}: {e}")
        
        total_gb = Decimal(str(total_bytes)) / Decimal(str(1024 ** 3))
        
        return {
            "total_bytes": total_bytes,
            "total_gb": float(total_gb),
            "total_gb_decimal": total_gb,
            "formatted": cls._format_storage_size(total_bytes),
            "project_count": len(project_storage),
            "projects": project_storage,
        }
    
    @classmethod
    @transaction.atomic
    def update_organization_storage(cls, organization):
        """
        Update storage tracking for an organization.
        
        Args:
            organization: Organization instance
            
        Returns:
            OrganizationBilling: Updated billing record
        """
        from billing.models import OrganizationBilling
        
        storage_info = cls.calculate_organization_storage(organization)
        
        billing, created = OrganizationBilling.objects.get_or_create(
            organization=organization
        )
        
        billing.storage_used_gb = storage_info["total_gb_decimal"]
        billing.last_storage_check = timezone.now()
        billing.save(update_fields=["storage_used_gb", "last_storage_check"])
        
        logger.info(
            f"Updated organization storage for {organization.title}: "
            f"{storage_info['formatted']} ({storage_info['total_gb']:.4f} GB)"
        )
        
        return billing
    
    @classmethod
    @transaction.atomic
    def charge_storage_overage(cls, organization, overage_gb, overage_cost):
        """
        Charge organization for storage overage beyond free tier.
        
        Args:
            organization: Organization instance
            overage_gb: Amount of storage exceeding free tier (in GB)
            overage_cost: Cost to charge (in credits/INR)
            
        Returns:
            dict: Charge details
        """
        from billing.models import OrganizationBilling, CreditTransaction
        from decimal import Decimal
        
        billing, created = OrganizationBilling.objects.get_or_create(
            organization=organization
        )
        
        overage_cost_decimal = Decimal(str(overage_cost))
        
        # Deduct credits
        billing.credit_balance -= overage_cost_decimal
        billing.save(update_fields=["credit_balance"])
        
        # Create transaction record
        CreditTransaction.objects.create(
            organization=organization,
            amount=-overage_cost_decimal,
            transaction_type="storage_overage",
            description=f"Storage overage charge: {overage_gb:.2f} GB",
            balance_after=billing.credit_balance,
            created_by=None,  # System charge
        )
        
        logger.info(
            f"Charged storage overage for {organization.title}: "
            f"{overage_gb:.2f} GB = ₹{overage_cost:.2f}"
        )
        
        return {
            "overage_gb": float(overage_gb),
            "cost": float(overage_cost_decimal),
            "new_balance": float(billing.credit_balance),
        }
    
    @classmethod
    def calculate_storage_deposit(cls, storage_gb, subscription_plan=None):
        """
        Calculate security deposit amount for storage.
        
        Deposit = Storage GB × Rate per GB × Months (default 6)
        
        Args:
            storage_gb: Storage amount in GB
            subscription_plan: Optional subscription for discount
            
        Returns:
            dict: Deposit calculation breakdown
        """
        storage_gb = Decimal(str(storage_gb))
        
        if subscription_plan:
            rate = subscription_plan.extra_storage_rate_per_gb
            discount_percent = subscription_plan.storage_discount_percent
            plan_name = subscription_plan.name
        else:
            rate = cls.PAYG_STORAGE_RATE
            discount_percent = Decimal("0")
            plan_name = "PAYG"
        
        # Calculate deposit (for 6 months of storage)
        gross_deposit = storage_gb * rate * cls.DEPOSIT_STORAGE_MONTHS
        discount_amount = gross_deposit * (discount_percent / Decimal("100"))
        net_deposit = gross_deposit - discount_amount
        
        return {
            "storage_gb": float(storage_gb),
            "rate_per_gb": float(rate),
            "months_covered": cls.DEPOSIT_STORAGE_MONTHS,
            "gross_deposit": float(gross_deposit),
            "discount_percent": float(discount_percent),
            "discount_amount": float(discount_amount),
            "net_deposit": float(net_deposit),
            "plan_name": plan_name,
        }
    
    @classmethod
    def get_storage_pricing_info(cls, organization):
        """
        Get storage pricing information for an organization based on their subscription.
        
        Args:
            organization: Organization instance
            
        Returns:
            dict: Pricing information
        """
        from billing.models import OrganizationBilling
        
        try:
            billing = organization.billing
            subscription = billing.active_subscription
            
            if subscription and subscription.is_active():
                plan = subscription.plan
                return {
                    "free_storage_gb": plan.storage_gb,
                    "rate_per_gb": float(plan.extra_storage_rate_per_gb),
                    "discount_percent": float(plan.storage_discount_percent),
                    "billing_type": "subscription",
                    "plan_name": plan.name,
                    "plan_type": plan.plan_type,
                }
            else:
                return {
                    "free_storage_gb": 1,  # PAYG gets 1GB free
                    "rate_per_gb": float(cls.PAYG_STORAGE_RATE),
                    "discount_percent": 0,
                    "billing_type": "payg",
                    "plan_name": "Pay As You Go",
                    "plan_type": "payg",
                }
        except Exception:
            return {
                "free_storage_gb": 1,
                "rate_per_gb": float(cls.PAYG_STORAGE_RATE),
                "discount_percent": 0,
                "billing_type": "payg",
                "plan_name": "Pay As You Go",
                "plan_type": "payg",
            }
    
    @classmethod
    def estimate_monthly_storage_cost(cls, organization):
        """
        Estimate monthly storage cost for an organization.
        
        Args:
            organization: Organization instance
            
        Returns:
            dict: Cost estimation
        """
        storage_info = cls.calculate_organization_storage(organization)
        pricing_info = cls.get_storage_pricing_info(organization)
        
        total_gb = Decimal(str(storage_info["total_gb"]))
        free_gb = Decimal(str(pricing_info["free_storage_gb"]))
        rate = Decimal(str(pricing_info["rate_per_gb"]))
        discount_percent = Decimal(str(pricing_info["discount_percent"]))
        
        billable_gb = max(Decimal("0"), total_gb - free_gb)
        gross_cost = billable_gb * rate
        discount = gross_cost * (discount_percent / Decimal("100"))
        net_cost = gross_cost - discount
        
        return {
            "total_storage_gb": float(total_gb),
            "free_storage_gb": float(free_gb),
            "billable_storage_gb": float(billable_gb),
            "rate_per_gb": float(rate),
            "gross_cost": float(gross_cost),
            "discount_percent": float(discount_percent),
            "discount_amount": float(discount),
            "estimated_monthly_cost": float(net_cost),
            "billing_type": pricing_info["billing_type"],
            "plan_name": pricing_info["plan_name"],
        }
    
    @staticmethod
    def _format_storage_size(bytes_size):
        """Format bytes to human-readable string"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_size < 1024:
                return f"{bytes_size:.2f} {unit}"
            bytes_size /= 1024
        return f"{bytes_size:.2f} PB"
