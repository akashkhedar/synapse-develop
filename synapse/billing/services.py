"""
Credit deduction service for handling billing when annotations are created
"""

import re
import logging
from decimal import Decimal
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from .models import (
    OrganizationBilling,
    AnnotationPricing,
    CreditTransaction,
    AnnotatorEarnings,
    ProjectBilling,
    SecurityDeposit,
    APIUsageTracking,
    ExportRecord,
    CreditExpiry,
)

logger = logging.getLogger(__name__)


class InsufficientCreditsError(Exception):
    """Raised when organization doesn't have enough credits"""

    pass


class SecurityDepositError(Exception):
    """Raised when security deposit requirements are not met"""

    pass


class ProjectBillingError(Exception):
    """Raised for project billing related errors"""

    pass


class CreditService:
    """Service for managing credit operations"""

    @staticmethod
    def check_and_deduct_credits(
        organization, data_type, modality, annotation_type, volume=1, annotator=None
    ):
        """
        Check if organization has sufficient credits and deduct them

        Args:
            organization: Organization object
            data_type: Type of data (2d_image, 3d_volume, etc.)
            modality: Modality type (X-ray, CT Scan, etc.)
            annotation_type: Type of annotation (classification, bounding_box, etc.)
            volume: Number of units (images, slices, minutes)
            annotator: User who performed the annotation (for revenue share)

        Returns:
            dict: Transaction details including credits deducted

        Raises:
            InsufficientCreditsError: If organization doesn't have enough credits
            AnnotationPricing.DoesNotExist: If pricing not found
        """

        with transaction.atomic():
            # Get or create billing
            billing, _ = OrganizationBilling.objects.select_for_update().get_or_create(
                organization=organization
            )

            # Get pricing
            pricing = AnnotationPricing.objects.get(
                data_type=data_type, modality=modality, is_active=True
            )

            # Calculate credit cost
            credit_cost = pricing.calculate_credit(annotation_type, volume)

            # Check if sufficient credits
            if not billing.has_sufficient_credits(credit_cost):
                raise InsufficientCreditsError(
                    f"Insufficient credits. Required: {credit_cost}, Available: {billing.available_credits}"
                )

            # Deduct credits
            description = (
                f"{annotation_type} annotation on {pricing.get_data_type_display()} "
                f"({modality}) - {volume} {pricing.unit_description}"
            )

            billing.deduct_credits(credit_cost, description)

            # Handle annotator earnings if annotator provided
            annotator_earnings = None
            if annotator and annotator != organization.created_by:
                annotator_earnings = CreditService.credit_annotator(
                    annotator=annotator,
                    organization=organization,
                    total_credits=credit_cost,
                    description=description,
                )

            return {
                "success": True,
                "credits_deducted": float(credit_cost),
                "remaining_credits": float(billing.available_credits),
                "pricing_details": {
                    "data_type": data_type,
                    "modality": modality,
                    "annotation_type": annotation_type,
                    "volume": volume,
                    "base_credit": float(pricing.base_credit),
                },
                "annotator_earnings": annotator_earnings,
            }

    @staticmethod
    def credit_annotator(annotator, organization, total_credits, description=""):
        """
        Credit annotator with their share of the annotation credits

        Args:
            annotator: User who performed the annotation
            organization: Organization that owns the project
            total_credits: Total credits for the annotation
            description: Description of the work

        Returns:
            dict: Earnings details
        """
        # Get or create annotator earnings record
        earnings, _ = AnnotatorEarnings.objects.get_or_create(
            annotator=annotator, organization=organization
        )

        # Calculate annotator share (40-50%, using the configured percentage)
        revenue_share_pct = earnings.revenue_share_percentage / 100
        annotator_credits = Decimal(str(total_credits)) * Decimal(
            str(revenue_share_pct)
        )

        # Assuming 1 credit = ₹1 (adjust based on pricing)
        inr_amount = annotator_credits

        # Update earnings
        earnings.credits_earned += annotator_credits
        earnings.inr_equivalent += inr_amount
        earnings.total_annotations += 1
        earnings.save()

        logger.info(
            f"Annotator {annotator.email} earned {annotator_credits} credits "
            f"(₹{inr_amount}) for {description}"
        )

        return {
            "annotator_email": annotator.email,
            "credits_earned": float(annotator_credits),
            "inr_earned": float(inr_amount),
            "revenue_share_percentage": float(earnings.revenue_share_percentage),
            "total_earnings": float(earnings.inr_equivalent),
        }

    @staticmethod
    def get_credit_estimate(data_type, modality, annotation_type, volume=1):
        """
        Get estimated credit cost without deducting

        Args:
            data_type: Type of data
            modality: Modality type
            annotation_type: Type of annotation
            volume: Number of units

        Returns:
            Decimal: Estimated credit cost
        """
        try:
            pricing = AnnotationPricing.objects.get(
                data_type=data_type, modality=modality, is_active=True
            )
            return pricing.calculate_credit(annotation_type, volume)
        except AnnotationPricing.DoesNotExist:
            return Decimal("0")

    @staticmethod
    def add_bonus_credits(organization, amount, description, admin_user=None):
        """
        Add bonus credits to organization (promotional, compensation, etc.)

        Args:
            organization: Organization to credit
            amount: Number of credits to add
            description: Reason for bonus credits
            admin_user: Admin who authorized the bonus
        """
        billing, _ = OrganizationBilling.objects.get_or_create(
            organization=organization
        )

        billing.add_credits(amount, description)

        # Update transaction to mark as bonus
        transaction = (
            CreditTransaction.objects.filter(
                organization=organization, transaction_type="credit"
            )
            .order_by("-created_at")
            .first()
        )

        if transaction:
            transaction.category = "bonus"
            transaction.created_by = admin_user
            transaction.save()

        logger.info(
            f"Added {amount} bonus credits to {organization.title}: {description}"
        )

    @staticmethod
    def check_and_deduct_export_credits(organization, task_count, export_format="JSON"):
        """
        Check if organization has sufficient credits for export and deduct them

        Args:
            organization: Organization object
            task_count: Number of tasks/annotations being exported
            export_format: Format of export (JSON, CSV, etc.)

        Returns:
            dict: Transaction details including credits deducted

        Raises:
            InsufficientCreditsError: If organization doesn't have enough credits
        """

        with transaction.atomic():
            # Get or create billing
            billing, _ = OrganizationBilling.objects.select_for_update().get_or_create(
                organization=organization
            )

            # Calculate credit cost for export
            # Base cost: 0.1 credits per task/annotation
            base_rate = Decimal("0.1")
            credit_cost = base_rate * Decimal(str(task_count))

            # Check if sufficient credits
            if not billing.has_sufficient_credits(credit_cost):
                raise InsufficientCreditsError(
                    f"Insufficient credits for export. Required: {credit_cost}, Available: {billing.available_credits}"
                )

            # Deduct credits
            description = (
                f"Export of {task_count} annotations in {export_format} format"
            )

            billing.deduct_credits(credit_cost, description)

            logger.info(
                f"Deducted {credit_cost} credits from {organization.title} for export of {task_count} tasks"
            )

            return {
                "success": True,
                "credits_deducted": float(credit_cost),
                "remaining_credits": float(billing.available_credits),
                "task_count": task_count,
                "export_format": export_format,
                "rate_per_task": float(base_rate),
            }


class StorageService:
    """Service for tracking and billing storage usage"""

    @staticmethod
    def calculate_storage_usage(organization):
        """
        Calculate total storage used by organization using StorageCalculationService

        Args:
            organization: Organization object

        Returns:
            Decimal: Storage used in GB
        """
        from billing.storage_service import StorageCalculationService
        
        # Use the new StorageCalculationService for accurate calculation
        storage_info = StorageCalculationService.calculate_organization_storage(organization)
        
        return storage_info["total_gb_decimal"]

    @staticmethod
    def charge_storage(organization, billing_month):
        """
        Charge organization for storage usage with subscription discounts

        Args:
            organization: Organization object
            billing_month: First day of billing month (date object)

        Returns:
            Decimal: Credits charged
        """
        from .models import StorageBilling
        from billing.storage_service import StorageCalculationService

        # Calculate storage usage using the new service
        storage_info = StorageCalculationService.calculate_organization_storage(organization)
        storage_gb = storage_info["total_gb_decimal"]

        # Get or create storage billing record
        storage_billing, created = StorageBilling.objects.get_or_create(
            organization=organization,
            billing_month=billing_month,
            defaults={"storage_used_gb": storage_gb},
        )

        if not created and storage_billing.is_charged:
            logger.warning(
                f"Storage already charged for {organization.title} - {billing_month}"
            )
            return Decimal("0")

        # Update storage usage
        storage_billing.storage_used_gb = storage_gb
        storage_billing.storage_used_bytes = storage_info["total_bytes"]

        # Get subscription plan for discounts
        billing = organization.billing
        subscription_plan = None
        
        if billing.active_subscription and billing.active_subscription.is_active():
            subscription = billing.active_subscription
            subscription_plan = subscription.plan
            
            # Set free storage from subscription
            storage_billing.free_storage_gb = Decimal(str(subscription_plan.storage_gb))
            
            # Set rate and discount from subscription
            storage_billing.rate_per_gb = subscription_plan.extra_storage_rate_per_gb
            storage_billing.discount_percent = subscription_plan.storage_discount_percent
            storage_billing.subscription_plan_name = subscription_plan.name
            storage_billing.billing_type = "subscription"
        else:
            # PAYG defaults - no discount
            storage_billing.free_storage_gb = Decimal("1")  # PAYG gets 1GB free
            storage_billing.rate_per_gb = Decimal("20")  # Higher rate for PAYG
            storage_billing.discount_percent = Decimal("0")
            storage_billing.subscription_plan_name = "Pay As You Go"
            storage_billing.billing_type = "payg"

        # Calculate charges with subscription discounts
        credits_charged = storage_billing.calculate_charges(subscription_plan)

        if credits_charged > 0:
            try:
                billing.deduct_credits(
                    credits_charged,
                    f"Storage billing for {billing_month} - {storage_billing.billable_storage_gb} GB "
                    f"({storage_billing.subscription_plan_name}, {storage_billing.discount_percent}% discount)",
                )

                storage_billing.is_charged = True
                storage_billing.charged_at = timezone.now()
                storage_billing.save()

                logger.info(
                    f"Charged {credits_charged} credits for storage to {organization.title} "
                    f"({storage_gb} GB total, {storage_billing.billable_storage_gb} GB billable, "
                    f"{storage_billing.discount_percent}% discount applied)"
                )

            except Exception as e:
                logger.error(
                    f"Error charging storage for {organization.title}: {str(e)}"
                )

        return credits_charged


class ProjectBillingService:
    """
    Service for managing project-level billing including:
    - Security deposits
    - Project lifecycle states
    - Export billing
    - Storage tracking per project
    """

    # Configuration constants
    BASE_DEPOSIT_FEE = Decimal("500")  # Minimum ₹500 base fee
    STORAGE_RATE_PER_GB = Decimal("10")  # ₹10 per GB for deposit calculation
    ANNOTATION_BUFFER_MULTIPLIER = Decimal(
        "1.5"
    )  # 1.5x buffer for estimated annotations
    FREE_STORAGE_GB = Decimal("5")  # 5 GB free storage
    STORAGE_TIER_RATES = {
        "standard": {"min_gb": 5, "max_gb": 50, "rate": Decimal("5")},  # ₹5/GB/month
        "large": {"min_gb": 50, "max_gb": 500, "rate": Decimal("3")},  # ₹3/GB/month
        "enterprise": {
            "min_gb": 500,
            "max_gb": float("inf"),
            "rate": Decimal("2"),
        },  # Custom
    }
    DORMANT_THRESHOLD_DAYS = 30
    GRACE_PERIOD_DAYS = 30
    MIN_BALANCE_FOR_NEW_PROJECT = Decimal("100")

    # Annotation rate estimates by type (credits per task)
    ANNOTATION_RATE_ESTIMATES = {
        "classification": Decimal("2"),  # Simple choice/checkbox
        "bounding_box": Decimal("5"),  # Rectangle/bounding box
        "polygon": Decimal("8"),  # Polygon drawing
        "segmentation": Decimal("15"),  # Brush/semantic segmentation
        "keypoint": Decimal("10"),  # Keypoint detection
        "ner": Decimal("3"),  # Named entity recognition
        "text_area": Decimal("4"),  # Text input/transcription
        "rating": Decimal("1"),  # Simple rating
        "taxonomy": Decimal("3"),  # Hierarchical classification
        "pairwise": Decimal("4"),  # Comparison/ranking
        "time_series": Decimal("6"),  # Time series labeling
        "video": Decimal("12"),  # Video annotation (per minute)
        "audio": Decimal("8"),  # Audio annotation (per minute)
        "default": Decimal("5"),
    }

    # Duration-based data type multipliers (rate per minute)
    DURATION_BASED_TYPES = {
        "audio": {
            "base_rate": Decimal("8"),  # Credits per minute
            "min_charge": Decimal("5"),  # Minimum credits per task
            "default_duration_mins": Decimal("3"),  # Default assumed duration
        },
        "video": {
            "base_rate": Decimal("12"),  # Credits per minute
            "min_charge": Decimal("10"),  # Minimum credits per task
            "default_duration_mins": Decimal("5"),  # Default assumed duration
        },
    }

    # Data type detection patterns
    DATA_TYPE_PATTERNS = {
        "audio": [
            r"<audio\s",
            r"<audiolabels\s",
            r"\.mp3[\"\'>\s]",
            r"\.wav[\"\'>\s]",
            r"\.ogg[\"\'>\s]",
            r"\.flac[\"\'>\s]",
            r"\.m4a[\"\'>\s]",
        ],
        "video": [
            r"<video\s",
            r"<videorectangle\s",
            r"\.mp4[\"\'>\s]",
            r"\.webm[\"\'>\s]",
            r"\.mov[\"\'>\s]",
            r"\.avi[\"\'>\s]",
        ],
        "time_series": [
            r"<timeseries\s",
            r"<timeserieslabels\s",
            r"<channel\s",
        ],
        "text": [
            r"<text\s",
            r"<hypertextlabels\s",
            r"<paragraphlabels\s",
        ],
        "image": [
            r"<image\s",
            r"<rectanglelabels\s",
            r"<polygonlabels\s",
            r"<brushlabels\s",
            r"<keypointlabels\s",
        ],
    }

    # Tag name to annotation type mapping
    TAG_TYPE_MAPPING = {
        # Classification tags
        "choices": "classification",
        "choice": "classification",
        "checkbox": "classification",
        # Object detection / bounding box
        "rectanglelabels": "bounding_box",
        "rectangle": "bounding_box",
        "rect": "bounding_box",
        # Polygon
        "polygonlabels": "polygon",
        "polygon": "polygon",
        # Segmentation
        "brushlabels": "segmentation",
        "brush": "segmentation",
        # Keypoint
        "keypointlabels": "keypoint",
        "keypoint": "keypoint",
        # NER / Text
        "labels": "ner",
        "label": "ner",
        "hypertextlabels": "ner",
        # Text input
        "textarea": "text_area",
        "text": "text_area",
        # Rating
        "rating": "rating",
        # Taxonomy
        "taxonomy": "taxonomy",
        # Pairwise/Ranking
        "pairwise": "pairwise",
        "ranker": "pairwise",
        # Time series
        "timeserieslabels": "time_series",
        # Video
        "videorectangle": "video",
        # Audio
        "audiolabels": "audio",
    }

    # Complexity multipliers based on number of labels
    LABEL_COUNT_MULTIPLIERS = {
        (1, 5): Decimal("1.0"),  # 1-5 labels: no extra complexity
        (6, 15): Decimal("1.2"),  # 6-15 labels: 20% more complex
        (16, 30): Decimal("1.5"),  # 16-30 labels: 50% more complex
        (31, 100): Decimal("2.0"),  # 31-100 labels: 100% more complex
        (101, float("inf")): Decimal("2.5"),  # 100+ labels: 150% more complex
    }

    @classmethod
    def _detect_data_types(cls, label_config):
        """
        Detect primary data types from label config.

        Args:
            label_config: XML string of the label config

        Returns:
            list: Detected data types (audio, video, time_series, text, image)
        """
        if not label_config:
            return ["image"]  # Default to image

        label_config_lower = label_config.lower()
        detected_types = set()

        for data_type, patterns in cls.DATA_TYPE_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, label_config_lower):
                    detected_types.add(data_type)
                    break

        return list(detected_types) if detected_types else ["image"]

    @classmethod
    def _calculate_duration_based_cost(
        cls, data_type, task_count, avg_duration_mins=None, total_storage_gb=None
    ):
        """
        Calculate cost for duration-based data types (audio/video).

        Args:
            data_type: Type of data (audio, video)
            task_count: Number of tasks
            avg_duration_mins: Average duration per task in minutes (optional)
            total_storage_gb: Total storage in GB (optional, used to estimate duration)

        Returns:
            dict: Cost breakdown for duration-based pricing
        """
        if data_type not in cls.DURATION_BASED_TYPES:
            return None

        config = cls.DURATION_BASED_TYPES[data_type]
        base_rate = config["base_rate"]
        min_charge = config["min_charge"]
        default_duration = config["default_duration_mins"]

        # Estimate duration from storage if not provided
        if avg_duration_mins is None:
            if total_storage_gb and task_count > 0:
                # Estimate based on typical file sizes
                # Audio: ~1MB per minute (compressed), Video: ~10MB per minute
                mb_per_task = (float(total_storage_gb) * 1024) / task_count
                if data_type == "audio":
                    avg_duration_mins = Decimal(str(max(1, mb_per_task / 1.5)))
                else:  # video
                    avg_duration_mins = Decimal(str(max(1, mb_per_task / 15)))
            else:
                avg_duration_mins = default_duration

        # Calculate cost per task
        duration_cost = Decimal(str(avg_duration_mins)) * base_rate
        cost_per_task = max(duration_cost, min_charge)

        return {
            "data_type": data_type,
            "avg_duration_mins": float(avg_duration_mins),
            "base_rate_per_min": float(base_rate),
            "min_charge": float(min_charge),
            "cost_per_task": float(cost_per_task),
            "total_cost": float(cost_per_task * Decimal(str(task_count))),
        }

    @classmethod
    def _analyze_label_config(cls, label_config):
        """
        Analyze the label config XML to extract annotation types and label counts.

        Args:
            label_config: XML string of the label config

        Returns:
            dict: Analysis results with detected types, label counts, complexity
        """
        if not label_config:
            return {
                "annotation_types": ["default"],
                "total_labels": 0,
                "complexity_multiplier": Decimal("1.0"),
                "detected_tags": [],
                "data_types": ["image"],
            }

        label_config_lower = label_config.lower()
        detected_tags = []
        annotation_types = set()
        total_labels = 0

        # Detect control tags and their types
        for tag, ann_type in cls.TAG_TYPE_MAPPING.items():
            # Look for opening tags
            pattern = rf"<{tag}[\s>]"
            if re.search(pattern, label_config_lower):
                detected_tags.append(tag)
                annotation_types.add(ann_type)

        # Detect data types
        data_types = cls._detect_data_types(label_config)

        # Count labels using regex - look for <Label value="..." patterns
        label_pattern = r'<label\s+[^>]*value\s*=\s*["\']([^"\']+)["\']'
        labels = re.findall(label_pattern, label_config_lower)
        total_labels = len(labels)

        # Also count <Choice> tags for classification
        choice_pattern = r'<choice\s+[^>]*value\s*=\s*["\']([^"\']+)["\']'
        choices = re.findall(choice_pattern, label_config_lower)
        total_labels += len(choices)

        # Calculate complexity multiplier based on label count
        complexity_multiplier = Decimal("1.0")
        for (min_count, max_count), multiplier in cls.LABEL_COUNT_MULTIPLIERS.items():
            if min_count <= total_labels <= max_count:
                complexity_multiplier = multiplier
                break

        # Note: Complexity is based ONLY on label count as per pricing rules:
        # 1-5 labels: 1.0x, 6-15: 1.2x, 16-30: 1.5x, 31-100: 2.0x, 101+: 2.5x
        # Multiple annotation types (e.g., segmentation + NER) are handled via
        # separate rate charges, not additional complexity multiplier.

        return {
            "annotation_types": (
                list(annotation_types) if annotation_types else ["default"]
            ),
            "total_labels": total_labels,
            "complexity_multiplier": complexity_multiplier,
            "detected_tags": detected_tags,
            "data_types": data_types,
        }

    @classmethod
    def _calculate_annotation_rate(cls, annotation_types, data_types=None):
        """
        Calculate the combined annotation rate for multiple annotation types.
        
        First tries to get rates from AnnotationPricing table based on data type,
        then falls back to hardcoded ANNOTATION_RATE_ESTIMATES.

        Args:
            annotation_types: List of annotation types detected
            data_types: List of data types detected (e.g., ['image', 'audio'])

        Returns:
            Decimal: Combined annotation rate
        """
        if not annotation_types:
            return cls.ANNOTATION_RATE_ESTIMATES["default"]

        # Map Label Studio data types to AnnotationPricing data_type values
        data_type_mapping = {
            'image': '2d_image',
            'audio': 'time_series',  # Audio is a type of time series
            'video': 'video',
            'text': 'document',
            'time_series': 'time_series',
        }
        
        # Map annotation types to AnnotationPricing field names
        annotation_type_mapping = {
            'classification': 'classification',
            'bounding_box': 'bounding_box',
            'polygon': 'polygon',
            'segmentation': 'segmentation',
            'keypoint': 'keypoint',
            'ner': 'classification',  # NER is a type of classification
            'text_area': 'classification',
            'rating': 'classification',
            'taxonomy': 'classification',
            'pairwise': 'classification',
        }
        
        total_rate = Decimal("0")
        
        # Try to get rates from AnnotationPricing table
        if data_types:
            primary_data_type = data_types[0] if data_types else 'image'
            pricing_data_type = data_type_mapping.get(primary_data_type, '2d_image')
            
            try:
                # Get any active pricing for this data type
                pricing = AnnotationPricing.objects.filter(
                    data_type=pricing_data_type,
                    is_active=True
                ).first()
                
                if pricing:
                    # Calculate rate from pricing table
                    for ann_type in annotation_types:
                        pricing_ann_type = annotation_type_mapping.get(ann_type, 'classification')
                        rate = pricing.calculate_credit(pricing_ann_type, 1)
                        total_rate += rate
                    
                    if total_rate > 0:
                        return total_rate
            except Exception:
                pass  # Fall back to hardcoded rates
        
        # Fall back to hardcoded rates
        for ann_type in annotation_types:
            rate = cls.ANNOTATION_RATE_ESTIMATES.get(
                ann_type, cls.ANNOTATION_RATE_ESTIMATES["default"]
            )
            total_rate += rate

        return total_rate

    @classmethod
    def calculate_security_fee(cls, storage_fee, annotation_fee):
        """
        Calculate base fee (security fee) as 10% of annotation cost.
        Minimum base fee is ₹500 (fixed).
        If 10% > ₹500, round to nearest 50 or 100.
        
        Formula: 
        - 10% of annotation cost <= 500 → Base Fee = 500 (fixed)
        - 10% of annotation cost > 500 → Base Fee = rounded to nearest 50/100
        
        Args:
            storage_fee: Calculated storage fee (Decimal) - not used in new logic
            annotation_fee: Calculated annotation fee (Decimal)
            
        Returns:
            Decimal: Base fee amount (minimum ₹500)
        """
        from decimal import Decimal, ROUND_HALF_UP
        
        # Calculate 10% of annotation cost only
        ten_percent = annotation_fee * Decimal('0.10')
        
        # If less than or equal to 500, return fixed 500
        if ten_percent <= Decimal('500'):
            return Decimal('500')
        
        # Otherwise, round to nearest 50 or 100
        # For amounts < 1000, round to nearest 50
        # For amounts >= 1000, round to nearest 100
        if ten_percent < Decimal('1000'):
            # Round to nearest 50
            base_fee = (ten_percent / Decimal('50')).quantize(Decimal('1'), rounding=ROUND_HALF_UP) * Decimal('50')
        else:
            # Round to nearest 100
            base_fee = (ten_percent / Decimal('100')).quantize(Decimal('1'), rounding=ROUND_HALF_UP) * Decimal('100')
        
        return base_fee
    
    @classmethod
    @transaction.atomic
    def calculate_security_deposit(
        cls,
        project,
        estimated_tasks=None,
        estimated_storage_gb=None,
        annotation_type=None,  # Deprecated, kept for backward compatibility
    ):
        """
        Calculate required security deposit for a project based on label config complexity.

        Security Deposit = Base Fee + Storage Fee + (Annotation Cost × Complexity)

        The calculation considers:
        - Base fee: Minimum deposit required
        - Storage fee: Based on estimated storage requirements with subscription plan limits
        - Annotation cost: Based on task count, annotation types, and label complexity
        - Complexity multiplier: Based on number of labels and annotation types

        Args:
            project: Project instance with label_config
            estimated_tasks: Estimated number of tasks (if known)
            estimated_storage_gb: Estimated storage in GB (if known)
            annotation_type: Deprecated, type is now auto-detected from label_config

        Returns:
            dict: Breakdown of deposit calculation
        """
        from billing.models import SubscriptionPlan, OrganizationBilling
        from billing.storage_service import StorageCalculationService
        
        # Get organization and subscription plan
        organization = getattr(project, 'organization', None)
        
        subscription_plan = None
        free_storage_gb = Decimal("5")  # Default free storage
        storage_rate_per_gb = cls.STORAGE_RATE_PER_GB
        storage_discount = Decimal("0")
        
        if organization:
            # Get active subscription
            org_billing = OrganizationBilling.objects.filter(organization=organization).first()
            
            if org_billing and org_billing.active_subscription and org_billing.active_subscription.status == 'active':
                # Get the subscription plan from the active subscription
                subscription_plan = org_billing.active_subscription.plan
                free_storage_gb = Decimal(str(subscription_plan.storage_gb))
                storage_rate_per_gb = subscription_plan.extra_storage_rate_per_gb
                storage_discount = subscription_plan.storage_discount_percent
            
            # Calculate existing storage usage
            existing_storage_info = StorageCalculationService.calculate_organization_storage(organization)
            existing_storage_gb = existing_storage_info["total_gb_decimal"]
        else:
            existing_storage_gb = Decimal("0")
        
        # Calculate new project storage
        new_project_storage_gb = (
            Decimal(str(estimated_storage_gb)) if estimated_storage_gb else Decimal("0")
        )
        
        # Total storage after this project
        total_storage_gb = existing_storage_gb + new_project_storage_gb
        
        # Calculate billable storage (overage beyond free limit)
        billable_storage_gb = max(Decimal("0"), total_storage_gb - free_storage_gb)
        
        # Calculate storage fee for this project's contribution to overage
        if total_storage_gb <= free_storage_gb:
            # All storage is within free limit
            storage_fee = Decimal("0")
            storage_overage_gb = Decimal("0")
        else:
            # Calculate how much of this project contributes to overage
            if existing_storage_gb >= free_storage_gb:
                # Already over limit, charge for entire project storage
                storage_overage_gb = new_project_storage_gb
            else:
                # This project pushes over the limit
                storage_overage_gb = total_storage_gb - free_storage_gb
            
            # Calculate fee with subscription rate
            storage_fee = storage_overage_gb * storage_rate_per_gb
            
            # Apply discount if available
            if storage_discount > 0:
                discount_amount = storage_fee * (storage_discount / Decimal("100"))
                storage_fee = storage_fee - discount_amount

        # Get label config from project
        label_config = getattr(project, "label_config", None)

        # Analyze label config for complexity
        config_analysis = cls._analyze_label_config(label_config)

        # Get task count
        try:
            task_count = estimated_tasks or project.tasks.count() or 10
        except (AttributeError, TypeError):
            task_count = estimated_tasks or 10

        # Get detected data types
        data_types = config_analysis.get("data_types", ["image"])

        # Calculate annotation rate based on detected types and data types
        annotation_rate = cls._calculate_annotation_rate(
            config_analysis["annotation_types"],
            data_types=data_types
        )

        # Check for duration-based data types (audio/video)
        duration_pricing = None
        for data_type in data_types:
            if data_type in cls.DURATION_BASED_TYPES:
                duration_pricing = cls._calculate_duration_based_cost(
                    data_type=data_type,
                    task_count=task_count,
                    avg_duration_mins=None,  # Will use default
                    total_storage_gb=new_project_storage_gb if new_project_storage_gb > 0 else None,
                )
                # Use duration-based pricing for the annotation rate
                if duration_pricing:
                    annotation_rate = Decimal(str(duration_pricing["cost_per_task"]))
                break

        # Apply complexity multiplier
        complexity_multiplier = config_analysis["complexity_multiplier"]

        # Calculate estimated annotation cost
        estimated_annotation_cost = (
            Decimal(str(task_count))
            * annotation_rate
            * complexity_multiplier
            * cls.ANNOTATION_BUFFER_MULTIPLIER
        )

        # Calculate security fee as 10% of annotation cost only
        security_fee = cls.calculate_security_fee(storage_fee, estimated_annotation_cost)
        base_fee = security_fee  # For backward compatibility

        # Total deposit = Base Fee + Storage Fee (non-refundable) + Annotation Cost
        total_deposit = security_fee + storage_fee + estimated_annotation_cost
        
        # Refundable portion = Base Fee + Annotation Cost
        # Non-refundable portion = Storage Fee
        refundable_amount = security_fee + estimated_annotation_cost
        non_refundable_amount = storage_fee

        breakdown = {
            "base_fee": float(base_fee),
            "estimated_tasks": task_count,
            "annotation_types": config_analysis["annotation_types"],
            "annotation_rate": float(annotation_rate),
            "total_labels": config_analysis["total_labels"],
            "complexity_multiplier": float(complexity_multiplier),
            "estimated_storage_gb": float(new_project_storage_gb),
            "existing_storage_gb": float(existing_storage_gb),
            "total_storage_gb": float(total_storage_gb),
            "free_storage_gb": float(free_storage_gb),
            "storage_overage_gb": float(storage_overage_gb),
            "storage_rate": float(storage_rate_per_gb),
            "storage_discount_percent": float(storage_discount),
            "storage_fee": float(storage_fee),
            "storage_fee_refundable": False,  # Storage is non-refundable
            "buffer_multiplier": float(cls.ANNOTATION_BUFFER_MULTIPLIER),
            "annotation_fee": float(estimated_annotation_cost),
            "detected_tags": config_analysis["detected_tags"],
            "data_types": data_types,
            "subscription_plan": subscription_plan.name if subscription_plan else "Pay As You Go",
            "refundable_amount": float(refundable_amount),
            "non_refundable_amount": float(non_refundable_amount),
        }

        # Add duration pricing details if applicable
        if duration_pricing:
            breakdown["duration_pricing"] = duration_pricing

        return {
            "success": True,
            "base_fee": float(base_fee),
            "storage_fee": float(storage_fee),
            "storage_fee_refundable": False,
            "annotation_fee": float(estimated_annotation_cost),
            "total_deposit": float(total_deposit),
            "refundable_amount": float(refundable_amount),
            "non_refundable_amount": float(non_refundable_amount),
            "breakdown": breakdown,
        }

    @classmethod
    @transaction.atomic
    def create_project_billing(
        cls,
        project,
        user=None,
        deposit_amount=None,
        estimated_tasks=None,
        estimated_storage_gb=None,
    ):
        """
        Create billing record for a new project and collect security deposit.

        Args:
            project: Project instance
            user: User creating the project
            deposit_amount: Pre-calculated deposit amount from frontend (takes priority)
            estimated_tasks: Estimated number of tasks for deposit calculation
            estimated_storage_gb: Estimated storage in GB for deposit calculation

        Returns:
            ProjectBilling instance

        Raises:
            InsufficientCreditsError: If organization doesn't have enough credits
            SecurityDepositError: If deposit calculation fails
        """
        organization = project.organization

        # Check minimum balance requirement
        try:
            billing = organization.billing
        except OrganizationBilling.DoesNotExist:
            billing = OrganizationBilling.objects.create(organization=organization)

        if billing.available_credits < cls.MIN_BALANCE_FOR_NEW_PROJECT:
            raise InsufficientCreditsError(
                f"Minimum balance of ₹{cls.MIN_BALANCE_FOR_NEW_PROJECT} required to create projects. "
                f"Current balance: ₹{billing.available_credits}"
            )

        # Use pre-calculated deposit amount from frontend if provided
        # Otherwise calculate based on project state with estimates
        if deposit_amount and deposit_amount > 0:
            # Trust the frontend calculation (it was shown to user and confirmed)
            total_deposit = deposit_amount
            # Still calculate for breakdown info
            deposit_calc = cls.calculate_security_deposit(
                project,
                estimated_tasks=estimated_tasks,
                estimated_storage_gb=estimated_storage_gb,
            )
        else:
            # Calculate security deposit with estimates
            deposit_calc = cls.calculate_security_deposit(
                project,
                estimated_tasks=estimated_tasks,
                estimated_storage_gb=estimated_storage_gb,
            )
            total_deposit = Decimal(str(deposit_calc["total_deposit"]))

        # Check if organization has enough credits for deposit
        if not billing.has_sufficient_credits(total_deposit):
            raise InsufficientCreditsError(
                f"Insufficient credits for security deposit. "
                f"Required: ₹{total_deposit}, Available: ₹{billing.available_credits}"
            )

        # Create ProjectBilling record
        storage_fee = Decimal(str(deposit_calc.get("storage_fee", 0)))
        storage_overage_gb = Decimal(str(deposit_calc.get("breakdown", {}).get("storage_overage_gb", 0)))
        
        project_billing, created = ProjectBilling.objects.get_or_create(
            project=project,
            defaults={
                "security_deposit_required": total_deposit,
                "estimated_annotation_cost": Decimal(
                    str(deposit_calc["annotation_fee"])
                ),
                "storage_fee_paid": storage_fee,
                "storage_overage_gb": storage_overage_gb,
            },
        )

        if not created:
            # Update existing record
            project_billing.security_deposit_required = total_deposit
            project_billing.estimated_annotation_cost = Decimal(
                str(deposit_calc["annotation_fee"])
            )
            project_billing.storage_fee_paid = storage_fee
            project_billing.storage_overage_gb = storage_overage_gb
            project_billing.save()

        # Create SecurityDeposit record
        security_deposit = SecurityDeposit.objects.create(
            project=project,
            organization=organization,
            base_fee=Decimal(str(deposit_calc["base_fee"])),
            storage_fee=Decimal(str(deposit_calc["storage_fee"])),
            annotation_fee=Decimal(str(deposit_calc["annotation_fee"])),
            total_deposit=total_deposit,
            status=SecurityDeposit.DepositStatus.PENDING,
        )

        # Deduct deposit from organization credits
        billing.deduct_credits(
            total_deposit, f"Security deposit for project: {project.title}"
        )

        # Get the transaction record
        payment_transaction = (
            CreditTransaction.objects.filter(
                organization=organization, transaction_type="debit"
            )
            .order_by("-created_at")
            .first()
        )

        # Update records
        security_deposit.status = SecurityDeposit.DepositStatus.HELD
        security_deposit.paid_at = timezone.now()
        security_deposit.payment_transaction = payment_transaction
        security_deposit.save()

        project_billing.security_deposit_paid = total_deposit
        project_billing.deposit_paid_at = timezone.now()
        project_billing.is_deposit_held = True
        project_billing.save()

        # Publish the project after deposit is collected
        project.is_published = True
        project.save(update_fields=['is_published'])

        logger.info(
            f"Security deposit of ₹{total_deposit} collected for project {project.title} "
            f"(ID: {project.id}) from {organization.title}"
        )

        return project_billing

    @classmethod
    def calculate_import_cost(cls, project, new_task_count, file_upload_ids=None):
        """
        Calculate the cost for importing additional data into an existing project.
        
        This calculates:
        1. Annotation cost for new tasks (based on existing label config)
        2. Additional base fee if the new total tasks increase the tier
        
        Args:
            project: Project instance
            new_task_count: Number of new tasks being imported
            file_upload_ids: Optional list of file upload IDs (for storage calculation)
            
        Returns:
            dict: Import cost breakdown
        """
        from billing.models import ProjectBilling, OrganizationBilling
        
        if new_task_count <= 0:
            return {
                "success": True,
                "annotation_cost": 0,
                "additional_base_fee": 0,
                "storage_cost": 0,
                "total_cost": 0,
                "breakdown": {},
            }
        
        organization = project.organization
        
        # Get existing billing info
        try:
            project_billing = project.billing
            existing_task_count = project.num_tasks or 0
            original_base_fee = float(project_billing.security_deposit_required) - float(project_billing.estimated_annotation_cost) - float(project_billing.storage_fee_paid)
        except ProjectBilling.DoesNotExist:
            existing_task_count = project.num_tasks or 0
            original_base_fee = Decimal('500')  # Minimum base fee
        
        # Analyze label config for complexity
        config_analysis = cls._analyze_label_config(project.label_config or "")
        complexity_multiplier = config_analysis["complexity_multiplier"]
        
        # Get detected data types from project
        data_types = list(project.data_types.keys()) if project.data_types else ["image"]
        
        # Calculate annotation rate based on detected types and data types
        annotation_rate = cls._calculate_annotation_rate(
            config_analysis["annotation_types"],
            data_types=data_types
        )
        
        # Calculate annotation cost for new tasks
        new_annotation_cost = (
            Decimal(str(new_task_count))
            * annotation_rate
            * complexity_multiplier
            * cls.ANNOTATION_BUFFER_MULTIPLIER
        )
        
        # Calculate what the base fee SHOULD be with the new total
        new_total_tasks = existing_task_count + new_task_count
        
        # Calculate annotation cost for the new total to determine base fee
        total_annotation_cost = (
            Decimal(str(new_total_tasks))
            * annotation_rate
            * complexity_multiplier
            * cls.ANNOTATION_BUFFER_MULTIPLIER
        )
        
        # Calculate new base fee based on total annotation cost
        new_base_fee = cls.calculate_security_fee(Decimal('0'), total_annotation_cost)
        
        # Additional base fee = new base fee - original base fee (if positive)
        original_base_fee_decimal = Decimal(str(original_base_fee)) if original_base_fee > 0 else Decimal('500')
        additional_base_fee = max(Decimal('0'), new_base_fee - original_base_fee_decimal)
        
        # Calculate storage cost for new data (if any)
        storage_cost = Decimal('0')
        if file_upload_ids:
            # This would calculate additional storage needed
            # For now, storage is calculated at upload time
            pass
        
        # Total import cost
        total_cost = new_annotation_cost + additional_base_fee + storage_cost
        
        # Check if organization has enough credits
        try:
            org_billing = organization.billing
            has_sufficient_credits = org_billing.has_sufficient_credits(total_cost)
            available_credits = float(org_billing.available_credits)
        except OrganizationBilling.DoesNotExist:
            has_sufficient_credits = False
            available_credits = 0
        
        breakdown = {
            "existing_task_count": existing_task_count,
            "new_task_count": new_task_count,
            "total_task_count": new_total_tasks,
            "annotation_rate": float(annotation_rate),
            "complexity_multiplier": float(complexity_multiplier),
            "buffer_multiplier": float(cls.ANNOTATION_BUFFER_MULTIPLIER),
            "original_base_fee": float(original_base_fee_decimal),
            "new_base_fee": float(new_base_fee),
            "additional_base_fee": float(additional_base_fee),
            "annotation_cost": float(new_annotation_cost),
            "storage_cost": float(storage_cost),
        }
        
        return {
            "success": True,
            "annotation_cost": float(new_annotation_cost),
            "additional_base_fee": float(additional_base_fee),
            "storage_cost": float(storage_cost),
            "total_cost": float(total_cost),
            "has_sufficient_credits": has_sufficient_credits,
            "available_credits": available_credits,
            "breakdown": breakdown,
        }

    @classmethod
    @transaction.atomic
    def charge_import_cost(cls, project, new_task_count, user=None):
        """
        Charge the organization for importing additional data.
        
        Args:
            project: Project instance
            new_task_count: Number of new tasks being imported
            user: User performing the import
            
        Returns:
            dict: Charge result
            
        Raises:
            InsufficientCreditsError: If organization doesn't have enough credits
        """
        from billing.models import ProjectBilling, OrganizationBilling, CreditTransaction
        
        if new_task_count <= 0:
            return {"success": True, "charged": 0}
        
        # Calculate import cost
        cost_info = cls.calculate_import_cost(project, new_task_count)
        
        if not cost_info["success"]:
            return cost_info
        
        total_cost = Decimal(str(cost_info["total_cost"]))
        
        if total_cost <= 0:
            return {"success": True, "charged": 0}
        
        organization = project.organization
        
        # Check credits
        try:
            org_billing = organization.billing
        except OrganizationBilling.DoesNotExist:
            org_billing = OrganizationBilling.objects.create(organization=organization)
        
        if not org_billing.has_sufficient_credits(total_cost):
            raise InsufficientCreditsError(
                f"Insufficient credits for data import. "
                f"Required: ₹{total_cost}, Available: ₹{org_billing.available_credits}"
            )
        
        # Deduct credits
        org_billing.deduct_credits(
            total_cost,
            f"Data import for project: {project.title} ({new_task_count} new tasks)"
        )
        
        # Update project billing record
        try:
            project_billing = project.billing
        except ProjectBilling.DoesNotExist:
            # Shouldn't happen for published projects, but create if needed
            project_billing = ProjectBilling.objects.create(
                project=project,
                security_deposit_required=Decimal('0'),
            )
        
        # Add to the deposit record
        additional_base_fee = Decimal(str(cost_info["additional_base_fee"]))
        annotation_cost = Decimal(str(cost_info["annotation_cost"]))
        
        project_billing.security_deposit_required += total_cost
        project_billing.security_deposit_paid += total_cost
        project_billing.estimated_annotation_cost += annotation_cost
        project_billing.save()
        
        logger.info(
            f"Import cost of ₹{total_cost} charged for project {project.title} "
            f"(ID: {project.id}) - {new_task_count} new tasks"
        )
        
        return {
            "success": True,
            "charged": float(total_cost),
            "annotation_cost": float(annotation_cost),
            "additional_base_fee": float(additional_base_fee),
            "new_task_count": new_task_count,
        }

    @classmethod
    @transaction.atomic
    def refund_security_deposit(cls, project, reason="Project completed successfully"):
        """
        Refund unused security deposit when project is completed.

        Refund = Deposit Paid - Credits Consumed - Annotation Costs

        Args:
            project: Project instance
            reason: Reason for refund

        Returns:
            dict: Refund details
        """
        try:
            project_billing = project.billing
        except ProjectBilling.DoesNotExist:
            return {"success": False, "error": "No billing record for project"}

        if project_billing.security_deposit_refunded > 0:
            return {"success": False, "error": "Deposit already refunded"}

        # Calculate refundable amount
        refundable = project_billing.refundable_deposit

        if refundable <= 0:
            return {
                "success": False,
                "error": "No refundable amount (deposit fully consumed)",
                "consumed": float(
                    project_billing.credits_consumed
                    + project_billing.actual_annotation_cost
                ),
            }

        organization = project.organization
        billing = organization.billing

        # Add refund to organization credits
        billing.add_credits(
            refundable, f"Security deposit refund for project: {project.title}"
        )

        # Get the transaction record
        refund_transaction = (
            CreditTransaction.objects.filter(
                organization=organization, transaction_type="credit"
            )
            .order_by("-created_at")
            .first()
        )

        # Update project billing
        project_billing.security_deposit_refunded = refundable
        project_billing.deposit_refunded_at = timezone.now()
        project_billing.is_deposit_held = False
        project_billing.state = ProjectBilling.ProjectState.COMPLETED
        project_billing.save()

        # Update security deposit record
        security_deposit = SecurityDeposit.objects.filter(
            project=project, status=SecurityDeposit.DepositStatus.HELD
        ).first()

        if security_deposit:
            security_deposit.amount_refunded = refundable
            security_deposit.refunded_at = timezone.now()
            security_deposit.refund_transaction = refund_transaction
            security_deposit.status = SecurityDeposit.DepositStatus.REFUNDED
            security_deposit.save()

        logger.info(
            f"Refunded ₹{refundable} security deposit for project {project.title} (ID: {project.id})"
        )

        return {
            "success": True,
            "refunded_amount": float(refundable),
            "original_deposit": float(project_billing.security_deposit_paid),
            "consumed": float(
                project_billing.credits_consumed
                + project_billing.actual_annotation_cost
            ),
            "reason": reason,
        }

    @classmethod
    @transaction.atomic
    def forfeit_security_deposit(cls, project, reason="Project abandoned"):
        """
        Forfeit security deposit when project is abandoned or edge cases not met.

        Args:
            project: Project instance
            reason: Reason for forfeiture

        Returns:
            dict: Forfeiture details
        """
        try:
            project_billing = project.billing
        except ProjectBilling.DoesNotExist:
            return {"success": False, "error": "No billing record for project"}

        # Calculate forfeit amount (remaining deposit)
        forfeit_amount = (
            project_billing.security_deposit_paid
            - project_billing.security_deposit_refunded
        )

        if forfeit_amount <= 0:
            return {"success": False, "error": "No amount to forfeit"}

        # Update project billing
        project_billing.is_deposit_held = False
        project_billing.state = ProjectBilling.ProjectState.DELETED
        project_billing.save()

        # Update security deposit record
        security_deposit = SecurityDeposit.objects.filter(
            project=project,
            status__in=[
                SecurityDeposit.DepositStatus.HELD,
                SecurityDeposit.DepositStatus.PARTIALLY_USED,
            ],
        ).first()

        if security_deposit:
            security_deposit.amount_forfeited = forfeit_amount
            security_deposit.forfeited_at = timezone.now()
            security_deposit.status = SecurityDeposit.DepositStatus.FORFEITED
            security_deposit.save()

        logger.info(
            f"Forfeited ₹{forfeit_amount} security deposit for project {project.title} "
            f"(ID: {project.id}). Reason: {reason}"
        )

        return {
            "success": True,
            "forfeited_amount": float(forfeit_amount),
            "reason": reason,
        }

    @classmethod
    @transaction.atomic
    def charge_export(
        cls,
        project,
        tasks_exported,
        annotations_exported,
        export_format="JSON",
        file_size_bytes=0,
        user=None,
    ):
        """
        Charge for data export. First export is free, subsequent exports cost credits.

        Args:
            project: Project instance
            tasks_exported: Number of tasks exported
            annotations_exported: Number of annotations exported
            export_format: Export format
            file_size_bytes: Size of export file
            user: User performing export

        Returns:
            dict: Export billing details
        """
        organization = project.organization
        billing = organization.billing

        try:
            project_billing = project.billing
        except ProjectBilling.DoesNotExist:
            project_billing = ProjectBilling.objects.create(project=project)

        # Check if first export (free)
        is_first_export = project_billing.export_count == 0

        # Check if within 24h of last export (free re-export)
        is_free_reexport = False
        if project_billing.last_export_at:
            time_since_last = timezone.now() - project_billing.last_export_at
            is_free_reexport = time_since_last < timedelta(hours=24)

        is_free = is_first_export or is_free_reexport

        # Calculate export credits
        if is_free:
            credits_charged = Decimal("0")
        else:
            # 0.1 credits per annotation
            credits_charged = Decimal(str(annotations_exported)) * Decimal("0.1")
            # Minimum 10 credits per export (after first free)
            credits_charged = max(credits_charged, Decimal("10"))

        # Check credits if not free
        if credits_charged > 0:
            if not billing.has_sufficient_credits(credits_charged):
                raise InsufficientCreditsError(
                    f"Insufficient credits for export. Required: ₹{credits_charged}, "
                    f"Available: ₹{billing.available_credits}"
                )

            billing.deduct_credits(
                credits_charged,
                f"Export of {annotations_exported} annotations from project: {project.title}",
            )

        # Record export
        export_record = ExportRecord.objects.create(
            project=project,
            organization=organization,
            exported_by=user,
            export_format=export_format,
            tasks_exported=tasks_exported,
            annotations_exported=annotations_exported,
            file_size_bytes=file_size_bytes,
            credits_charged=credits_charged,
            is_free_export=is_free,
        )

        # Update project billing
        project_billing.export_count += 1
        project_billing.last_export_at = timezone.now()
        project_billing.credits_consumed += credits_charged
        project_billing.record_activity()
        project_billing.save()

        # Update API usage
        cls._track_api_usage(organization, "export")

        logger.info(
            f"Export charged: {credits_charged} credits for {annotations_exported} annotations "
            f"from project {project.title}. Free: {is_free}"
        )

        return {
            "success": True,
            "credits_charged": float(credits_charged),
            "is_free_export": is_free,
            "export_count": project_billing.export_count,
            "tasks_exported": tasks_exported,
            "annotations_exported": annotations_exported,
        }

    @classmethod
    def check_project_lifecycle(cls, project):
        """
        Check and update project lifecycle state.

        States:
        - ACTIVE: Normal operation
        - DORMANT: No activity for 30 days
        - WARNING: Low credits (< estimated remaining cost)
        - GRACE: Credits exhausted, 30 day grace period
        - DELETED: Auto-deleted after grace period

        Args:
            project: Project instance

        Returns:
            str: New state
        """
        try:
            project_billing = project.billing
        except ProjectBilling.DoesNotExist:
            return None

        organization = project.organization
        billing = organization.billing

        current_state = project_billing.state
        now = timezone.now()

        # Check for deletion (grace period expired)
        if current_state == ProjectBilling.ProjectState.GRACE:
            if (
                project_billing.scheduled_deletion_at
                and now >= project_billing.scheduled_deletion_at
            ):
                project_billing.transition_to_state(
                    ProjectBilling.ProjectState.DELETED,
                    "Grace period expired - automatic deletion",
                )
                return ProjectBilling.ProjectState.DELETED

        # Check for grace period (zero credits)
        if billing.available_credits <= 0:
            if current_state not in [
                ProjectBilling.ProjectState.GRACE,
                ProjectBilling.ProjectState.DELETED,
            ]:
                project_billing.transition_to_state(
                    ProjectBilling.ProjectState.GRACE, "Organization credits exhausted"
                )
                return ProjectBilling.ProjectState.GRACE

        # Check for warning (low credits)
        remaining_cost_estimate = (
            project_billing.estimated_annotation_cost
            - project_billing.actual_annotation_cost
        )
        if billing.available_credits < remaining_cost_estimate:
            if current_state == ProjectBilling.ProjectState.ACTIVE:
                project_billing.transition_to_state(
                    ProjectBilling.ProjectState.WARNING,
                    f"Low credits: {billing.available_credits} < estimated remaining {remaining_cost_estimate}",
                )
                return ProjectBilling.ProjectState.WARNING

        # Check for dormant (no activity for 30 days)
        if project_billing.last_activity_at:
            days_inactive = (now - project_billing.last_activity_at).days
            if days_inactive >= cls.DORMANT_THRESHOLD_DAYS:
                if current_state == ProjectBilling.ProjectState.ACTIVE:
                    project_billing.transition_to_state(
                        ProjectBilling.ProjectState.DORMANT,
                        f"No activity for {days_inactive} days",
                    )
                    return ProjectBilling.ProjectState.DORMANT

        # If credits recovered and in warning/grace, restore to active
        if current_state in [
            ProjectBilling.ProjectState.WARNING,
            ProjectBilling.ProjectState.DORMANT,
        ]:
            if billing.available_credits >= remaining_cost_estimate:
                project_billing.transition_to_state(
                    ProjectBilling.ProjectState.ACTIVE, "Credits restored"
                )
                return ProjectBilling.ProjectState.ACTIVE

        return current_state

    @classmethod
    def _track_api_usage(cls, organization, request_type="read"):
        """Track API usage for rate limiting"""
        today = timezone.now().date()

        usage, _ = APIUsageTracking.objects.get_or_create(
            organization=organization, date=today
        )

        if request_type == "read":
            usage.increment_read()
        elif request_type == "write":
            usage.increment_write()
        elif request_type == "export":
            usage.increment_export()


class APIRateLimitService:
    """
    Service for API rate limiting and overage billing.

    Free Tier Limits (per day):
    - Read requests: 10,000
    - Write requests: 1,000
    - Export requests: 100

    Overage Rates:
    - Read: 1 credit per 1000 requests
    - Write: 5 credits per 1000 requests
    - Export: 10 credits per export
    """

    FREE_LIMITS = {
        "read": 10000,
        "write": 1000,
        "export": 100,
    }

    OVERAGE_RATES = {
        "read": Decimal("0.001"),  # 1 credit per 1000
        "write": Decimal("0.005"),  # 5 credits per 1000
        "export": Decimal("10"),  # 10 credits per export
    }

    @classmethod
    def check_rate_limit(cls, organization, request_type="read"):
        """
        Check if organization has exceeded rate limit.

        Args:
            organization: Organization instance
            request_type: Type of request (read, write, export)

        Returns:
            dict: Rate limit status
        """
        today = timezone.now().date()

        usage, _ = APIUsageTracking.objects.get_or_create(
            organization=organization, date=today
        )

        limit = cls.FREE_LIMITS.get(request_type, 10000)

        if request_type == "read":
            current = usage.read_requests
        elif request_type == "write":
            current = usage.write_requests
        else:
            current = usage.export_requests

        remaining = max(0, limit - current)
        is_over_limit = current > limit

        return {
            "request_type": request_type,
            "limit": limit,
            "used": current,
            "remaining": remaining,
            "is_over_limit": is_over_limit,
            "overage": max(0, current - limit),
        }

    @classmethod
    def track_request(cls, organization, request_type="read"):
        """
        Track an API request.

        Args:
            organization: Organization instance
            request_type: Type of request

        Returns:
            bool: True if within free limit, False if overage
        """
        today = timezone.now().date()

        usage, _ = APIUsageTracking.objects.get_or_create(
            organization=organization, date=today
        )

        if request_type == "read":
            usage.increment_read()
            return usage.read_requests <= cls.FREE_LIMITS["read"]
        elif request_type == "write":
            usage.increment_write()
            return usage.write_requests <= cls.FREE_LIMITS["write"]
        elif request_type == "export":
            usage.increment_export()
            return usage.export_requests <= cls.FREE_LIMITS["export"]

        return True

    @classmethod
    @transaction.atomic
    def charge_daily_overage(cls, organization, date=None):
        """
        Charge organization for API overage at end of day.

        Args:
            organization: Organization instance
            date: Date to charge for (defaults to yesterday)

        Returns:
            dict: Overage charge details
        """
        if date is None:
            date = (timezone.now() - timedelta(days=1)).date()

        try:
            usage = APIUsageTracking.objects.get(organization=organization, date=date)
        except APIUsageTracking.DoesNotExist:
            return {"success": False, "error": "No usage record for date"}

        if usage.charged_at:
            return {"success": False, "error": "Already charged for this date"}

        # Calculate overage credits
        credits_charged = usage.calculate_overage_credits()

        if credits_charged <= 0:
            return {
                "success": True,
                "credits_charged": 0,
                "message": "No overage charges",
            }

        # Charge organization
        billing = organization.billing

        if billing.has_sufficient_credits(credits_charged):
            billing.deduct_credits(
                credits_charged,
                f"API overage charges for {date}: "
                f"R:{usage.read_overage}/W:{usage.write_overage}/E:{usage.export_overage}",
            )

            usage.credits_charged = credits_charged
            usage.charged_at = timezone.now()
            usage.save()

            logger.info(
                f"Charged {credits_charged} credits for API overage to {organization.title} "
                f"for {date}"
            )

            return {
                "success": True,
                "credits_charged": float(credits_charged),
                "breakdown": {
                    "read_overage": usage.read_overage,
                    "write_overage": usage.write_overage,
                    "export_overage": usage.export_overage,
                },
            }
        else:
            logger.warning(
                f"Insufficient credits for API overage: {organization.title} "
                f"needs {credits_charged}, has {billing.available_credits}"
            )
            return {
                "success": False,
                "error": "Insufficient credits",
                "credits_needed": float(credits_charged),
            }


class ProjectLifecycleService:
    """
    Service for managing project lifecycle and automatic cleanup.
    Designed to run as a periodic task (daily).
    """

    @classmethod
    def process_all_projects(cls):
        """
        Process all projects for lifecycle state updates.
        Should be run daily as a Celery/RQ task.

        Returns:
            dict: Processing summary
        """
        from projects.models import Project

        summary = {
            "processed": 0,
            "dormant": 0,
            "warning": 0,
            "grace": 0,
            "deleted": 0,
            "errors": [],
        }

        # Get all projects with billing records
        project_billings = (
            ProjectBilling.objects.exclude(state=ProjectBilling.ProjectState.DELETED)
            .exclude(state=ProjectBilling.ProjectState.COMPLETED)
            .select_related("project", "project__organization")
        )

        for pb in project_billings:
            try:
                new_state = ProjectBillingService.check_project_lifecycle(pb.project)
                summary["processed"] += 1

                if new_state == ProjectBilling.ProjectState.DORMANT:
                    summary["dormant"] += 1
                    cls._send_dormant_notification(pb.project)
                elif new_state == ProjectBilling.ProjectState.WARNING:
                    summary["warning"] += 1
                    cls._send_warning_notification(pb.project)
                elif new_state == ProjectBilling.ProjectState.GRACE:
                    summary["grace"] += 1
                    cls._send_grace_notification(pb.project)
                elif new_state == ProjectBilling.ProjectState.DELETED:
                    summary["deleted"] += 1
                    cls._handle_project_deletion(pb.project)

            except Exception as e:
                summary["errors"].append({"project_id": pb.project.id, "error": str(e)})
                logger.error(f"Error processing project {pb.project.id}: {e}")

        logger.info(f"Project lifecycle processing complete: {summary}")
        return summary

    @classmethod
    def _send_dormant_notification(cls, project):
        """Send notification for dormant project"""
        # TODO: Implement email notification
        logger.info(f"[DORMANT] Project {project.id} ({project.title}) is dormant")

    @classmethod
    def _send_warning_notification(cls, project):
        """Send notification for low credits warning"""
        # TODO: Implement email notification
        logger.info(f"[WARNING] Project {project.id} ({project.title}) has low credits")

    @classmethod
    def _send_grace_notification(cls, project):
        """Send notification for grace period start"""
        # TODO: Implement email notification
        logger.info(
            f"[GRACE] Project {project.id} ({project.title}) entered grace period. "
            f"Will be deleted in 30 days."
        )

    @classmethod
    def _handle_project_deletion(cls, project):
        """Handle automatic project deletion"""
        # Forfeit remaining deposit
        ProjectBillingService.forfeit_security_deposit(
            project, reason="Automatic deletion due to expired grace period"
        )

        # TODO: Actually delete project data or mark for deletion
        # For now, we just update the state
        logger.info(
            f"[DELETED] Project {project.id} ({project.title}) marked for deletion"
        )

    @classmethod
    def get_projects_summary(cls, organization):
        """
        Get summary of projects by lifecycle state for an organization.

        Args:
            organization: Organization instance

        Returns:
            dict: Summary by state
        """
        from django.db.models import Count, Sum

        summary = (
            ProjectBilling.objects.filter(project__organization=organization)
            .values("state")
            .annotate(
                count=Count("id"),
                total_deposit=Sum("security_deposit_paid"),
                total_consumed=Sum("credits_consumed"),
            )
        )

        result = {
            "by_state": {item["state"]: item for item in summary},
            "total_projects": sum(item["count"] for item in summary),
            "total_deposit_held": sum(
                item["total_deposit"] or 0
                for item in summary
                if item["state"] in ["active", "dormant", "warning", "grace"]
            ),
        }

        return result





