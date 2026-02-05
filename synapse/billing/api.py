from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db import transaction as db_transaction
from datetime import timedelta
from decimal import Decimal
import logging

from .models import (
    SubscriptionPlan,
    CreditPackage,
    OrganizationBilling,
    Subscription,
    CreditTransaction,
    Payment,
    AnnotationPricing,
    AnnotatorEarnings,
    StorageBilling,
    ProjectBilling,
    SecurityDeposit,
    APIUsageTracking,
    ExportRecord,
)
from .serializers import (
    SubscriptionPlanSerializer,
    CreditPackageSerializer,
    OrganizationBillingSerializer,
    SubscriptionSerializer,
    CreditTransactionSerializer,
    PaymentSerializer,
    AnnotationPricingSerializer,
    AnnotatorEarningsSerializer,
    StorageBillingSerializer,
    CreatePaymentOrderSerializer,
    VerifyPaymentSerializer,
)
from .razorpay_utils import (
    create_razorpay_order,
    verify_payment_signature,
    create_razorpay_customer,
    create_razorpay_subscription,
    fetch_payment,
    fetch_order,
)
from .services import (
    ProjectBillingService,
    APIRateLimitService,
    InsufficientCreditsError,
    SecurityDepositError,
)
from .cost_estimation import CostEstimationService
from organizations.models import Organization
from projects.models import Project

logger = logging.getLogger(__name__)


class SubscriptionPlanViewSet(viewsets.ReadOnlyModelViewSet):
    """View available subscription plans"""

    queryset = SubscriptionPlan.objects.filter(is_active=True)
    serializer_class = SubscriptionPlanSerializer
    permission_classes = [IsAuthenticated]


class CreditPackageViewSet(viewsets.ReadOnlyModelViewSet):
    """View available credit packages"""

    queryset = CreditPackage.objects.filter(is_active=True)
    serializer_class = CreditPackageSerializer
    permission_classes = [IsAuthenticated]


class BillingViewSet(viewsets.ViewSet):
    """Main billing operations"""

    permission_classes = [IsAuthenticated]

    def get_organization(self):
        """Get user's organization"""
        org_id = self.request.query_params.get("organization")
        if org_id:
            org = get_object_or_404(Organization, id=org_id)
        else:
            # Get user's active organization
            org = getattr(self.request.user, "active_organization", None)
            if not org:
                orgs = self.request.user.organizations_organizationmember.filter(
                    organization__is_active=True
                ).first()
                if orgs:
                    org = orgs.organization

        if not org:
            raise ValueError("No organization found for user")

        return org

    @action(detail=False, methods=["get"], permission_classes=[])
    def razorpay_key(self, request):
        """Get Razorpay public key for frontend"""
        from django.conf import settings

        return Response(
            {
                "key_id": getattr(settings, "RAZORPAY_KEY_ID", ""),
                "test_mode": getattr(settings, "RAZORPAY_KEY_ID", "").startswith(
                    "rzp_test_"
                ),
            }
        )

    @action(detail=False, methods=["get"])
    def dashboard(self, request):
        """Get billing dashboard data"""
        try:
            org = self.get_organization()
            billing, _ = OrganizationBilling.objects.get_or_create(organization=org)

            # Recent transactions
            recent_transactions = CreditTransaction.objects.filter(organization=org)[
                :10
            ]

            # Recent payments
            recent_payments = Payment.objects.filter(organization=org)[:5]

            return Response(
                {
                    "billing": OrganizationBillingSerializer(billing).data,
                    "recent_transactions": CreditTransactionSerializer(
                        recent_transactions, many=True
                    ).data,
                    "recent_payments": PaymentSerializer(
                        recent_payments, many=True
                    ).data,
                }
            )
        except Exception as e:
            logger.error(f"Error fetching billing dashboard: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["post"])
    def create_order(self, request):
        """Create Razorpay order for payment"""
        logger.info(f"Create order request data: {request.data}")
        serializer = CreatePaymentOrderSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            org = self.get_organization()
            billing, _ = OrganizationBilling.objects.get_or_create(organization=org)

            payment_for = serializer.validated_data["payment_for"]

            # Prepare order notes
            order_notes = {
                "organization_id": org.id,
                "organization_name": org.title,
                "payment_for": payment_for,
            }

            if payment_for == "credits":
                package_id = serializer.validated_data["credit_package_id"]
                package = get_object_or_404(
                    CreditPackage, id=package_id, is_active=True
                )
                amount = package.price_inr
                description = f"{package.credits} credits package"
                order_notes["credit_package_id"] = package_id

            else:  # subscription
                plan_id = serializer.validated_data["subscription_plan_id"]
                plan = get_object_or_404(SubscriptionPlan, id=plan_id, is_active=True)
                amount = plan.price_inr
                description = f"{plan.name} subscription"
                order_notes["subscription_plan_id"] = plan_id

            # Create Razorpay customer if not exists
            if not billing.razorpay_customer_id:
                # Safely get the email: billing_email > org.created_by.email > request.user.email
                customer_email = billing.billing_email
                if not customer_email and org.created_by:
                    customer_email = org.created_by.email
                if not customer_email:
                    customer_email = request.user.email
                    
                customer = create_razorpay_customer(
                    email=customer_email, name=org.title
                )
                billing.razorpay_customer_id = customer["id"]
                billing.save()

            # Create Razorpay order with all notes
            order = create_razorpay_order(
                amount_inr=amount,
                receipt=f"{org.id}-{timezone.now().timestamp()}",
                notes=order_notes,
            )

            # Create payment record
            payment_data = {
                "organization": org,
                "payment_for": payment_for,
                "amount_inr": amount,
                "razorpay_order_id": order["id"],
                "status": "pending",
                "created_by": request.user,
            }

            if payment_for == "credits":
                payment_data["credit_package_id"] = package_id
            # Note: subscription will be linked after payment verification

            payment = Payment.objects.create(**payment_data)

            return Response(
                {
                    "order_id": order["id"],
                    "amount": order["amount"],
                    "currency": order["currency"],
                    "payment_id": payment.id,
                    "description": description,
                    "customer_id": billing.razorpay_customer_id,
                }
            )

        except Exception as e:
            logger.error(f"Error creating order: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["post"])
    def verify_payment(self, request):
        """Verify and process payment"""
        serializer = VerifyPaymentSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            order_id = serializer.validated_data["razorpay_order_id"]
            payment_id = serializer.validated_data["razorpay_payment_id"]
            signature = serializer.validated_data["razorpay_signature"]

            # Verify signature
            if not verify_payment_signature(order_id, payment_id, signature):
                # Mark as failed
                try:
                    payment = Payment.objects.get(razorpay_order_id=order_id)
                    payment.status = "failed"
                    payment.save()
                except Payment.DoesNotExist:
                    pass

                return Response(
                    {"error": "Invalid payment signature"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Get payment record
            payment = get_object_or_404(Payment, razorpay_order_id=order_id)

            with db_transaction.atomic():
                # Update payment status
                payment.razorpay_payment_id = payment_id
                payment.razorpay_signature = signature
                payment.status = "captured"
                payment.paid_at = timezone.now()

                # Fetch payment details from Razorpay
                payment_details = fetch_payment(payment_id)
                payment.payment_method = payment_details.get("method", "")
                payment.save()

                billing = payment.organization.billing

                # Process based on payment type
                if payment.payment_for == "credits":
                    # Add credits to organization
                    package = payment.credit_package
                    billing.add_credits(
                        package.credits, f"Credit purchase - {package.name}"
                    )

                else:  # subscription
                    # Fetch order from Razorpay to get plan_id from notes
                    order_details = fetch_order(order_id)
                    plan_id = order_details.get("notes", {}).get("subscription_plan_id")

                    if not plan_id:
                        raise ValueError("Subscription plan ID not found in order")

                    # Get the plan
                    plan = SubscriptionPlan.objects.get(id=plan_id)

                    # Calculate dates
                    start_date = timezone.now()
                    if plan.billing_cycle == "monthly":
                        end_date = start_date + timedelta(days=30)
                        next_billing = end_date
                    else:  # annual
                        end_date = start_date + timedelta(days=365)
                        next_billing = start_date + timedelta(days=30)

                    subscription = Subscription.objects.create(
                        organization=payment.organization,
                        plan=plan,
                        status="active",
                        start_date=start_date,
                        end_date=end_date,
                        next_billing_date=next_billing,
                    )

                    payment.subscription = subscription
                    payment.save()

                    # Update billing type
                    billing.billing_type = "subscription"
                    billing.active_subscription = subscription
                    billing.save()

                    # Allocate initial credits
                    subscription.allocate_monthly_credits()

            return Response(
                {
                    "success": True,
                    "message": "Payment verified successfully",
                    "payment": PaymentSerializer(payment).data,
                }
            )

        except Exception as e:
            logger.error(f"Error verifying payment: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["get"])
    def transactions(self, request):
        """Get credit transaction history"""
        try:
            org = self.get_organization()
            transactions = CreditTransaction.objects.filter(organization=org)

            # Filter by type if provided
            txn_type = request.query_params.get("type")
            if txn_type:
                transactions = transactions.filter(transaction_type=txn_type)

            # Filter by category if provided
            category = request.query_params.get("category")
            if category:
                transactions = transactions.filter(category=category)

            serializer = CreditTransactionSerializer(transactions, many=True)
            return Response(serializer.data)

        except Exception as e:
            logger.error(f"Error fetching transactions: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["get"])
    def payments(self, request):
        """Get payment history with pagination"""
        try:
            org = self.get_organization()
            limit = int(request.query_params.get("limit", 20))
            offset = int(request.query_params.get("offset", 0))

            payments = Payment.objects.filter(organization=org)
            total_count = payments.count()
            
            # Apply slicing
            payments = payments[offset : offset + limit]

            serializer = PaymentSerializer(payments, many=True)
            return Response({
                "results": serializer.data,
                "count": total_count,
                "limit": limit,
                "offset": offset,
                "has_more": offset + limit < total_count
            })

        except Exception as e:
            logger.error(f"Error fetching payments: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class AnnotationPricingViewSet(viewsets.ReadOnlyModelViewSet):
    """View annotation pricing rules"""

    queryset = AnnotationPricing.objects.filter(is_active=True)
    serializer_class = AnnotationPricingSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["post"])
    def calculate(self, request):
        """Calculate credit cost for annotation"""
        data_type = request.data.get("data_type")
        modality = request.data.get("modality")
        annotation_type = request.data.get("annotation_type")
        volume = int(request.data.get("volume", 1))

        try:
            pricing = AnnotationPricing.objects.get(
                data_type=data_type, modality=modality, is_active=True
            )

            credit_cost = pricing.calculate_credit(annotation_type, volume)

            return Response(
                {
                    "data_type": data_type,
                    "modality": modality,
                    "annotation_type": annotation_type,
                    "volume": volume,
                    "credit_cost": float(credit_cost),
                    "pricing_details": AnnotationPricingSerializer(pricing).data,
                }
            )

        except AnnotationPricing.DoesNotExist:
            return Response(
                {"error": "Pricing not found for specified data type and modality"},
                status=status.HTTP_404_NOT_FOUND,
            )


class ProjectBillingViewSet(viewsets.ViewSet):
    """
    API for project-level billing operations including:
    - Security deposit calculation and collection
    - Project lifecycle management
    - Export billing
    - Storage tracking
    """

    permission_classes = [IsAuthenticated]

    def get_project(self, project_id):
        """Get project and verify access"""
        project = get_object_or_404(Project, id=project_id)
        # Check if user has access to project's organization
        if not self.request.user.active_organization == project.organization:
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied("You don't have access to this project")
        return project

    @action(detail=False, methods=["post"])
    def calculate_deposit(self, request):
        """
        Calculate security deposit for a new project.

        Request body:
        {
            "project_id": 123,  // Optional, for existing project
            "label_config": "<View>...",  // Optional, label config XML
            "estimated_tasks": 100,  // Optional, number of tasks/files
            "estimated_storage_gb": 2.5,  // Optional
        }
        """
        project_id = request.data.get("project_id")
        label_config = request.data.get("label_config")
        estimated_tasks = request.data.get("estimated_tasks")
        estimated_storage_gb = request.data.get("estimated_storage_gb")

        try:
            actual_task_count = None
            actual_storage_gb = None

            if project_id:
                project = self.get_project(project_id)

                # Get actual task count and storage from database
                from data_import.models import FileUpload
                from data_import.serializers import analyze_zip_contents
                from django.db.models import Sum

                # First try tasks, then try file uploads (for draft projects)
                actual_task_count = project.tasks.count()

                # Get file uploads for the project
                file_uploads = FileUpload.objects.filter(project=project)

                if actual_task_count == 0:
                    # For draft projects, count files including ZIP contents
                    for fu in file_uploads:
                        try:
                            file_name = fu.file.name.lower() if fu.file else ''
                            if file_name.endswith('.zip'):
                                # Analyze ZIP contents to get actual file count
                                zip_analysis = analyze_zip_contents(fu.file.name)
                                if zip_analysis.get('total_files', 0) > 0:
                                    actual_task_count += zip_analysis['total_files']
                                else:
                                    # If ZIP analysis failed, count as 1
                                    actual_task_count += 1
                            else:
                                # Regular file counts as 1 task
                                actual_task_count += 1
                        except Exception:
                            actual_task_count += 1  # Count as 1 if analysis fails
                    
                    # Ensure at least 1 task if files exist
                    if actual_task_count == 0 and file_uploads.exists():
                        actual_task_count = file_uploads.count()

                # Calculate total storage from file uploads
                total_bytes = 0
                for fu in file_uploads:
                    try:
                        if fu.file and hasattr(fu.file, "size"):
                            total_bytes += fu.file.size
                    except Exception:
                        pass  # Skip files we can't read size for

                # Convert to GB
                if total_bytes > 0:
                    actual_storage_gb = Decimal(str(total_bytes)) / Decimal(
                        str(1024**3)
                    )

                # Use provided label_config if given, otherwise use project's config
                if label_config:
                    # Create a wrapper that uses the provided label_config
                    class ProjectWrapper:
                        def __init__(self, proj, config, task_count):
                            self._project = proj
                            self.label_config = config
                            self._task_count = task_count
                            # Expose organization from the original project
                            self.organization = getattr(proj, 'organization', None)

                        @property
                        def tasks(self):
                            count = self._task_count

                            class Tasks:
                                @staticmethod
                                def count():
                                    return count

                            return Tasks()

                    project = ProjectWrapper(project, label_config, actual_task_count)
            else:
                # Create a dummy project object for calculation
                # Use user's active organization to get subscription info
                user_org = getattr(request.user, 'active_organization', None)
                
                class DummyProject:
                    def __init__(self, config, organization):
                        self.label_config = config or ""
                        self.organization = organization

                        class Tasks:
                            @staticmethod
                            def count():
                                return 0

                        self.tasks = Tasks()

                project = DummyProject(label_config, user_org)

            # Use estimated storage from request, or calculated from files
            if estimated_storage_gb:
                storage_gb = Decimal(str(estimated_storage_gb))
            elif actual_storage_gb:
                storage_gb = actual_storage_gb
            else:
                storage_gb = None

            # Use estimated_tasks from request, or actual_task_count from DB
            task_count = estimated_tasks or actual_task_count or 1

            deposit = ProjectBillingService.calculate_security_deposit(
                project,
                estimated_tasks=task_count,
                estimated_storage_gb=storage_gb,
            )

            return Response({"success": True, **deposit})

        except Exception as e:
            logger.error(f"Error calculating deposit: {e}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["post"])
    def estimate_cost(self, request):
        """
        Get detailed cost estimation for project creation and annotation work.
        
        This provides a comprehensive breakdown including:
        - Upfront deposit cost
        - Expected actual cost after completion
        - Expected refund amount
        - Cost per task breakdown
        - Formula explanation
        
        Request body:
        {
            "task_count": 100,
            "label_config": "<View>...",  // Optional
            "estimated_storage_gb": 2.5,  // Optional
            "avg_duration_mins": 3,  // Optional, for audio/video
            "annotation_types": ["rectanglelabels"],  // Optional
            "label_count": 10  // Optional
        }
        """
        task_count = request.data.get("task_count")
        label_config = request.data.get("label_config")
        estimated_storage_gb = request.data.get("estimated_storage_gb")
        avg_duration_mins = request.data.get("avg_duration_mins")
        annotation_types = request.data.get("annotation_types")
        label_count = request.data.get("label_count")
        # Note: required_overlap is NOT client-configurable
        # It defaults to 3 and can only be adjusted by the system algorithm
        
        if not task_count:
            return Response(
                {"error": "task_count is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            estimation = CostEstimationService.estimate_project_cost(
                task_count=int(task_count),
                label_config=label_config,
                estimated_storage_gb=float(estimated_storage_gb) if estimated_storage_gb else None,
                avg_duration_mins=float(avg_duration_mins) if avg_duration_mins else None,
                annotation_types=annotation_types,
                label_count=int(label_count) if label_count else None,
                # Overlap is system-controlled, always use default (3)
            )
            
            return Response({
                "success": True,
                **estimation
            })
            
        except Exception as e:
            logger.error(f"Error estimating cost: {e}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=["get"])
    def cost_formula(self, request):
        """
        Get detailed documentation of cost calculation formulas.
        
        Returns comprehensive explanation of:
        - Project creation cost calculation
        - Annotation work cost calculation
        - Complexity multipliers
        - Rate tables
        - Example calculations
        """
        try:
            documentation = CostEstimationService.get_formula_documentation()
            
            return Response({
                "success": True,
                "documentation": documentation,
                "rate_tables": {
                    "annotation_rates": {k: float(v) for k, v in CostEstimationService.ANNOTATION_RATES.items()},
                    "duration_rates": {k: float(v) for k, v in CostEstimationService.DURATION_RATES.items()},
                    "base_deposit_fee": float(CostEstimationService.BASE_DEPOSIT_FEE),
                    "storage_rate_per_gb": float(CostEstimationService.STORAGE_RATE_PER_GB),
                    "buffer_multiplier": float(CostEstimationService.ANNOTATION_BUFFER_MULTIPLIER),
                },
                "complexity_tiers": [
                    {
                        "max_labels": tier[0] if tier[0] != float('inf') else "unlimited",
                        "multiplier": float(tier[1]),
                        "level": tier[2]
                    }
                    for tier in CostEstimationService.COMPLEXITY_TIERS
                ]
            })
            
        except Exception as e:
            logger.error(f"Error getting cost formula: {e}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["get"])
    def storage_info(self, request):
        """
        Get storage information for organization or project.
        
        Query params:
        - project_id: Get storage info for specific project
        - organization: Get storage info for specific organization (default: user's active org)
        
        Returns storage usage, free limits, and cost estimates.
        """
        from billing.storage_service import StorageCalculationService
        
        project_id = request.query_params.get("project_id")
        
        try:
            if project_id:
                # Get project storage info
                project = self.get_project(project_id)
                storage_info = StorageCalculationService.calculate_project_total_storage(project)
                
                # Get subscription plan for the project's org
                billing = project.organization.billing
                subscription_plan = None
                if billing.active_subscription and billing.active_subscription.is_active():
                    subscription_plan = billing.active_subscription.plan
                
                # Calculate deposit for this storage
                deposit_info = StorageCalculationService.calculate_storage_deposit(
                    storage_info["total_gb_decimal"],
                    subscription_plan
                )
                
                return Response({
                    "success": True,
                    "type": "project",
                    "project_id": project.id,
                    "storage": storage_info,
                    "deposit": deposit_info,
                    "subscription_plan": subscription_plan.name if subscription_plan else "Pay As You Go"
                })
            else:
                # Get organization storage info
                org = self.get_organization()
                storage_info = StorageCalculationService.calculate_organization_storage(org)
                
                # Get monthly cost estimate
                billing = org.billing
                subscription_plan = None
                if billing.active_subscription and billing.active_subscription.is_active():
                    subscription_plan = billing.active_subscription.plan
                
                monthly_estimate = StorageCalculationService.estimate_monthly_storage_cost(org)
                
                return Response({
                    "success": True,
                    "type": "organization",
                    "organization_id": org.id,
                    "storage": storage_info,
                    "monthly_estimate": monthly_estimate,
                    "subscription_plan": subscription_plan.name if subscription_plan else "Pay As You Go",
                    "free_storage_gb": float(subscription_plan.storage_gb) if subscription_plan else 1.0,
                })
                
        except Exception as e:
            logger.error(f"Error getting storage info: {e}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["post"])
    def update_project_storage(self, request):
        """
        Manually update storage calculations for a project.
        
        Request body:
        {
            "project_id": 123
        }
        
        Recalculates storage from file uploads and tasks.
        """
        from billing.storage_service import StorageCalculationService
        
        project_id = request.data.get("project_id")
        
        if not project_id:
            return Response(
                {"error": "project_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            project = self.get_project(project_id)
            storage_info = StorageCalculationService.update_project_storage(project)
            
            # Also update organization storage
            if project.organization:
                StorageCalculationService.update_organization_storage(project.organization)
            
            return Response({
                "success": True,
                "project_id": project.id,
                "storage": storage_info
            })
            
        except Exception as e:
            logger.error(f"Error updating project storage: {e}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["post"])
    def collect_deposit(self, request):
        """
        Collect security deposit for a project.

        Request body:
        {
            "project_id": 123,
            "deposit_amount": 1537,  # Optional: use calculated amount from frontend
            "estimated_tasks": 32,   # Optional: task count for deposit calc
            "estimated_storage_gb": 0.5  # Optional: storage estimate
        }
        """
        project_id = request.data.get("project_id")
        deposit_amount = request.data.get(
            "deposit_amount"
        )  # Pre-calculated amount from frontend
        estimated_tasks = request.data.get("estimated_tasks")
        estimated_storage_gb = request.data.get("estimated_storage_gb")

        if not project_id:
            return Response(
                {"error": "project_id is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            project = self.get_project(project_id)

            project_billing = ProjectBillingService.create_project_billing(
                project,
                user=request.user,
                deposit_amount=Decimal(str(deposit_amount)) if deposit_amount else None,
                estimated_tasks=estimated_tasks,
                estimated_storage_gb=(
                    Decimal(str(estimated_storage_gb)) if estimated_storage_gb else None
                ),
            )

            return Response(
                {
                    "success": True,
                    "project_id": project.id,
                    "deposit_collected": float(project_billing.security_deposit_paid),
                    "state": project_billing.state,
                }
            )

        except InsufficientCreditsError as e:
            return Response(
                {"error": str(e), "code": "insufficient_credits"},
                status=status.HTTP_402_PAYMENT_REQUIRED,
            )
        except Exception as e:
            logger.error(f"Error collecting deposit: {e}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["post"])
    def calculate_import_cost(self, request):
        """
        Calculate the cost for importing additional data into an existing project.

        Request body:
        {
            "project_id": 123,
            "new_task_count": 50,
            "file_upload_ids": [1, 2, 3]  # Optional
        }
        """
        project_id = request.data.get("project_id")
        new_task_count = request.data.get("new_task_count", 0)
        file_upload_ids = request.data.get("file_upload_ids")

        if not project_id:
            return Response(
                {"error": "project_id is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            project = self.get_project(project_id)
            
            result = ProjectBillingService.calculate_import_cost(
                project,
                new_task_count=new_task_count,
                file_upload_ids=file_upload_ids,
            )
            
            return Response(result)
            
        except Exception as e:
            logger.error(f"Error calculating import cost: {e}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["post"])
    def charge_import_cost(self, request):
        """
        Charge the organization for importing additional data.

        Request body:
        {
            "project_id": 123,
            "new_task_count": 50
        }
        """
        project_id = request.data.get("project_id")
        new_task_count = request.data.get("new_task_count", 0)

        if not project_id:
            return Response(
                {"error": "project_id is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        if new_task_count <= 0:
            return Response(
                {"error": "new_task_count must be greater than 0"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            project = self.get_project(project_id)
            
            result = ProjectBillingService.charge_import_cost(
                project,
                new_task_count=new_task_count,
                user=request.user,
            )
            
            return Response(result)
            
        except InsufficientCreditsError as e:
            return Response(
                {"error": str(e), "code": "insufficient_credits"},
                status=status.HTTP_402_PAYMENT_REQUIRED,
            )
        except Exception as e:
            logger.error(f"Error charging import cost: {e}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["post"])
    def calculate_deletion_refund(self, request):
        """
        Calculate refund amount for deleting tasks based on unfilled annotation slots.
        
        With 3x overlap, each task has 3 annotation slots.
        Refund = unfilled_slots × cost_per_slot
        
        Examples:
        - Task with 0 annotations: Refund 3 slots
        - Task with 1 annotation: Refund 2 slots
        - Task with 2 annotations: Refund 1 slot
        - Task with 3 annotations: Refund 0 slots (work complete)
        
        Request body:
        {
            "project_id": 123,
            "task_ids": [1, 2, 3, 4, 5]
        }
        
        Response:
        {
            "success": true,
            "tasks_total": 5,
            "overlap_per_task": 3,
            "total_slots_charged": 15,
            "slots_filled": 6,
            "slots_refundable": 9,
            "cost_per_slot": 15.0,
            "refund_amount": 135.0,
            "per_task_breakdown": [...]
        }
        """
        project_id = request.data.get("project_id")
        task_ids = request.data.get("task_ids", [])

        if not project_id:
            return Response(
                {"error": "project_id is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        if not task_ids:
            return Response(
                {"error": "task_ids is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            from billing.cost_estimation import CostEstimationService
            from decimal import Decimal
            
            project = self.get_project(project_id)
            
            # Default overlap
            OVERLAP = CostEstimationService.DEFAULT_OVERLAP
            
            # Calculate cost per slot
            config_analysis = ProjectBillingService._analyze_label_config(project.label_config or "")
            complexity_multiplier = config_analysis["complexity_multiplier"]
            
            data_types = list(project.data_types.keys()) if project.data_types else ["image"]
            annotation_rate = ProjectBillingService._calculate_annotation_rate(
                config_analysis["annotation_types"],
                data_types=data_types
            )
            
            cost_per_slot = (
                annotation_rate
                * complexity_multiplier
                * ProjectBillingService.ANNOTATION_BUFFER_MULTIPLIER
            )
            
            # Calculate slot-based refund
            refund_info = CostEstimationService.calculate_slot_based_refund(
                task_ids=task_ids,
                cost_per_slot=cost_per_slot,
                overlap=OVERLAP,
            )
            
            return Response({
                "success": True,
                **refund_info,
                "breakdown": {
                    "annotation_rate": float(annotation_rate),
                    "complexity_multiplier": float(complexity_multiplier),
                    "buffer_multiplier": float(ProjectBillingService.ANNOTATION_BUFFER_MULTIPLIER),
                }
            })
            
        except Exception as e:
            logger.error(f"Error calculating deletion refund: {e}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["post"])
    def calculate_project_deletion_refund(self, request):
        """
        Calculate refund for project deletion based on slot-based work completion.
        
        With 3x overlap, work completion is measured by filled annotation slots:
        - Total slots = total_tasks × 3
        - Filled slots = sum(min(annotation_count, 3) for each task)
        - Work completion % = (filled_slots / total_slots) × 100
        
        Refund policy:
        - If work done >= 30%: Only refund unfilled slots cost
        - If work done < 30%: Refund base fee + buffer + unfilled slots cost
        
        Request body:
        {
            "project_id": 123
        }
        
        Response:
        {
            "success": true,
            "total_tasks": 100,
            "overlap_per_task": 3,
            "total_slots": 300,
            "filled_slots": 75,
            "unfilled_slots": 225,
            "work_done_percentage": 25.0,
            "threshold_percentage": 30,
            "meets_threshold": false,
            "refund_amount": 3200.0,
            "breakdown": {
                "base_fee_refund": 500.0,
                "buffer_refund": 450.0,
                "unfilled_slots_refund": 2250.0,
                ...
            }
        }
        """
        project_id = request.data.get("project_id")

        if not project_id:
            return Response(
                {"error": "project_id is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            project = self.get_project(project_id)
            
            result = ProjectBillingService.calculate_project_deletion_refund(project)
            
            return Response(result)
            
        except Exception as e:
            logger.error(f"Error calculating project deletion refund: {e}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["post"])
    def refund_deposit(self, request):
        """
        Refund security deposit for a completed project.

        Request body:
        {
            "project_id": 123,
            "reason": "Project completed successfully"
        }
        """
        project_id = request.data.get("project_id")
        reason = request.data.get("reason", "Project completed")

        if not project_id:
            return Response(
                {"error": "project_id is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            project = self.get_project(project_id)

            result = ProjectBillingService.refund_security_deposit(project, reason)

            if result["success"]:
                return Response(result)
            else:
                return Response(result, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.error(f"Error refunding deposit: {e}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["get"])
    def project_status(self, request):
        """
        Get billing status for a project.

        Query params:
        - project_id: Project ID
        """
        project_id = request.query_params.get("project_id")

        if not project_id:
            return Response(
                {"error": "project_id is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            project = self.get_project(project_id)

            try:
                billing = project.billing
            except ProjectBilling.DoesNotExist:
                return Response(
                    {
                        "project_id": project.id,
                        "has_billing": False,
                        "message": "No billing record for this project",
                    }
                )

            # Get security deposit history
            deposits = SecurityDeposit.objects.filter(project=project).order_by(
                "-created_at"
            )

            # Get export history
            exports = ExportRecord.objects.filter(project=project).order_by(
                "-created_at"
            )[:5]

            return Response(
                {
                    "project_id": project.id,
                    "has_billing": True,
                    "state": billing.state,
                    "security_deposit": {
                        "required": float(billing.security_deposit_required),
                        "paid": float(billing.security_deposit_paid),
                        "refunded": float(billing.security_deposit_refunded),
                        "refundable": float(billing.refundable_deposit),
                    },
                    "costs": {
                        "estimated_annotation": float(
                            billing.estimated_annotation_cost
                        ),
                        "actual_annotation": float(billing.actual_annotation_cost),
                        "credits_consumed": float(billing.credits_consumed),
                    },
                    "storage": {
                        "used_gb": float(billing.storage_used_gb),
                        "last_calculated": billing.last_storage_calculated,
                    },
                    "activity": {
                        "last_activity": billing.last_activity_at,
                        "last_export": billing.last_export_at,
                        "export_count": billing.export_count,
                    },
                    "lifecycle": {
                        "state": billing.state,
                        "state_changed_at": billing.state_changed_at,
                        "dormant_since": billing.dormant_since,
                        "grace_period_start": billing.grace_period_start,
                        "scheduled_deletion": billing.scheduled_deletion_at,
                    },
                    "deposits": [
                        {
                            "id": d.id,
                            "total": float(d.total_deposit),
                            "status": d.status,
                            "paid_at": d.paid_at,
                            "refunded_at": d.refunded_at,
                        }
                        for d in deposits[:5]
                    ],
                    "recent_exports": [
                        {
                            "id": e.id,
                            "format": e.export_format,
                            "tasks": e.tasks_exported,
                            "credits_charged": float(e.credits_charged),
                            "is_free": e.is_free_export,
                            "created_at": e.created_at,
                        }
                        for e in exports
                    ],
                }
            )

        except Exception as e:
            logger.error(f"Error getting project status: {e}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["get"])
    def deletion_warnings(self, request):
        """
        Get warnings and information before deleting a project.

        This endpoint analyzes the project state and returns a list of
        warnings/edge cases the user should be aware of before deletion.

        Query params:
        - project_id: Project ID

        Returns:
        - warnings: List of warning objects with severity, message, and details
        - can_delete: Boolean indicating if deletion is allowed
        - refund_estimate: Estimated refund amount if applicable
        """
        project_id = request.query_params.get("project_id")

        if not project_id:
            return Response(
                {"error": "project_id is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            project = self.get_project(project_id)
            warnings = []
            can_delete = True
            refund_estimate = Decimal("0")

            # Get project statistics
            task_count = project.tasks.count()
            annotation_count = (
                project.annotations.count() if hasattr(project, "annotations") else 0
            )

            # Try to get annotation count through tasks if direct access fails
            if annotation_count == 0:
                from tasks.models import Annotation

                annotation_count = Annotation.objects.filter(
                    task__project=project
                ).count()

            # Check for billing record
            has_billing = False
            billing = None
            try:
                billing = project.billing
                has_billing = True
            except ProjectBilling.DoesNotExist:
                pass

            # === WARNING 1: Unexported annotations ===
            if annotation_count > 0:
                # Check if any exports have been done
                export_count = 0
                last_export = None
                if has_billing:
                    export_count = billing.export_count
                    last_export = billing.last_export_at
                else:
                    export_count = ExportRecord.objects.filter(project=project).count()
                    last_record = (
                        ExportRecord.objects.filter(project=project)
                        .order_by("-created_at")
                        .first()
                    )
                    if last_record:
                        last_export = last_record.created_at

                if export_count == 0:
                    warnings.append(
                        {
                            "severity": "critical",
                            "type": "no_export",
                            "title": "Work Never Exported",
                            "message": f"This project has {annotation_count} annotations that have NEVER been exported. Deleting will permanently lose all this work.",
                            "details": {
                                "annotation_count": annotation_count,
                                "export_count": 0,
                            },
                            "action_suggested": "Export your data before deleting",
                        }
                    )
                elif last_export:
                    # Check for annotations after last export
                    from tasks.models import Annotation

                    annotations_after_export = Annotation.objects.filter(
                        task__project=project, created_at__gt=last_export
                    ).count()

                    if annotations_after_export > 0:
                        warnings.append(
                            {
                                "severity": "high",
                                "type": "unexported_annotations",
                                "title": "Annotations Not Exported",
                                "message": f"{annotations_after_export} annotations have been created since your last export on {last_export.strftime('%Y-%m-%d %H:%M')}.",
                                "details": {
                                    "unexported_count": annotations_after_export,
                                    "last_export": (
                                        last_export.isoformat() if last_export else None
                                    ),
                                },
                                "action_suggested": "Export recent annotations before deleting",
                            }
                        )

            # === WARNING 2: Tasks with no annotations (incomplete work) ===
            if task_count > 0:
                from tasks.models import Task

                tasks_without_annotations = Task.objects.filter(
                    project=project, total_annotations=0
                ).count()

                completion_rate = (
                    ((task_count - tasks_without_annotations) / task_count * 100)
                    if task_count > 0
                    else 0
                )

                if tasks_without_annotations > 0 and completion_rate < 100:
                    severity = "high" if completion_rate < 50 else "medium"
                    warnings.append(
                        {
                            "severity": severity,
                            "type": "incomplete_tasks",
                            "title": "Incomplete Annotation Work",
                            "message": f"{tasks_without_annotations} out of {task_count} tasks ({100 - completion_rate:.1f}%) have not been annotated.",
                            "details": {
                                "total_tasks": task_count,
                                "incomplete_tasks": tasks_without_annotations,
                                "completion_rate": round(completion_rate, 1),
                            },
                            "action_suggested": "Complete or export partial work before deleting",
                        }
                    )

            # === WARNING 3: Security deposit status ===
            if has_billing and billing.security_deposit_paid > 0:
                refund_estimate = billing.refundable_deposit

                if billing.state == ProjectBilling.ProjectState.ACTIVE:
                    # Check if there are annotations - work has been done
                    if annotation_count > 0:
                        # Calculate consumed credits
                        consumed = billing.credits_consumed
                        refund = billing.security_deposit_paid - consumed

                        warnings.append(
                            {
                                "severity": "medium",
                                "type": "deposit_partial_refund",
                                "title": "Partial Deposit Refund",
                                "message": f"You will receive a partial refund of {float(refund):.0f} credits. {float(consumed):.0f} credits were consumed for annotations.",
                                "details": {
                                    "deposit_paid": float(
                                        billing.security_deposit_paid
                                    ),
                                    "credits_consumed": float(consumed),
                                    "refund_amount": float(refund),
                                },
                                "action_suggested": None,
                            }
                        )
                    else:
                        # No work done, full refund
                        warnings.append(
                            {
                                "severity": "info",
                                "type": "deposit_full_refund",
                                "title": "Full Deposit Refund",
                                "message": f"You will receive a full refund of {float(billing.security_deposit_paid):.0f} credits.",
                                "details": {
                                    "refund_amount": float(
                                        billing.security_deposit_paid
                                    ),
                                },
                                "action_suggested": None,
                            }
                        )
                        refund_estimate = billing.security_deposit_paid

                elif billing.state == ProjectBilling.ProjectState.DORMANT:
                    warnings.append(
                        {
                            "severity": "high",
                            "type": "dormant_project",
                            "title": "Project is Dormant",
                            "message": "This project has been inactive. Deposit refund may be reduced based on inactivity period.",
                            "details": {
                                "dormant_since": (
                                    billing.dormant_since.isoformat()
                                    if billing.dormant_since
                                    else None
                                ),
                            },
                            "action_suggested": None,
                        }
                    )

                elif billing.state == ProjectBilling.ProjectState.GRACE:
                    warnings.append(
                        {
                            "severity": "critical",
                            "type": "grace_period",
                            "title": "Project in Grace Period",
                            "message": "This project is in its grace period before automatic deletion. Export your data immediately if needed.",
                            "details": {
                                "grace_start": (
                                    billing.grace_period_start.isoformat()
                                    if billing.grace_period_start
                                    else None
                                ),
                                "scheduled_deletion": (
                                    billing.scheduled_deletion_at.isoformat()
                                    if billing.scheduled_deletion_at
                                    else None
                                ),
                            },
                            "action_suggested": "Export data before deletion deadline",
                        }
                    )

            # === WARNING 4: Active assignments (annotators working) ===
            try:
                from annotators.models import AnnotatorAssignment

                active_assignments = AnnotatorAssignment.objects.filter(
                    project=project, status__in=["pending", "in_progress"]
                ).count()

                if active_assignments > 0:
                    warnings.append(
                        {
                            "severity": "high",
                            "type": "active_assignments",
                            "title": "Annotators Currently Assigned",
                            "message": f"{active_assignments} annotators are currently assigned to this project. Their work will be terminated.",
                            "details": {
                                "active_assignments": active_assignments,
                            },
                            "action_suggested": "Notify annotators before deleting",
                        }
                    )
            except Exception:
                pass  # Annotator module may not be available

            # === WARNING 5: Pending payments ===
            try:
                pending_payments = Payment.objects.filter(
                    organization=project.organization, status="pending"
                ).count()

                if pending_payments > 0:
                    warnings.append(
                        {
                            "severity": "medium",
                            "type": "pending_payments",
                            "title": "Pending Payments",
                            "message": f"There are {pending_payments} pending payments in your organization. Resolve these before deleting projects.",
                            "details": {
                                "pending_count": pending_payments,
                            },
                            "action_suggested": "Complete pending payments first",
                        }
                    )
            except Exception:
                pass

            # === WARNING 6: Large dataset ===
            if task_count > 1000:
                warnings.append(
                    {
                        "severity": "info",
                        "type": "large_dataset",
                        "title": "Large Dataset",
                        "message": f"This project contains {task_count} tasks. Deletion may take a few moments.",
                        "details": {
                            "task_count": task_count,
                        },
                        "action_suggested": None,
                    }
                )

            # === WARNING 7: Stored files/media ===
            from data_import.models import FileUpload

            file_uploads = FileUpload.objects.filter(project=project)
            file_count = file_uploads.count()

            if file_count > 0:
                # Calculate total storage
                total_size = 0
                for fu in file_uploads:
                    try:
                        if fu.file and hasattr(fu.file, "size"):
                            total_size += fu.file.size
                    except Exception:
                        pass

                size_mb = total_size / (1024 * 1024)

                warnings.append(
                    {
                        "severity": "info",
                        "type": "stored_files",
                        "title": "Uploaded Files",
                        "message": f"{file_count} files ({size_mb:.1f} MB) will be permanently deleted.",
                        "details": {
                            "file_count": file_count,
                            "size_mb": round(size_mb, 2),
                        },
                        "action_suggested": "Ensure you have backups if needed",
                    }
                )

            # Sort warnings by severity
            severity_order = {
                "critical": 0,
                "high": 1,
                "medium": 2,
                "low": 3,
                "info": 4,
            }
            warnings.sort(key=lambda x: severity_order.get(x["severity"], 5))

            # Calculate detailed refund breakdown using new project deletion refund logic
            refund_breakdown = {
                "deposit_paid": 0,
                "annotation_cost": 0,
                "credits_consumed": 0,
                "total_consumed": 0,
                "refund_amount": 0,
            }

            if has_billing:
                # Use new project deletion refund calculation
                project_refund_data = ProjectBillingService.calculate_project_deletion_refund(project)
                
                if project_refund_data.get("success"):
                    # Convert all to float for consistent JSON serialization
                    annotated_cost = float(project_refund_data.get("breakdown", {}).get("annotated_tasks_cost", 0))
                    credits_consumed = float(billing.credits_consumed)
                    
                    refund_breakdown = {
                        "deposit_paid": float(billing.security_deposit_paid),
                        "annotation_cost": annotated_cost,
                        "credits_consumed": credits_consumed,
                        "total_consumed": annotated_cost + credits_consumed,
                        "refund_amount": float(project_refund_data.get("refund_amount", 0)),
                        "work_done_percentage": float(project_refund_data.get("work_done_percentage", 0)),
                        "meets_threshold": project_refund_data.get("meets_threshold", False),
                        "base_fee_refund": float(project_refund_data.get("breakdown", {}).get("base_fee_refund", 0)),
                        "buffer_refund": float(project_refund_data.get("breakdown", {}).get("buffer_refund", 0)),
                        "unannotated_tasks_refund": float(project_refund_data.get("breakdown", {}).get("unannotated_tasks_refund", 0)),
                    }
                    refund_estimate = Decimal(str(project_refund_data.get("refund_amount", 0)))
                else:
                    # Fallback to old calculation
                    refund_breakdown = {
                        "deposit_paid": float(billing.security_deposit_paid),
                        "annotation_cost": float(billing.actual_annotation_cost),
                        "credits_consumed": float(billing.credits_consumed),
                        "total_consumed": float(
                            billing.credits_consumed + billing.actual_annotation_cost
                        ),
                        "refund_amount": float(billing.refundable_deposit),
                    }

            return Response(
                {
                    "project_id": project.id,
                    "project_title": project.title,
                    "can_delete": can_delete,
                    "warnings": warnings,
                    "summary": {
                        "task_count": task_count,
                        "annotation_count": annotation_count,
                        "has_unexported_work": any(
                            w["type"] in ["no_export", "unexported_annotations"]
                            for w in warnings
                        ),
                        "refund_estimate": float(refund_estimate),
                    },
                    "refund_breakdown": refund_breakdown,
                }
            )

        except Exception as e:
            logger.error(f"Error getting deletion warnings: {e}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["get"])
    def organization_summary(self, request):
        """
        Get billing summary for all projects in organization.
        """
        try:
            org = request.user.active_organization
            if not org:
                return Response(
                    {"error": "No active organization"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            from .services import ProjectLifecycleService

            summary = ProjectLifecycleService.get_projects_summary(org)

            # Add organization billing info
            try:
                billing = org.billing
                summary["organization_credits"] = float(billing.available_credits)
            except OrganizationBilling.DoesNotExist:
                summary["organization_credits"] = 0

            return Response(summary)

        except Exception as e:
            logger.error(f"Error getting organization summary: {e}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class APIUsageViewSet(viewsets.ViewSet):
    """API for viewing API usage and rate limits"""

    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["get"])
    def current(self, request):
        """Get current day's API usage"""
        try:
            org = request.user.active_organization
            if not org:
                return Response(
                    {"error": "No active organization"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            today = timezone.now().date()

            usage, _ = APIUsageTracking.objects.get_or_create(
                organization=org, date=today
            )

            return Response(
                {
                    "date": str(today),
                    "read_requests": {
                        "used": usage.read_requests,
                        "limit": usage.free_read_limit,
                        "remaining": max(
                            0, usage.free_read_limit - usage.read_requests
                        ),
                        "overage": usage.read_overage,
                    },
                    "write_requests": {
                        "used": usage.write_requests,
                        "limit": usage.free_write_limit,
                        "remaining": max(
                            0, usage.free_write_limit - usage.write_requests
                        ),
                        "overage": usage.write_overage,
                    },
                    "export_requests": {
                        "used": usage.export_requests,
                        "limit": usage.free_export_limit,
                        "remaining": max(
                            0, usage.free_export_limit - usage.export_requests
                        ),
                        "overage": usage.export_overage,
                    },
                    "estimated_overage_cost": float(usage.calculate_overage_credits()),
                }
            )

        except Exception as e:
            logger.error(f"Error getting API usage: {e}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["get"])
    def history(self, request):
        """Get API usage history for the past 30 days"""
        try:
            org = request.user.active_organization
            if not org:
                return Response(
                    {"error": "No active organization"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            from_date = timezone.now().date() - timedelta(days=30)

            usage_history = APIUsageTracking.objects.filter(
                organization=org, date__gte=from_date
            ).order_by("-date")

            return Response(
                {
                    "history": [
                        {
                            "date": str(u.date),
                            "read_requests": u.read_requests,
                            "write_requests": u.write_requests,
                            "export_requests": u.export_requests,
                            "credits_charged": float(u.credits_charged),
                        }
                        for u in usage_history
                    ]
                }
            )

        except Exception as e:
            logger.error(f"Error getting API usage history: {e}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)





