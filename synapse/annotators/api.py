"""
Annotator APIs
- Uses Django authentication
- Annotator = normal User
- AnnotatorProfile = metadata only
"""

import logging
from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.contrib.auth import authenticate, login
from django.utils import timezone
from django.core.mail import send_mail
from django.db import models

from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.exceptions import PermissionDenied, NotAuthenticated

from users.models import User
from tasks.models import Task
from .models import AnnotatorProfile, TaskAssignment, ProjectAssignment
from .serializers import (
    AnnotatorRegistrationSerializer,
    AnnotatorProfileSerializer,
)
from django.contrib.auth import logout
from rest_framework.authtoken.models import Token


logger = logging.getLogger(__name__)


class AnnotatorRegistrationAPI(generics.CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = AnnotatorRegistrationSerializer

    def perform_create(self, serializer):
        profile = serializer.save()
        self._send_verification_email(profile)

    def _send_verification_email(self, profile: AnnotatorProfile):
        verification_url = (
            f"{settings.HOSTNAME}/annotators/verify-email?"
            f"token={profile.verification_token}"
        )

        send_mail(
            subject="Verify your annotator account",
            message=(
                f"Hello {profile.user.get_full_name()},\n\n"
                f"Verify your email:\n{verification_url}\n\n"
                "This link expires in 24 hours."
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[profile.user.email],
            fail_silently=True,
        )


class AnnotatorEmailVerificationAPI(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        token = request.data.get("token")
        if not token:
            return Response({"detail": "Token required"}, status=400)

        try:
            profile = AnnotatorProfile.objects.get(verification_token=token)
        except AnnotatorProfile.DoesNotExist:
            return Response({"detail": "Invalid token"}, status=400)

        if profile.verification_token_created:
            if timezone.now() > profile.verification_token_created + timedelta(
                hours=24
            ):
                return Response({"detail": "Token expired"}, status=400)

        profile.verify_email()

        return Response(
            {
                "message": "Email verified successfully",
                "status": profile.status,
            },
            status=200,
        )


class ResendVerificationEmailAPI(APIView):
    """API to resend verification email"""

    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")

        if not email:
            return Response(
                {"error": "Email is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(email=email)
            profile = user.annotator_profile

            if profile.email_verified:
                return Response(
                    {"error": "Email is already verified"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Generate new token
            profile.generate_verification_token()

            # Send email
            verification_url = f"{settings.HOSTNAME}/annotators/verify-email?token={profile.verification_token}"

            subject = "Verify Your Email - Synapse Annotator"
            message = f"""
            Hello {profile.user.get_full_name()},
            
            Here is your new verification link:
            
            {verification_url}
            
            This link will expire in 24 hours.
            
            Best regards,
            Synapse Team
            """

            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [profile.user.email],
                fail_silently=False,
            )

            return Response(
                {"message": "Verification email sent successfully"},
                status=status.HTTP_200_OK,
            )

        except User.DoesNotExist:
            return Response(
                {"error": "No account found with this email"},
                status=status.HTTP_404_NOT_FOUND,
            )
        except AnnotatorProfile.DoesNotExist:
            return Response(
                {"error": "No annotator profile found for this account"},
                status=status.HTTP_404_NOT_FOUND,
            )


class AnnotatorProfileAPI(generics.RetrieveUpdateAPIView):
    """
    Profile API that handles both annotators and experts.
    Returns role-specific data for RBAC.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = AnnotatorProfileSerializer

    def get_object(self):
        try:
            return self.request.user.annotator_profile
        except AnnotatorProfile.DoesNotExist:
            raise PermissionDenied("Not an annotator")

    def get(self, request, *args, **kwargs):
        """Override get to handle both annotator and expert profiles"""
        from .models import ExpertProfile

        user = request.user
        response_data = {
            "user": {
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
            },
            "roles": [],
            "permissions": [],
        }

        # Check for expert profile
        try:
            expert = user.expert_profile
            response_data["roles"].append("expert")
            response_data["expert"] = {
                "id": expert.id,
                "status": expert.status,
                "expertise_level": expert.expertise_level,
                "expertise_areas": expert.expertise_areas,
                "total_reviews": expert.total_reviews_completed,
                "approval_rate": float(expert.approval_rate),
                "total_earned": float(expert.total_earned),
                "available_balance": float(expert.available_balance),
                "pending_payout": float(expert.pending_payout),
                "current_workload": expert.current_workload,
                "max_reviews_per_day": expert.max_reviews_per_day,
            }
            response_data["permissions"].extend(
                [
                    "view_expert_dashboard",
                    "review_tasks",
                    "approve_annotations",
                    "reject_annotations",
                    "correct_annotations",
                    "view_expert_earnings",
                    "request_expert_payout",
                ]
            )
        except ExpertProfile.DoesNotExist:
            pass

        # Check for annotator profile
        try:
            annotator = user.annotator_profile
            response_data["roles"].append("annotator")
            response_data["annotator"] = {
                "id": annotator.id,
                "status": annotator.status,
                "email_verified": annotator.email_verified,
                "is_approved": annotator.is_active_annotator,
                "total_earned": float(annotator.total_earned),
                "available_balance": float(annotator.available_balance),
                "pending_approval": float(annotator.pending_approval),
            }
            response_data["permissions"].extend(
                [
                    "view_annotator_dashboard",
                    "annotate_tasks",
                    "view_annotator_earnings",
                    "request_annotator_payout",
                ]
            )
        except AnnotatorProfile.DoesNotExist:
            pass

        # If no profile found
        if not response_data["roles"]:
            return Response(
                {"error": "No annotator or expert profile found"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Set primary role (expert takes precedence if user has both)
        response_data["primary_role"] = response_data["roles"][0]

        return Response(response_data, status=status.HTTP_200_OK)


class AnnotatorTestStatusAPI(APIView):
    """API to check test status"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            profile = request.user.annotator_profile

            return Response(
                {
                    "email_verified": profile.email_verified,
                    "status": profile.status,
                    "can_take_test": profile.can_take_test,
                    "is_approved": profile.is_active_annotator,
                },
                status=status.HTTP_200_OK,
            )

        except AnnotatorProfile.DoesNotExist:
            return Response(
                {"error": "No annotator profile found"},
                status=status.HTTP_404_NOT_FOUND,
            )


class AnnotatorTestQuestionsAPI(APIView):
    """API to get test questions"""

    permission_classes = [AllowAny]

    def get(self, request):
        from .test_data import get_full_test
        import copy

        # Return test without answers - use deep copy to avoid modifying original
        test_data = copy.deepcopy(get_full_test())

        # Remove correct answers and explanations
        for question in test_data["knowledge_questions"]:
            question.pop("correct_answer", None)

        for task in test_data["text_annotation_tasks"]:
            task.pop("ground_truth", None)

        for task in test_data["classification_tasks"]:
            task.pop("correct_answer", None)
            task.pop("explanation", None)

        return Response(test_data, status=status.HTTP_200_OK)


class AnnotatorTestStartAPI(APIView):
    """API to start a test attempt"""

    permission_classes = [AllowAny]

    def post(self, request):
        # For now, we'll use session or a simple token
        # In production, you'd want proper authentication

        # Create a test attempt
        # For MVP, we can track this in memory or session
        # Later, create a database record

        # Generate a simple attempt ID
        import uuid

        attempt_id = str(uuid.uuid4())

        # Store in session
        request.session["test_attempt_id"] = attempt_id
        request.session["test_start_time"] = timezone.now().isoformat()

        return Response(
            {"attempt_id": attempt_id, "started_at": timezone.now()},
            status=status.HTTP_200_OK,
        )


class AnnotatorTestSubmitAPI(APIView):
    """API to submit test answers and get results"""

    permission_classes = [AllowAny]

    def post(self, request):
        from .test_data import get_full_test
        from .scoring import calculate_test_score

        attempt_id = request.data.get("attempt_id")
        client_results = request.data.get(
            "results"
        )  # Trust client results if provided (for Skill Tests)

        # If we have client results for skill tests (String IDs, new frontend), accept them for now
        # because the backend doesn't have the "Computer Vision" test definitions in test_data.py yet.
        if client_results and isinstance(client_results, dict):
            # Pass through the client results but ensure status fields are added
            results = client_results
            passed = results.get("passed", False)

            if passed:
                status_value = "approved"  # Immediately approve passing users
                feedback = "Congratulations! You've passed the test and your account is now active."
            else:
                status_value = "pending_test"
                feedback = "You did not meet the minimum passing criteria. Please review the study materials and try again in 7 days."

            can_retake_at = (
                (timezone.now() + timedelta(days=7)).isoformat() if not passed else None
            )

            # UPDATE USER STATUS IN DATABASE
            # Try multiple ways to get the user
            user = None
            
            # Method 1: Check if user is authenticated
            if request.user.is_authenticated:
                user = request.user
                logger.info(f"Test submit: User authenticated as {user.email}")
            else:
                logger.warning(f"Test submit: User NOT authenticated. Session key: {request.session.session_key}")
                # Method 2: Try to get user from session
                try:
                    from django.contrib.auth import get_user
                    session_user = get_user(request)
                    if session_user.is_authenticated:
                        user = session_user
                        logger.info(f"Test submit: Got user from session: {user.email}")
                except Exception as e:
                    logger.warning(f"Test submit: Could not get user from session: {e}")
            
            # Update status if we found the user
            if user:
                # Get or create profile
                profile, created = AnnotatorProfile.objects.get_or_create(
                    user=user,
                    defaults={
                        "email_verified": True, # Assume verified if they are taking test
                        "status": "pending_test"
                    }
                )
                
                if created:
                    logger.info(f"Created new AnnotatorProfile for user {user.email}")

                # Only update if status is changing to avoid unnecessary db writes
                if profile.status != status_value:
                    profile.status = status_value
                    profile.save(update_fields=["status"])
                    
                    # If approved, set approved_at timestamp
                    if status_value == "approved" and not profile.approved_at:
                        profile.approved_at = timezone.now()
                        profile.save(update_fields=["approved_at"])
                        
                    logger.info(f"SUCCESS: Updated annotator_profile status to '{status_value}' for user {user.email}")

                    # Sync User model status (prevent desync)
                    if user.annotator_status != status_value:
                        user.annotator_status = status_value
                        user.save(update_fields=["annotator_status"])
                        logger.info(f"Synced User.annotator_status to '{status_value}'")
            else:
                logger.warning(f"Test submit: Could not update status - no valid user found")

            # Return the enriched results
            response_data = {
                **results,
                "status": status_value,
                "can_retake_at": can_retake_at,
                "feedback": feedback,
            }
            return Response(response_data, status=status.HTTP_200_OK)

        # Fallback to legacy backend scoring logic (requires attempt_id and integer IDs)
        if not attempt_id:
            return Response(
                {"error": "Invalid test attempt"}, status=status.HTTP_400_BAD_REQUEST
            )

        mcq_answers = request.data.get("mcq_answers", {})
        text_annotations = request.data.get("text_annotations", {})
        classification_answers = request.data.get("classification_answers", {})

        # Get test data
        test_data = get_full_test()

        # Safely convert string keys to integers, ignoring non-integer keys (like 'cv-001')
        def safe_int_map(d):
            new_d = {}
            for k, v in d.items():
                try:
                    new_d[int(k)] = v
                except (ValueError, TypeError):
                    pass
            return new_d

        mcq_answers = safe_int_map(mcq_answers)
        text_annotations = safe_int_map(text_annotations)
        classification_answers = safe_int_map(classification_answers)

        # Calculate score
        results = calculate_test_score(
            mcq_answers, text_annotations, classification_answers, test_data
        )

        # Determine status
        if results["passed"]:
            status_value = "approved"  # Immediately approve passing users
            feedback = "Congratulations! You've passed the test and your account is now active."
        else:
            status_value = "pending_test"
            feedback = "You did not meet the minimum passing criteria. Please review the study materials and try again in 7 days."

        # Calculate retake date
        can_retake_at = (
            (timezone.now() + timedelta(days=7)).isoformat()
            if not results["passed"]
            else None
        )

        # UPDATE USER STATUS IN DATABASE
        if request.user.is_authenticated:
            user = request.user
            # Get or create profile
            profile, created = AnnotatorProfile.objects.get_or_create(
                user=user,
                defaults={
                    "email_verified": True,
                    "status": "pending_test"
                }
            )
            
            if created:
                logger.info(f"Created new AnnotatorProfile for user {user.email}")

            if profile.status != status_value:
                profile.status = status_value
                profile.save(update_fields=["status"])
                
                if status_value == "approved" and not profile.approved_at:
                    profile.approved_at = timezone.now()
                    profile.save(update_fields=["approved_at"])
                    
                logger.info(f"Updated annotator_profile status to '{status_value}' for user {user.email}")

                # Sync User model status (prevent desync)
                if user.annotator_status != status_value:
                    user.annotator_status = status_value
                    user.save(update_fields=["annotator_status"])
                    logger.info(f"Synced User.annotator_status to '{status_value}'")

        results.update(
            {
                "status": status_value,
                "can_retake_at": can_retake_at,
                "feedback": feedback,
            }
        )

        return Response(results, status=status.HTTP_200_OK)


class AnnotatorLoginAPI(APIView):
    """
    Login API for annotators only.
    Experts should use the standard client login at /user/login.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        if not email or not password:
            return Response({"detail": "Email and password required"}, status=400)

        user = authenticate(request, username=email, password=password)
        if not user:
            return Response({"detail": "Invalid credentials"}, status=401)

        # Check for annotator profile
        try:
            profile = user.annotator_profile
        except AnnotatorProfile.DoesNotExist:
            return Response(
                {
                    "detail": "Not an annotator account. Experts should use the main login page."
                },
                status=403,
            )

        if not profile.email_verified:
            return Response({"detail": "Email not verified"}, status=403)

        # Login the user
        login(request, user)

        return Response(
            {
                "message": "Login successful",
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                },
                "role": "annotator",
                "status": profile.status,
                "is_approved": profile.is_active_annotator,
            },
            status=200,
        )


class AnnotatorProjectsAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            profile = request.user.annotator_profile
        except AnnotatorProfile.DoesNotExist:
            raise PermissionDenied("Not an annotator")

        # Only get projects where annotator has ACTIVE task assignments
        # (assigned or in_progress status)
        from django.db.models import Count, Q
        
        # Get project IDs where annotator has active tasks
        project_ids_with_tasks = TaskAssignment.objects.filter(
            annotator=profile,
            status__in=["assigned", "in_progress"]
        ).values_list("task__project_id", flat=True).distinct()
        
        # Get project assignments only for those projects
        assignments = ProjectAssignment.objects.filter(
            annotator=profile,
            active=True,
            project_id__in=project_ids_with_tasks
        ).select_related("project").annotate(
            active_tasks=Count(
                "project__tasks__annotator_assignments",
                filter=Q(
                    project__tasks__annotator_assignments__annotator=profile,
                    project__tasks__annotator_assignments__status__in=["assigned", "in_progress"]
                )
            )
        )

        return Response(
            [
                {
                    "id": a.project.id,
                    "title": a.project.title,
                    "assigned_at": a.assigned_at,
                    "role": a.role,
                    "active_tasks": a.active_tasks,
                }
                for a in assignments
            ]
        )


class AnnotatorTasksAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            profile = request.user.annotator_profile
        except AnnotatorProfile.DoesNotExist:
            raise PermissionDenied("Not an annotator")

        tasks = (
            Task.objects.filter(annotator_assignments__annotator=profile)
            .distinct()
            .order_by("-updated_at")
        )

        return Response(
            {
                "total": tasks.count(),
                "tasks": [
                    {
                        "id": t.id,
                        "project": t.project_id,
                        "data": t.data,
                        "updated_at": t.updated_at,
                    }
                    for t in tasks
                ],
            }
        )


class AnnotatorTaskAssignmentAPI(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        annotator_id = request.data.get("annotator_id")
        task_id = request.data.get("task_id")

        if not annotator_id or not task_id:
            return Response({"detail": "Missing params"}, status=400)

        profile = AnnotatorProfile.objects.get(id=annotator_id)
        task = Task.objects.get(id=task_id)

        assignment, _ = TaskAssignment.objects.get_or_create(
            annotator=profile,
            task=task,
            defaults={"status": "assigned"},
        )

        return Response(
            {
                "annotator": profile.user.email,
                "task": task.id,
                "status": assignment.status,
            }
        )


class AnnotatorLogoutAPI(APIView):
    def post(self, request):
        logout(request)
        return Response({"success": True})


# ============================================================================
# PAYMENT APIS
# ============================================================================


class AnnotatorEarningsAPI(APIView):
    """Get annotator earnings summary"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            profile = request.user.annotator_profile
        except AnnotatorProfile.DoesNotExist:
            return Response(
                {"error": "Not an annotator account"}, status=status.HTTP_403_FORBIDDEN
            )

        from .payment_service import PayoutService

        summary = PayoutService.get_earnings_summary(profile)

        return Response(summary, status=status.HTTP_200_OK)


class AnnotatorTransactionsAPI(APIView):
    """Get annotator transaction history"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            profile = request.user.annotator_profile
        except AnnotatorProfile.DoesNotExist:
            return Response(
                {"error": "Not an annotator account"}, status=status.HTTP_403_FORBIDDEN
            )

        from .models import EarningsTransaction

        # Pagination
        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 20))
        offset = (page - 1) * page_size

        # Filter by type
        tx_type = request.query_params.get("type")

        queryset = EarningsTransaction.objects.filter(annotator=profile)
        if tx_type:
            queryset = queryset.filter(transaction_type=tx_type)

        total = queryset.count()
        transactions = queryset.order_by("-created_at")[offset : offset + page_size]

        return Response(
            {
                "total": total,
                "page": page,
                "page_size": page_size,
                "transactions": [
                    {
                        "id": t.id,
                        "type": t.transaction_type,
                        "stage": t.earning_stage,
                        "amount": float(t.amount),
                        "balance_after": float(t.balance_after),
                        "description": t.description,
                        "task_id": (
                            t.task_assignment.task_id if t.task_assignment else None
                        ),
                        "created_at": t.created_at.isoformat(),
                    }
                    for t in transactions
                ],
            },
            status=status.HTTP_200_OK,
        )


class AnnotatorTrustLevelAPI(APIView):
    """Get annotator trust level details"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            profile = request.user.annotator_profile
        except AnnotatorProfile.DoesNotExist:
            return Response(
                {"error": "Not an annotator account"}, status=status.HTTP_403_FORBIDDEN
            )

        from .models import TrustLevel

        trust_level, created = TrustLevel.objects.get_or_create(annotator=profile)

        # Calculate progress to next level
        current_level = trust_level.level
        next_level = None
        progress = {}

        level_order = ["new", "junior", "regular", "senior", "expert"]
        current_index = level_order.index(current_level)

        if current_index < len(level_order) - 1:
            next_level = level_order[current_index + 1]
            next_thresholds = TrustLevel.LEVEL_THRESHOLDS[next_level]

            progress = {
                "tasks": {
                    "current": trust_level.tasks_completed,
                    "required": next_thresholds["tasks"],
                    "percentage": min(
                        100,
                        (trust_level.tasks_completed / max(1, next_thresholds["tasks"]))
                        * 100,
                    ),
                },
                "accuracy": {
                    "current": float(trust_level.accuracy_score),
                    "required": next_thresholds["accuracy"],
                    "percentage": min(
                        100,
                        (
                            float(trust_level.accuracy_score)
                            / max(1, next_thresholds["accuracy"])
                        )
                        * 100,
                    ),
                },
                "honeypot": {
                    "current": float(trust_level.honeypot_pass_rate),
                    "required": next_thresholds["honeypot_rate"],
                    "percentage": min(
                        100,
                        (
                            float(trust_level.honeypot_pass_rate)
                            / max(1, next_thresholds["honeypot_rate"])
                        )
                        * 100,
                    ),
                },
            }

        return Response(
            {
                "level": trust_level.level,
                "multiplier": float(trust_level.multiplier),
                "tasks_completed": trust_level.tasks_completed,
                "accuracy_score": float(trust_level.accuracy_score),
                "honeypot_pass_rate": float(trust_level.honeypot_pass_rate),
                "total_honeypots": trust_level.total_honeypots,
                "passed_honeypots": trust_level.passed_honeypots,
                "fraud_flags": trust_level.fraud_flags,
                "is_suspended": trust_level.is_suspended,
                "next_level": next_level,
                "progress": progress,
                "all_levels": {
                    level: {
                        "multiplier": float(TrustLevel.LEVEL_MULTIPLIERS[level]),
                        "thresholds": TrustLevel.LEVEL_THRESHOLDS[level],
                    }
                    for level in level_order
                },
            },
            status=status.HTTP_200_OK,
        )


class PayoutRequestAPI(APIView):
    """Create and manage payout requests"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get payout request history"""
        try:
            profile = request.user.annotator_profile
        except AnnotatorProfile.DoesNotExist:
            return Response(
                {"error": "Not an annotator account"}, status=status.HTTP_403_FORBIDDEN
            )

        from .models import PayoutRequest

        payouts = PayoutRequest.objects.filter(annotator=profile).order_by(
            "-requested_at"
        )

        return Response(
            {
                "payouts": [
                    {
                        "id": p.id,
                        "amount": float(p.amount),
                        "status": p.status,
                        "payout_method": p.payout_method,
                        "transaction_id": p.transaction_id,
                        "failure_reason": p.failure_reason,
                        "requested_at": p.requested_at.isoformat(),
                        "processed_at": (
                            p.processed_at.isoformat() if p.processed_at else None
                        ),
                    }
                    for p in payouts
                ]
            },
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        """Create a new payout request"""
        try:
            profile = request.user.annotator_profile
        except AnnotatorProfile.DoesNotExist:
            return Response(
                {"error": "Not an annotator account"}, status=status.HTTP_403_FORBIDDEN
            )

        from decimal import Decimal
        from .payment_service import PayoutService

        amount = Decimal(str(request.data.get("amount", 0)))
        payout_method = request.data.get("payout_method", "bank_transfer")

        result = PayoutService.create_payout_request(profile, amount, payout_method)

        if result["success"]:
            return Response(result, status=status.HTTP_201_CREATED)
        else:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)


class PayoutCancelAPI(APIView):
    """Cancel a pending payout request"""

    permission_classes = [IsAuthenticated]

    def post(self, request, payout_id):
        try:
            profile = request.user.annotator_profile
        except AnnotatorProfile.DoesNotExist:
            return Response(
                {"error": "Not an annotator account"}, status=status.HTTP_403_FORBIDDEN
            )

        from .models import PayoutRequest

        try:
            payout = PayoutRequest.objects.get(id=payout_id, annotator=profile)
            payout.cancel()
            return Response({"success": True, "message": "Payout cancelled"})
        except PayoutRequest.DoesNotExist:
            return Response(
                {"error": "Payout not found"}, status=status.HTTP_404_NOT_FOUND
            )
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class BankDetailsAPI(APIView):
    """Manage annotator bank details"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get current bank details"""
        try:
            profile = request.user.annotator_profile
        except AnnotatorProfile.DoesNotExist:
            return Response(
                {"error": "Not an annotator account"}, status=status.HTTP_403_FORBIDDEN
            )

        # Mask sensitive data
        account_number = profile.account_number
        masked_account = (
            f"****{account_number[-4:]}"
            if account_number and len(account_number) > 4
            else ""
        )

        return Response(
            {
                "bank_name": profile.bank_name,
                "account_number": masked_account,
                "ifsc_code": profile.ifsc_code,
                "account_holder_name": profile.account_holder_name,
                "upi_id": profile.upi_id,
                "has_bank_details": bool(profile.bank_name and profile.account_number),
                "has_upi": bool(profile.upi_id),
            },
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        """Update bank details"""
        try:
            profile = request.user.annotator_profile
        except AnnotatorProfile.DoesNotExist:
            return Response(
                {"error": "Not an annotator account"}, status=status.HTTP_403_FORBIDDEN
            )

        data = request.data

        # Update fields if provided
        if "bank_name" in data:
            profile.bank_name = data["bank_name"]
        if "account_number" in data:
            profile.account_number = data["account_number"]
        if "ifsc_code" in data:
            profile.ifsc_code = data["ifsc_code"]
        if "account_holder_name" in data:
            profile.account_holder_name = data["account_holder_name"]
        if "upi_id" in data:
            profile.upi_id = data["upi_id"]

        profile.save(
            update_fields=[
                "bank_name",
                "account_number",
                "ifsc_code",
                "account_holder_name",
                "upi_id",
            ]
        )

        return Response(
            {"success": True, "message": "Bank details updated"},
            status=status.HTTP_200_OK,
        )


class PaymentSettingsAPI(APIView):
    """Get payment configuration"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        from .payment_service import PaymentService, PayoutService
        from .models import TrustLevel

        return Response(
            {
                "base_rates": {
                    k: float(v) for k, v in PaymentService.BASE_RATES.items()
                },
                "complexity_multipliers": {
                    k: float(v)
                    for k, v in PaymentService.COMPLEXITY_MULTIPLIERS.items()
                },
                "minimum_payout": float(PayoutService.MINIMUM_PAYOUT),
                "escrow_splits": {
                    "immediate": 40,
                    "consensus": 40,
                    "review": 20,
                },
                "trust_levels": {
                    level: {
                        "multiplier": float(TrustLevel.LEVEL_MULTIPLIERS[level]),
                        "thresholds": TrustLevel.LEVEL_THRESHOLDS[level],
                    }
                    for level in TrustLevel.LEVEL_MULTIPLIERS.keys()
                },
            },
            status=status.HTTP_200_OK,
        )


class TestPayoutAPI(APIView):
    """
    Test payout API - Send a test payment of ₹1 to verify RazorpayX integration.
    Only accessible by admin users or the annotator themselves for testing.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Create a test payout of ₹1

        Request body:
        {
            "amount": 1,  # Amount in INR (default ₹1)
            "payout_method": "upi",  # or "bank_transfer"
            "user_id": 123  # Optional: admin can test for specific user
        }
        """
        from decimal import Decimal
        from .payment_service import PayoutService

        user = request.user
        amount = Decimal(str(request.data.get("amount", 1)))
        payout_method = request.data.get("payout_method", "upi")

        # Admin can test for any user
        target_user_id = request.data.get("user_id")
        if target_user_id and user.is_superuser:
            try:
                from users.models import User

                target_user = User.objects.get(id=target_user_id)
            except User.DoesNotExist:
                return Response(
                    {"success": False, "error": "User not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )
        else:
            target_user = user

        # Check if user has annotator profile
        try:
            profile = target_user.annotator_profile
        except AnnotatorProfile.DoesNotExist:
            return Response(
                {"success": False, "error": "Not an annotator account"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Validate amount (max ₹10 for test payouts)
        if amount > Decimal("10"):
            return Response(
                {"success": False, "error": "Test payout amount cannot exceed ₹10"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if amount < Decimal("1"):
            return Response(
                {"success": False, "error": "Minimum test payout is ₹1"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Process test payout
        result = PayoutService.create_test_payout(
            user=target_user,
            amount_inr=float(amount),
            payout_method=payout_method,
        )

        if result["success"]:
            return Response(result, status=status.HTTP_200_OK)
        else:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)


class RazorpayXBalanceAPI(APIView):
    """Get RazorpayX account balance - Admin only"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user.is_superuser:
            return Response(
                {"error": "Admin access required"},
                status=status.HTTP_403_FORBIDDEN,
            )

        from .razorpayx_payout import get_account_balance, is_test_mode

        balance = get_account_balance()
        balance["is_test_mode"] = is_test_mode()
        return Response(balance, status=status.HTTP_200_OK)


class RazorpayTestModeAPI(APIView):
    """
    Get Razorpay test mode information including test bank accounts and UPI IDs.
    This helps users test the payout flow without real money.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get test mode configuration and test bank accounts/UPI IDs"""
        from .razorpayx_payout import get_test_mode_info, is_test_mode

        if not is_test_mode():
            return Response(
                {
                    "is_test_mode": False,
                    "message": "Razorpay is in LIVE mode. Real money will be transferred.",
                    "warning": "Do not use test accounts in live mode!",
                },
                status=status.HTTP_200_OK,
            )

        test_info = get_test_mode_info()
        return Response(test_info, status=status.HTTP_200_OK)


class TestPayoutWithTestAccountAPI(APIView):
    """
    Create a test payout using Razorpay's test bank accounts.
    This is specifically for testing the RazorpayX integration.
    Only works in test mode.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Create a test payout using test bank account or UPI

        Request body:
        {
            "amount": 1,  # Amount in INR (default ₹1, max ₹10)
            "payout_method": "bank_transfer",  # or "upi"
            "test_scenario": "success"  # success, pending, failed, reversed
        }
        """
        from decimal import Decimal
        from .razorpayx_payout import (
            is_test_mode,
            TEST_BANK_ACCOUNTS,
            TEST_UPI_IDS,
            create_test_payout,
        )

        if not is_test_mode():
            return Response(
                {
                    "success": False,
                    "error": "This endpoint only works in test mode. Razorpay is in LIVE mode.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        amount = Decimal(str(request.data.get("amount", 1)))
        payout_method = request.data.get("payout_method", "bank_transfer")
        test_scenario = request.data.get("test_scenario", "success")

        # Validate amount
        if amount < Decimal("1") or amount > Decimal("10"):
            return Response(
                {
                    "success": False,
                    "error": "Test payout amount must be between ₹1 and ₹10",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Get test account based on scenario
        user = request.user
        email = user.email
        name = user.get_full_name() or email

        try:
            if payout_method == "upi":
                # Use test UPI ID
                test_upi = TEST_UPI_IDS.get(test_scenario, TEST_UPI_IDS["success"])
                result = create_test_payout(
                    email=email,
                    name=name,
                    upi_id=test_upi,
                    amount_inr=float(amount),
                )
            else:
                # Use test bank account
                test_bank = TEST_BANK_ACCOUNTS.get(
                    test_scenario, TEST_BANK_ACCOUNTS["success"]
                )
                result = create_test_payout(
                    email=email,
                    name=name,
                    bank_details={
                        "account_number": test_bank["account_number"],
                        "ifsc_code": test_bank["ifsc_code"],
                        "account_holder_name": test_bank["account_holder_name"],
                    },
                    amount_inr=float(amount),
                )

            if result["success"]:
                result["test_mode"] = True
                result["test_scenario"] = test_scenario
                result["note"] = "This is a test payout. No real money was transferred."
                return Response(result, status=status.HTTP_200_OK)
            else:
                return Response(result, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response(
                {"success": False, "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class AdminPayoutApprovalAPI(APIView):
    """Admin API to approve and process payout requests"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get all pending payout requests"""
        if not request.user.is_superuser:
            return Response(
                {"error": "Admin access required"},
                status=status.HTTP_403_FORBIDDEN,
            )

        from .models import PayoutRequest

        pending = PayoutRequest.objects.filter(status="pending").order_by(
            "-requested_at"
        )

        return Response(
            {
                "pending_payouts": [
                    {
                        "id": p.id,
                        "annotator": {
                            "id": p.annotator.id,
                            "email": p.annotator.user.email,
                            "name": p.annotator.user.get_full_name(),
                        },
                        "amount": float(p.amount),
                        "payout_method": p.payout_method,
                        "bank_details": p.bank_details,
                        "requested_at": p.requested_at.isoformat(),
                    }
                    for p in pending
                ],
                "total_pending": pending.count(),
                "total_amount": float(sum(p.amount for p in pending)),
            }
        )

    def post(self, request, payout_id=None):
        """Approve and process a payout request"""
        if not request.user.is_superuser:
            return Response(
                {"error": "Admin access required"},
                status=status.HTTP_403_FORBIDDEN,
            )

        payout_id = payout_id or request.data.get("payout_id")
        if not payout_id:
            return Response(
                {"error": "payout_id required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from .models import PayoutRequest
        from .payment_service import PayoutService

        try:
            payout = PayoutRequest.objects.get(id=payout_id)
        except PayoutRequest.DoesNotExist:
            return Response(
                {"error": "Payout not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        result = PayoutService.approve_and_process_payout(payout, request.user)

        if result["success"]:
            return Response(result, status=status.HTTP_200_OK)
        else:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)


class AdminPayoutRejectAPI(APIView):
    """Admin API to reject payout requests"""

    permission_classes = [IsAuthenticated]

    def post(self, request, payout_id):
        """Reject a payout request"""
        if not request.user.is_superuser:
            return Response(
                {"error": "Admin access required"},
                status=status.HTTP_403_FORBIDDEN,
            )

        from .models import PayoutRequest

        reason = request.data.get("reason", "Rejected by admin")

        try:
            payout = PayoutRequest.objects.get(id=payout_id)
            payout.reject(request.user, reason)
            return Response(
                {
                    "success": True,
                    "message": "Payout rejected",
                }
            )
        except PayoutRequest.DoesNotExist:
            return Response(
                {"error": "Payout not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        except ValueError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )


# ============================================================================
# AUTOMATIC TASK ASSIGNMENT APIs
# ============================================================================


class TriggerAutoAssignmentAPI(APIView):
    """
    Manually trigger automatic task assignment for a project.

    Only accessible by project owners and admins.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        POST /api/annotators/trigger-assignment/

        Request body:
        {
            "project_id": 123,
            "async": true  # Optional, defaults to true
        }
        """
        from projects.models import Project
        from annotators.tasks import trigger_auto_assignment
        from organizations.models import OrganizationMember

        project_id = request.data.get("project_id")
        async_mode = request.data.get("async", True)

        if not project_id:
            return Response(
                {"error": "project_id is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            return Response(
                {"error": f"Project {project_id} not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Check permissions - must be org owner/admin or project creator
        user = request.user

        # Check if superuser
        if not user.is_superuser:
            # Check if user is client
            if not user.is_client:
                return Response(
                    {"error": "Only clients can trigger assignment"},
                    status=status.HTTP_403_FORBIDDEN,
                )

            # Check organization membership
            if project.organization:
                try:
                    member = OrganizationMember.objects.get(
                        user=user,
                        organization=project.organization,
                        deleted_at__isnull=True,
                    )
                    # Must be owner or admin
                    if not (member.is_owner or member.is_admin):
                        return Response(
                            {
                                "error": "Only organization owners/admins can trigger assignment"
                            },
                            status=status.HTTP_403_FORBIDDEN,
                        )
                except OrganizationMember.DoesNotExist:
                    return Response(
                        {"error": "You are not a member of this organization"},
                        status=status.HTTP_403_FORBIDDEN,
                    )

        # Check if project is published
        if not project.is_published:
            return Response(
                {"error": "Project must be published before triggering assignment"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check if project has tasks
        task_count = project.tasks.count()
        if task_count == 0:
            return Response(
                {"error": "Project has no tasks to assign"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Trigger assignment
        try:
            if async_mode:
                job = trigger_auto_assignment(project_id, async_mode=True)
                return Response(
                    {
                        "success": True,
                        "message": f"Auto-assignment queued for project {project_id}",
                        "job_id": job.id,
                        "async": True,
                        "project_id": project_id,
                        "task_count": task_count,
                    },
                    status=status.HTTP_202_ACCEPTED,
                )
            else:
                result = trigger_auto_assignment(project_id, async_mode=False)
                return Response(
                    {
                        "success": result.get("success", False),
                        "message": result.get("message", "Assignment complete"),
                        "annotators_assigned": result.get("annotators_assigned", 0),
                        "async": False,
                        "project_id": project_id,
                    },
                    status=status.HTTP_200_OK,
                )

        except Exception as e:
            logger.exception(f"Error triggering auto-assignment: {e}")
            return Response(
                {"error": f"Failed to trigger assignment: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class AssignmentMetricsAPI(APIView):
    """Get assignment metrics for a project"""

    permission_classes = [IsAuthenticated]

    def get(self, request, project_id):
        """
        GET /api/annotators/assignment-metrics/{project_id}/

        Returns assignment effectiveness metrics for a project.
        """
        from projects.models import Project
        from annotators.assignment_engine import AssignmentEngine
        from organizations.models import OrganizationMember

        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            return Response(
                {"error": f"Project {project_id} not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Check permissions
        user = request.user
        if not user.is_superuser:
            if project.organization:
                if not project.organization.has_user(user):
                    return Response(
                        {"error": "You do not have access to this project"},
                        status=status.HTTP_403_FORBIDDEN,
                    )

        # Calculate metrics
        try:
            metrics = AssignmentEngine.calculate_assignment_metrics(project)

            # Add project info
            metrics["project"] = {
                "id": project.id,
                "title": project.title,
                "is_published": project.is_published,
                "total_tasks": project.tasks.count(),
                "completed_tasks": project.tasks.filter(is_labeled=True).count(),
            }

            return Response(metrics, status=status.HTTP_200_OK)

        except Exception as e:
            logger.exception(f"Error calculating metrics: {e}")
            return Response(
                {"error": f"Failed to calculate metrics: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


# ============================================================================
# GAMIFICATION APIs
# ============================================================================


class AnnotatorEarningsAPI(APIView):
    """Get earnings summary for the authenticated annotator"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        GET /api/annotators/earnings/

        Returns comprehensive earnings summary including:
        - Total earned, pending, available balance
        - Weekly/monthly breakdowns
        - Trust level info
        - Recent transactions
        """
        from .payment_service import PayoutService

        try:
            profile = request.user.annotator_profile
        except AnnotatorProfile.DoesNotExist:
            return Response(
                {"error": "No annotator profile found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        earnings = PayoutService.get_earnings_summary(profile)
        return Response(earnings, status=status.HTTP_200_OK)


class AnnotatorGamificationStatsAPI(APIView):
    """Get gamification stats for the authenticated annotator"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        GET /api/annotators/gamification/

        Returns:
        - Streak info (current, longest, multiplier)
        - Trust level
        - Achievements earned
        - Skill badges
        - Leaderboard history
        """
        from .payment_service import GamificationService

        try:
            profile = request.user.annotator_profile
        except AnnotatorProfile.DoesNotExist:
            return Response(
                {"error": "No annotator profile found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        stats = GamificationService.get_annotator_gamification_stats(profile)
        return Response(stats, status=status.HTTP_200_OK)


class LeaderboardAPI(APIView):
    """Get current leaderboard"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        GET /api/annotators/leaderboard/
        GET /api/annotators/leaderboard/?date=2024-01-15

        Returns leaderboard for specified date (default: today).
        """
        from .models import DailyLeaderboard
        from datetime import datetime

        date_str = request.query_params.get("date")
        if date_str:
            try:
                date = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                return Response(
                    {"error": "Invalid date format. Use YYYY-MM-DD"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            date = timezone.now().date()

        leaderboard = DailyLeaderboard.objects.filter(date=date).order_by(
            "-tasks_completed", "-quality_score"
        )[:50]

        # Get current user's position
        user_position = None
        try:
            profile = request.user.annotator_profile
            user_entry = DailyLeaderboard.objects.filter(
                date=date, annotator=profile
            ).first()
            if user_entry:
                # Calculate rank if not set
                rank = (
                    leaderboard.filter(
                        tasks_completed__gt=user_entry.tasks_completed
                    ).count()
                    + 1
                )
                user_position = {
                    "rank": rank,
                    "tasks_completed": user_entry.tasks_completed,
                    "earnings": float(user_entry.earnings),
                    "quality_score": float(user_entry.quality_score),
                }
        except AnnotatorProfile.DoesNotExist:
            pass

        entries = []
        for rank, entry in enumerate(leaderboard, 1):
            entries.append(
                {
                    "rank": rank,
                    "annotator_name": entry.annotator.user.get_full_name()
                    or entry.annotator.user.username,
                    "tasks_completed": entry.tasks_completed,
                    "earnings": float(entry.earnings),
                    "quality_score": float(entry.quality_score),
                    "is_current_user": (
                        hasattr(request.user, "annotator_profile")
                        and entry.annotator_id == request.user.annotator_profile.id
                    ),
                }
            )

        return Response(
            {
                "date": str(date),
                "entries": entries,
                "user_position": user_position,
            },
            status=status.HTTP_200_OK,
        )


class AchievementsAPI(APIView):
    """Get achievements list and progress"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        GET /api/annotators/achievements/

        Returns all achievements with user's progress.
        """
        from .models import Achievement, AnnotatorAchievement
        from .payment_service import GamificationService

        # Ensure achievements exist
        GamificationService._ensure_achievements_exist()

        try:
            profile = request.user.annotator_profile
            earned_ids = set(
                AnnotatorAchievement.objects.filter(annotator=profile).values_list(
                    "achievement_id", flat=True
                )
            )
        except AnnotatorProfile.DoesNotExist:
            earned_ids = set()

        achievements = Achievement.objects.filter(is_active=True).order_by(
            "category", "tier"
        )

        result = []
        for achievement in achievements:
            result.append(
                {
                    "id": achievement.id,
                    "code": achievement.code,
                    "name": achievement.name,
                    "description": achievement.description,
                    "category": achievement.category,
                    "tier": achievement.tier,
                    "bonus_amount": float(achievement.bonus_amount),
                    "is_earned": achievement.id in earned_ids,
                }
            )

        return Response(
            {
                "total_achievements": len(result),
                "earned_count": len(earned_ids),
                "achievements": result,
            },
            status=status.HTTP_200_OK,
        )


class PayoutRequestAPI(APIView):
    """Request a payout"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        GET /api/annotators/payouts/

        Returns list of payout requests.
        """
        from .models import PayoutRequest

        try:
            profile = request.user.annotator_profile
        except AnnotatorProfile.DoesNotExist:
            return Response(
                {"error": "No annotator profile found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        payouts = PayoutRequest.objects.filter(annotator=profile).order_by(
            "-requested_at"
        )[:20]

        result = [
            {
                "id": p.id,
                "amount": float(p.amount),
                "status": p.status,
                "payout_method": p.payout_method,
                "requested_at": p.requested_at.isoformat(),
                "processed_at": p.processed_at.isoformat() if p.processed_at else None,
                "transaction_id": p.transaction_id,
                "failure_reason": p.failure_reason,
            }
            for p in payouts
        ]

        return Response(
            {
                "payouts": result,
                "available_balance": float(profile.available_balance),
            },
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        """
        POST /api/annotators/payouts/

        Create a new payout request.

        Request body:
        {
            "amount": 500,
            "payout_method": "bank_transfer"  // or "upi"
        }
        """
        from .payment_service import PayoutService

        try:
            profile = request.user.annotator_profile
        except AnnotatorProfile.DoesNotExist:
            return Response(
                {"error": "No annotator profile found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        amount = request.data.get("amount")
        payout_method = request.data.get("payout_method", "bank_transfer")

        if not amount:
            return Response(
                {"error": "Amount is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            from decimal import Decimal

            amount = Decimal(str(amount))
        except:
            return Response(
                {"error": "Invalid amount"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        result = PayoutService.create_payout_request(
            annotator=profile,
            amount=amount,
            payout_method=payout_method,
        )

        if result.get("success"):
            return Response(result, status=status.HTTP_201_CREATED)
        else:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)


class SkillBadgesAPI(APIView):
    """Get skill badges and progress"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        GET /api/annotators/skill-badges/

        Returns all skill badges with user's progress.
        """
        from .models import SkillBadge, AnnotatorSkillBadge

        try:
            profile = request.user.annotator_profile
            user_badges = {
                sb.skill_badge_id: sb
                for sb in AnnotatorSkillBadge.objects.filter(annotator=profile)
            }
        except AnnotatorProfile.DoesNotExist:
            user_badges = {}

        badges = SkillBadge.objects.filter(is_active=True)

        result = []
        for badge in badges:
            user_badge = user_badges.get(badge.id)
            result.append(
                {
                    "id": badge.id,
                    "code": badge.code,
                    "name": badge.name,
                    "description": badge.description,
                    "annotation_type": badge.annotation_type,
                    "required_tasks": badge.required_tasks,
                    "required_accuracy": float(badge.required_accuracy),
                    "skill_multiplier": float(badge.skill_multiplier),
                    "is_earned": user_badge.is_earned if user_badge else False,
                    "progress": user_badge.tasks_completed if user_badge else 0,
                    "current_accuracy": (
                        float(user_badge.current_accuracy) if user_badge else 0
                    ),
                }
            )

        return Response(
            {
                "badges": result,
                "earned_count": sum(1 for b in result if b["is_earned"]),
            },
            status=status.HTTP_200_OK,
        )


class StreakInfoAPI(APIView):
    """Get streak information"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        GET /api/annotators/streak/

        Returns current streak info.
        """
        from .models import AnnotatorStreak

        try:
            profile = request.user.annotator_profile
        except AnnotatorProfile.DoesNotExist:
            return Response(
                {"error": "No annotator profile found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        streak, created = AnnotatorStreak.objects.get_or_create(annotator=profile)

        return Response(
            {
                "current_streak": streak.current_streak,
                "longest_streak": streak.longest_streak,
                "last_activity_date": (
                    str(streak.last_activity_date)
                    if streak.last_activity_date
                    else None
                ),
                "multiplier": float(streak.get_streak_multiplier()),
                "tasks_this_week": streak.tasks_this_week,
                "tasks_this_month": streak.tasks_this_month,
                "total_streak_bonus": float(streak.total_streak_bonus),
                "next_multiplier_at": (
                    3
                    if streak.current_streak < 3
                    else (
                        7
                        if streak.current_streak < 7
                        else (
                            14
                            if streak.current_streak < 14
                            else 30 if streak.current_streak < 30 else None
                        )
                    )
                ),
            },
            status=status.HTTP_200_OK,
        )


# ============================================================================
# CONSENSUS API ENDPOINTS
# ============================================================================


class TaskConsensusStatusAPI(APIView):
    """Get consensus status for a task including visibility permissions"""

    permission_classes = [IsAuthenticated]

    def get(self, request, task_id):
        """
        GET /api/annotators/consensus/task/<task_id>/

        Returns consensus status for a specific task.
        Also includes visibility permissions based on user role:
        - can_view_annotations: Whether user can see annotations
        - can_view_annotators: Whether user can see annotator info
        """
        from tasks.models import Task
        from .annotation_workflow import AnnotationWorkflowService

        try:
            task = Task.objects.get(id=task_id)
        except Task.DoesNotExist:
            return Response(
                {"error": "Task not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Check permissions - user must be project member or annotator on task
        user = request.user
        project = task.project

        has_access = (
            project.created_by == user
            or project.organization.created_by == user
            or TaskAssignment.objects.filter(task=task, annotator__user=user).exists()
            or getattr(user, "is_expert", False)
        )

        if not has_access:
            return Response(
                {"error": "Access denied"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Get status with visibility info for clients
        consensus_status = AnnotationWorkflowService.get_task_status_for_client(task)

        # Add visible annotations count for the requesting user
        visible_annotations = AnnotationWorkflowService.get_visible_annotations(
            user, task
        )
        consensus_status["visible_annotation_count"] = visible_annotations.count()

        # Add visible annotators if allowed
        if consensus_status.get("can_view_annotators"):
            consensus_status["annotators"] = (
                AnnotationWorkflowService.get_visible_annotators(user, task)
            )

        return Response(consensus_status, status=status.HTTP_200_OK)


class ProjectConsensusOverviewAPI(APIView):
    """Get consensus overview for a project"""

    permission_classes = [IsAuthenticated]

    def get(self, request, project_id):
        """
        GET /api/annotators/consensus/project/<project_id>/

        Returns consensus overview for all tasks in a project.
        """
        from projects.models import Project
        from .models import TaskConsensus
        from django.db.models import Count, Avg

        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            return Response(
                {"error": "Project not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Check permissions
        user = request.user
        if project.created_by != user and project.organization.created_by != user:
            return Response(
                {"error": "Access denied"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Get consensus statistics
        task_ids = project.tasks.values_list("id", flat=True)
        consensus_records = TaskConsensus.objects.filter(task_id__in=task_ids)

        status_counts = consensus_records.values("status").annotate(count=Count("id"))
        status_dict = {s["status"]: s["count"] for s in status_counts}

        avg_agreement = consensus_records.aggregate(avg=Avg("average_agreement"))["avg"]

        # Get tasks needing attention
        needs_review = consensus_records.filter(
            status__in=["conflict", "review_required"]
        ).select_related("task")[:10]

        return Response(
            {
                "project_id": project_id,
                "required_overlap": project.required_overlap,
                "total_tasks": project.tasks.count(),
                "status_breakdown": {
                    "pending": status_dict.get("pending", 0),
                    "in_consensus": status_dict.get("in_consensus", 0),
                    "consensus_reached": status_dict.get("consensus_reached", 0),
                    "conflict": status_dict.get("conflict", 0),
                    "review_required": status_dict.get("review_required", 0),
                    "finalized": status_dict.get("finalized", 0),
                },
                "average_agreement": float(avg_agreement) if avg_agreement else None,
                "needs_review": [
                    {
                        "task_id": c.task_id,
                        "status": c.status,
                        "average_agreement": float(c.average_agreement or 0),
                        "current_annotations": c.current_annotations,
                    }
                    for c in needs_review
                ],
            },
            status=status.HTTP_200_OK,
        )


class FinalizeConsensusAPI(APIView):
    """Finalize consensus after expert review"""

    permission_classes = [IsAuthenticated]

    def post(self, request, task_id):
        """
        POST /api/annotators/consensus/finalize/<task_id>/

        Finalizes consensus and releases review payment.
        Body: { "review_notes": "optional notes" }
        """
        from tasks.models import Task
        from .consensus_service import ConsensusService

        try:
            task = Task.objects.get(id=task_id)
        except Task.DoesNotExist:
            return Response(
                {"error": "Task not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Check permissions - only project owner/org admin can finalize
        user = request.user
        project = task.project

        if project.created_by != user and project.organization.created_by != user:
            return Response(
                {"error": "Only project owner can finalize consensus"},
                status=status.HTTP_403_FORBIDDEN,
            )

        review_notes = request.data.get("review_notes", "")

        result = ConsensusService.finalize_consensus(
            task, reviewed_by=user, review_notes=review_notes
        )

        if "error" in result:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)

        return Response(result, status=status.HTTP_200_OK)


class BulkFinalizeConsensusAPI(APIView):
    """Bulk finalize consensus for multiple tasks"""

    permission_classes = [IsAuthenticated]

    def post(self, request, project_id):
        """
        POST /api/annotators/consensus/bulk-finalize/<project_id>/

        Finalizes consensus for all tasks with consensus_reached status.
        Body: { "task_ids": [optional list], "finalize_all": true/false }
        """
        from projects.models import Project
        from .models import TaskConsensus
        from .consensus_service import ConsensusService

        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            return Response(
                {"error": "Project not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Check permissions
        user = request.user
        if project.created_by != user and project.organization.created_by != user:
            return Response(
                {"error": "Access denied"},
                status=status.HTTP_403_FORBIDDEN,
            )

        task_ids = request.data.get("task_ids")
        finalize_all = request.data.get("finalize_all", False)

        if finalize_all:
            # Get all tasks with consensus_reached
            consensus_records = TaskConsensus.objects.filter(
                task__project=project, status="consensus_reached"
            )
        elif task_ids:
            consensus_records = TaskConsensus.objects.filter(
                task_id__in=task_ids, task__project=project
            )
        else:
            return Response(
                {"error": "Provide task_ids or set finalize_all=true"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        finalized = 0
        errors = []

        for consensus in consensus_records:
            try:
                result = ConsensusService.finalize_consensus(
                    consensus.task, reviewed_by=user, review_notes="Bulk finalized"
                )
                if "error" not in result:
                    finalized += 1
                else:
                    errors.append(
                        {"task_id": consensus.task_id, "error": result["error"]}
                    )
            except Exception as e:
                errors.append({"task_id": consensus.task_id, "error": str(e)})

        return Response(
            {
                "finalized": finalized,
                "errors": errors,
            },
            status=status.HTTP_200_OK,
        )


class AnnotatorQualityStatsAPI(APIView):
    """Get quality statistics for an annotator"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        GET /api/annotators/quality-stats/

        Returns quality statistics for the authenticated annotator.
        """
        from .models import ConsensusQualityScore, AnnotatorAgreement
        from django.db.models import Avg, Count

        try:
            profile = request.user.annotator_profile
        except AnnotatorProfile.DoesNotExist:
            return Response(
                {"error": "Not an annotator account"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Get quality scores
        quality_scores = ConsensusQualityScore.objects.filter(annotator=profile)

        avg_quality = quality_scores.aggregate(avg=Avg("quality_score"))["avg"]
        avg_peer_agreement = quality_scores.aggregate(avg=Avg("avg_peer_agreement"))[
            "avg"
        ]

        # Quality distribution
        quality_distribution = {
            "excellent": quality_scores.filter(quality_score__gte=90).count(),
            "good": quality_scores.filter(
                quality_score__gte=70, quality_score__lt=90
            ).count(),
            "acceptable": quality_scores.filter(
                quality_score__gte=50, quality_score__lt=70
            ).count(),
            "poor": quality_scores.filter(quality_score__lt=50).count(),
        }

        # Recent quality scores
        recent_scores = quality_scores.order_by("-calculated_at")[:10]

        # Agreement stats
        as_first = AnnotatorAgreement.objects.filter(annotator_1=profile)
        as_second = AnnotatorAgreement.objects.filter(annotator_2=profile)

        total_agreements = as_first.count() + as_second.count()
        avg_agreement = None

        if total_agreements > 0:
            sum_first = as_first.aggregate(s=Avg("agreement_score"))["s"] or 0
            sum_second = as_second.aggregate(s=Avg("agreement_score"))["s"] or 0
            avg_agreement = (
                sum_first * as_first.count() + sum_second * as_second.count()
            ) / total_agreements

        return Response(
            {
                "total_consensus_tasks": quality_scores.count(),
                "average_quality_score": float(avg_quality) if avg_quality else None,
                "average_peer_agreement": (
                    float(avg_peer_agreement) if avg_peer_agreement else None
                ),
                "average_agreement_score": (
                    float(avg_agreement) if avg_agreement else None
                ),
                "quality_distribution": quality_distribution,
                "recent_scores": [
                    {
                        "task_id": qs.task_consensus.task_id,
                        "quality_score": float(qs.quality_score),
                        "quality_multiplier": float(qs.quality_multiplier),
                        "peer_agreement": float(qs.avg_peer_agreement or 0),
                        "calculated_at": qs.calculated_at.isoformat(),
                    }
                    for qs in recent_scores
                ],
            },
            status=status.HTTP_200_OK,
        )


class UpdateConsolidatedResultAPI(APIView):
    """Update consolidated result after expert review"""

    permission_classes = [IsAuthenticated]

    def post(self, request, task_id):
        """
        POST /api/annotators/consensus/update-result/<task_id>/

        Updates the consolidated result with expert corrections.
        Body: { "consolidated_result": {...} }
        """
        from tasks.models import Task
        from .models import TaskConsensus

        try:
            task = Task.objects.get(id=task_id)
        except Task.DoesNotExist:
            return Response(
                {"error": "Task not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Check permissions
        user = request.user
        project = task.project

        if project.created_by != user and project.organization.created_by != user:
            return Response(
                {"error": "Only project owner can update consensus result"},
                status=status.HTTP_403_FORBIDDEN,
            )

        consolidated_result = request.data.get("consolidated_result")
        if not consolidated_result:
            return Response(
                {"error": "consolidated_result is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            consensus = TaskConsensus.objects.get(task=task)
            consensus.consolidated_result = consolidated_result
            consensus.reviewed_by = user
            consensus.review_notes = request.data.get(
                "review_notes", "Expert correction"
            )
            consensus.save(
                update_fields=["consolidated_result", "reviewed_by", "review_notes"]
            )

            return Response(
                {
                    "success": True,
                    "task_id": task_id,
                    "message": "Consolidated result updated",
                },
                status=status.HTTP_200_OK,
            )

        except TaskConsensus.DoesNotExist:
            return Response(
                {"error": "No consensus record found for this task"},
                status=status.HTTP_404_NOT_FOUND,
            )


# ============================================================================
# EXPERT API ENDPOINTS
# ============================================================================


class AdminAssignExpertAPI(APIView):
    """Admin API to assign expert role to a user"""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        POST /api/annotators/admin/assign-expert

        Body: {
            "user_id": int,
            "expertise_level": "junior_expert" | "senior_expert" | "lead_expert",
            "expertise_areas": ["classification", "bounding_box", ...]
        }
        """
        from users.models import User
        from .expert_service import ExpertService

        # Check if user is admin/org owner
        if not request.user.is_staff and not request.user.is_superuser:
            # Check if org admin
            from organizations.models import Organization

            is_org_admin = Organization.objects.filter(created_by=request.user).exists()
            if not is_org_admin:
                return Response(
                    {"error": "Only admins can assign expert roles"},
                    status=status.HTTP_403_FORBIDDEN,
                )

        user_id = request.data.get("user_id")
        expertise_level = request.data.get("expertise_level", "junior_expert")
        expertise_areas = request.data.get(
            "expertise_areas", ["classification", "bounding_box", "ner"]
        )

        if not user_id:
            return Response(
                {"error": "user_id is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {"error": "User not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        result = ExpertService.assign_expert_role(
            user=user,
            assigned_by=request.user,
            expertise_level=expertise_level,
            expertise_areas=expertise_areas,
        )

        return Response(result, status=status.HTTP_200_OK)


class AdminRevokeExpertAPI(APIView):
    """Admin API to revoke expert role"""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        POST /api/annotators/admin/revoke-expert

        Body: { "user_id": int }
        """
        from users.models import User
        from .expert_service import ExpertService

        # Check admin permissions
        if not request.user.is_staff and not request.user.is_superuser:
            from organizations.models import Organization

            is_org_admin = Organization.objects.filter(created_by=request.user).exists()
            if not is_org_admin:
                return Response(
                    {"error": "Only admins can revoke expert roles"},
                    status=status.HTTP_403_FORBIDDEN,
                )

        user_id = request.data.get("user_id")
        if not user_id:
            return Response(
                {"error": "user_id is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {"error": "User not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        result = ExpertService.revoke_expert_role(
            user=user,
            revoked_by=request.user,
        )

        if result["success"]:
            return Response(result, status=status.HTTP_200_OK)
        return Response(result, status=status.HTTP_400_BAD_REQUEST)


class AdminAssignExpertToProjectAPI(APIView):
    """Admin API to assign expert to a project"""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        POST /api/annotators/admin/assign-expert-project

        Body: {
            "expert_id": int,
            "project_id": int,
            "review_all_tasks": bool,
            "sample_rate": 100,
            "priority": 0
        }
        """
        from projects.models import Project
        from .models import ExpertProfile
        from .expert_service import ExpertService

        expert_id = request.data.get("expert_id")
        project_id = request.data.get("project_id")

        if not expert_id or not project_id:
            return Response(
                {"error": "expert_id and project_id are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            expert = ExpertProfile.objects.get(id=expert_id)
            project = Project.objects.get(id=project_id)
        except ExpertProfile.DoesNotExist:
            return Response(
                {"error": "Expert not found"}, status=status.HTTP_404_NOT_FOUND
            )
        except Project.DoesNotExist:
            return Response(
                {"error": "Project not found"}, status=status.HTTP_404_NOT_FOUND
            )

        # Check permissions
        user = request.user
        if project.created_by != user and project.organization.created_by != user:
            if not user.is_staff and not user.is_superuser:
                return Response(
                    {"error": "Access denied"},
                    status=status.HTTP_403_FORBIDDEN,
                )

        result = ExpertService.assign_expert_to_project(
            expert=expert,
            project=project,
            assigned_by=request.user,
            review_all_tasks=request.data.get("review_all_tasks", False),
            sample_rate=request.data.get("sample_rate", 100),
            priority=request.data.get("priority", 0),
        )

        return Response(result, status=status.HTTP_200_OK)


class AdminListExpertsAPI(APIView):
    """Admin API to list all experts"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        GET /api/annotators/admin/experts

        Returns list of all experts with their stats.
        """
        from .models import ExpertProfile

        # Check admin permissions
        if not request.user.is_staff and not request.user.is_superuser:
            from organizations.models import Organization

            is_org_admin = Organization.objects.filter(created_by=request.user).exists()
            if not is_org_admin:
                return Response(
                    {"error": "Access denied"},
                    status=status.HTTP_403_FORBIDDEN,
                )

        experts = ExpertProfile.objects.all().select_related("user", "assigned_by")

        return Response(
            {
                "experts": [
                    {
                        "id": e.id,
                        "user_id": e.user_id,
                        "email": e.user.email,
                        "name": e.user.get_full_name(),
                        "status": e.status,
                        "expertise_level": e.expertise_level,
                        "expertise_areas": e.expertise_areas,
                        "total_reviews": e.total_reviews_completed,
                        "approval_rate": float(e.approval_rate),
                        "total_earned": float(e.total_earned),
                        "current_workload": e.current_workload,
                        "is_available": e.is_available,
                        "assigned_at": e.assigned_at.isoformat(),
                        "assigned_by": e.assigned_by.email if e.assigned_by else None,
                    }
                    for e in experts
                ]
            },
            status=status.HTTP_200_OK,
        )


class ExpertDashboardAPI(APIView):
    """Expert dashboard API - shows pending reviews and stats"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        GET /api/annotators/expert/dashboard

        Returns expert dashboard data.
        """
        from .models import ExpertProfile
        from .expert_service import ExpertService

        try:
            expert = request.user.expert_profile
        except ExpertProfile.DoesNotExist:
            return Response(
                {"error": "Not an expert account"},
                status=status.HTTP_403_FORBIDDEN,
            )

        dashboard_data = ExpertService.get_expert_dashboard_data(expert)

        return Response(dashboard_data, status=status.HTTP_200_OK)


class ExpertReviewTaskListAPI(APIView):
    """List review tasks for expert"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        GET /api/annotators/expert/reviews

        Query params:
        - status: pending, in_review, approved, rejected, corrected
        - page: int
        - page_size: int
        """
        from .models import ExpertProfile, ExpertReviewTask

        try:
            expert = request.user.expert_profile
        except ExpertProfile.DoesNotExist:
            return Response(
                {"error": "Not an expert account"},
                status=status.HTTP_403_FORBIDDEN,
            )

        status_filter = request.query_params.get("status")
        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 20))
        offset = (page - 1) * page_size

        queryset = ExpertReviewTask.objects.filter(expert=expert).select_related(
            "task", "task_consensus", "task__project"
        )

        if status_filter:
            queryset = queryset.filter(status=status_filter)

        total = queryset.count()
        reviews = queryset.order_by("-assigned_at")[offset : offset + page_size]

        return Response(
            {
                "total": total,
                "page": page,
                "page_size": page_size,
                "reviews": [
                    {
                        "id": r.id,
                        "task_id": r.task_id,
                        "project_id": r.task.project_id,
                        "project_title": r.task.project.title,
                        "status": r.status,
                        "assignment_reason": r.assignment_reason,
                        "disagreement_score": float(r.disagreement_score or 0),
                        "assigned_at": r.assigned_at.isoformat(),
                        "started_at": (
                            r.started_at.isoformat() if r.started_at else None
                        ),
                        "completed_at": (
                            r.completed_at.isoformat() if r.completed_at else None
                        ),
                        "is_overdue": r.is_overdue,
                        "payment_amount": float(r.payment_amount),
                    }
                    for r in reviews
                ],
            },
            status=status.HTTP_200_OK,
        )


class ExpertProjectsAPI(APIView):
    """
    Expert projects API - simplified project cards for experts.

    Returns minimal, relevant information only:
    - Project ID and title
    - Pending reviews count
    - In-progress count
    - Completed count
    - Estimated earnings
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        GET /api/annotators/expert/projects

        Query params:
        - page: int
        - page_size: int
        - status: pending, in_review, approved, rejected

        Returns simplified project cards for experts.
        """
        from .models import ExpertProfile, ExpertReviewTask
        from projects.models import Project
        from django.db.models import Count, Q, Sum, F
        from decimal import Decimal

        try:
            expert = request.user.expert_profile
        except ExpertProfile.DoesNotExist:
            return Response(
                {"error": "Not an expert account"},
                status=status.HTTP_403_FORBIDDEN,
            )

        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 30))
        status_filter = request.query_params.get("status")
        offset = (page - 1) * page_size

        # Get all review tasks for this expert
        review_tasks_query = ExpertReviewTask.objects.filter(expert=expert)

        if status_filter:
            review_tasks_query = review_tasks_query.filter(status=status_filter)

        # Get unique project IDs from review tasks
        project_ids = review_tasks_query.values_list(
            "task__project_id", flat=True
        ).distinct()

        # Get projects with review task counts
        projects = Project.objects.filter(id__in=project_ids).annotate(
            pending_reviews=Count(
                "tasks__expert_reviews",
                filter=Q(
                    tasks__expert_reviews__expert=expert,
                    tasks__expert_reviews__status="pending",
                ),
            ),
            in_review_count=Count(
                "tasks__expert_reviews",
                filter=Q(
                    tasks__expert_reviews__expert=expert,
                    tasks__expert_reviews__status="in_review",
                ),
            ),
            completed_reviews=Count(
                "tasks__expert_reviews",
                filter=Q(
                    tasks__expert_reviews__expert=expert,
                    tasks__expert_reviews__status__in=[
                        "approved",
                        "rejected",
                        "corrected",
                    ],
                ),
            ),
        )
        
        # Only show projects with pending or in-review tasks
        # unless explicitly filtering for completed (via status_filter)
        if not status_filter or status_filter not in ["approved", "rejected", "corrected"]:
            # Filter to only show projects with active work (pending or in_review)
            projects = projects.filter(
                Q(pending_reviews__gt=0) | Q(in_review_count__gt=0)
            )

        total = projects.count()
        projects_page = projects.order_by("-pending_reviews", "-id")[
            offset : offset + page_size
        ]

        # Calculate estimated earnings per project
        results = []
        for project in projects_page:
            # Get earnings for this project
            project_earnings = ExpertReviewTask.objects.filter(
                expert=expert,
                task__project=project,
                status__in=["approved", "rejected", "corrected"],
            ).aggregate(total_earned=Sum("payment_amount"))["total_earned"] or Decimal(
                "0"
            )

            # Estimate pending earnings (average rate * pending)
            avg_rate = Decimal("50.00")  # Default expert review rate
            pending_earnings = avg_rate * project.pending_reviews

            results.append(
                {
                    "id": project.id,
                    "title": project.title,
                    "pending": project.pending_reviews,
                    "in_progress": project.in_review_count,
                    "completed": project.completed_reviews,
                    "earned": float(project_earnings),
                    "pending_earnings": float(pending_earnings),
                }
            )

        return Response(
            {
                "count": total,
                "next": (
                    f"/api/annotators/expert/projects?page={page + 1}&page_size={page_size}"
                    if offset + page_size < total
                    else None
                ),
                "previous": (
                    f"/api/annotators/expert/projects?page={page - 1}&page_size={page_size}"
                    if page > 1
                    else None
                ),
                "results": results,
            },
            status=status.HTTP_200_OK,
        )


class ExpertReviewTaskDetailAPI(APIView):
    """Get details for a specific review task"""

    permission_classes = [IsAuthenticated]

    def get(self, request, review_id):
        """
        GET /api/annotators/expert/reviews/<review_id>

        Returns detailed review task information.
        """
        from .models import ExpertProfile, ExpertReviewTask
        from .expert_service import ExpertService

        try:
            expert = request.user.expert_profile
        except ExpertProfile.DoesNotExist:
            return Response(
                {"error": "Not an expert account"},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            review_task = ExpertReviewTask.objects.get(id=review_id, expert=expert)
        except ExpertReviewTask.DoesNotExist:
            return Response(
                {"error": "Review task not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        details = ExpertService.get_review_task_details(review_task)

        return Response(details, status=status.HTTP_200_OK)


class ExpertStartReviewAPI(APIView):
    """Start reviewing a task"""

    permission_classes = [IsAuthenticated]

    def post(self, request, review_id):
        """
        POST /api/annotators/expert/reviews/<review_id>/start

        Marks the review as started.
        """
        from .models import ExpertProfile, ExpertReviewTask
        from .expert_service import ExpertService

        try:
            expert = request.user.expert_profile
        except ExpertProfile.DoesNotExist:
            return Response(
                {"error": "Not an expert account"},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            review_task = ExpertReviewTask.objects.get(id=review_id, expert=expert)
        except ExpertReviewTask.DoesNotExist:
            return Response(
                {"error": "Review task not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        result = ExpertService.start_review(review_task)

        if result["success"]:
            return Response(result, status=status.HTTP_200_OK)
        return Response(result, status=status.HTTP_400_BAD_REQUEST)


class ExpertSubmitReviewAPI(APIView):
    """Submit review decision"""

    permission_classes = [IsAuthenticated]

    def post(self, request, review_id):
        """
        POST /api/annotators/expert/reviews/<review_id>/submit

        Body: {
            "action": "approved" | "rejected" | "corrected" | "escalated",
            "review_notes": "...",
            "rejection_reason": "...",  # if rejected
            "corrected_result": {...}   # if corrected
        }
        """
        from .models import ExpertProfile, ExpertReviewTask
        from .expert_service import ExpertService

        try:
            expert = request.user.expert_profile
        except ExpertProfile.DoesNotExist:
            return Response(
                {"error": "Not an expert account"},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            review_task = ExpertReviewTask.objects.get(id=review_id, expert=expert)
        except ExpertReviewTask.DoesNotExist:
            return Response(
                {"error": "Review task not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        action = request.data.get("action")
        if action not in ["approved", "rejected", "corrected", "escalated"]:
            return Response(
                {
                    "error": "Invalid action. Must be: approved, rejected, corrected, escalated"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        result = ExpertService.process_expert_review(
            review_task=review_task,
            action=action,
            reviewer_notes=request.data.get("review_notes", ""),
            corrected_result=request.data.get("corrected_result"),
            rejection_reason=request.data.get("rejection_reason", ""),
        )

        return Response(result, status=status.HTTP_200_OK)


class ExpertEarningsAPI(APIView):
    """Expert earnings summary"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        GET /api/annotators/expert/earnings

        Returns earnings summary for the expert.
        """
        from .models import ExpertProfile, ExpertEarningsTransaction
        from django.db.models import Sum
        from datetime import timedelta

        try:
            expert = request.user.expert_profile
        except ExpertProfile.DoesNotExist:
            return Response(
                {"error": "Not an expert account"},
                status=status.HTTP_403_FORBIDDEN,
            )

        now = timezone.now()
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)

        weekly_earnings = ExpertEarningsTransaction.objects.filter(
            expert=expert, transaction_type="review_payment", created_at__gte=week_ago
        ).aggregate(total=Sum("amount"))["total"] or Decimal("0")

        monthly_earnings = ExpertEarningsTransaction.objects.filter(
            expert=expert, transaction_type="review_payment", created_at__gte=month_ago
        ).aggregate(total=Sum("amount"))["total"] or Decimal("0")

        recent_transactions = ExpertEarningsTransaction.objects.filter(
            expert=expert
        ).order_by("-created_at")[:20]

        # Calculate daily earnings for the last 30 days (for chart)
        daily_earnings = []
        for i in range(30):
            day = now - timedelta(days=29 - i)
            day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day.replace(hour=23, minute=59, second=59, microsecond=999999)
            
            day_total = ExpertEarningsTransaction.objects.filter(
                expert=expert,
                transaction_type="review_payment",
                created_at__gte=day_start,
                created_at__lte=day_end,
            ).aggregate(total=Sum("amount"))["total"] or Decimal("0")
            
            daily_earnings.append({
                "date": day_start.date().isoformat(),
                "amount": float(day_total),
            })

        return Response(
            {
                "total_reviews": expert.total_reviews_completed,
                "total_earned": float(expert.total_earned),
                "pending_payout": float(expert.pending_payout),
                "available_balance": float(expert.available_balance),
                "total_withdrawn": float(expert.total_withdrawn),
                "weekly_earnings": float(weekly_earnings),
                "monthly_earnings": float(monthly_earnings),
                "approval_rate": float(expert.approval_rate),
                "average_review_time": expert.average_review_time,
                "daily_earnings": daily_earnings,
                "recent_transactions": [
                    {
                        "id": t.id,
                        "type": t.transaction_type,
                        "amount": float(t.amount),
                        "balance_after": float(t.balance_after),
                        "description": t.description,
                        "created_at": t.created_at.isoformat(),
                    }
                    for t in recent_transactions
                ],
            },
            status=status.HTTP_200_OK,
        )


class ExpertPayoutRequestAPI(APIView):
    """Expert payout requests"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get payout request history"""
        from .models import ExpertProfile, ExpertPayoutRequest

        try:
            expert = request.user.expert_profile
        except ExpertProfile.DoesNotExist:
            return Response(
                {"error": "Not an expert account"},
                status=status.HTTP_403_FORBIDDEN,
            )

        payouts = ExpertPayoutRequest.objects.filter(expert=expert).order_by(
            "-requested_at"
        )

        return Response(
            {
                "payouts": [
                    {
                        "id": p.id,
                        "amount": float(p.amount),
                        "status": p.status,
                        "payout_method": p.payout_method,
                        "transaction_id": p.transaction_id,
                        "failure_reason": p.failure_reason,
                        "requested_at": p.requested_at.isoformat(),
                        "processed_at": (
                            p.processed_at.isoformat() if p.processed_at else None
                        ),
                    }
                    for p in payouts
                ]
            },
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        """Create payout request"""
        from .models import (
            ExpertProfile,
            ExpertPayoutRequest,
            ExpertEarningsTransaction,
        )
        from .expert_service import ExpertPaymentConfig

        try:
            expert = request.user.expert_profile
        except ExpertProfile.DoesNotExist:
            return Response(
                {"error": "Not an expert account"},
                status=status.HTTP_403_FORBIDDEN,
            )

        amount = Decimal(str(request.data.get("amount", 0)))
        payout_method = request.data.get("payout_method", "bank_transfer")

        # Validate
        if amount < ExpertPaymentConfig.MINIMUM_PAYOUT:
            return Response(
                {"error": f"Minimum payout is ₹{ExpertPaymentConfig.MINIMUM_PAYOUT}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if amount > expert.available_balance:
            return Response(
                {
                    "error": f"Insufficient balance. Available: ₹{expert.available_balance}"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check for pending payouts
        pending = ExpertPayoutRequest.objects.filter(
            expert=expert, status__in=["pending", "processing"]
        ).exists()

        if pending:
            return Response(
                {"error": "You have a pending payout request"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Create payout
        bank_details = {
            "bank_name": expert.bank_name,
            "account_number": expert.account_number,
            "ifsc_code": expert.ifsc_code,
            "account_holder_name": expert.account_holder_name,
            "upi_id": expert.upi_id,
        }

        payout = ExpertPayoutRequest.objects.create(
            expert=expert,
            amount=amount,
            payout_method=payout_method,
            bank_details=bank_details,
        )

        # Deduct from available balance
        expert.available_balance -= amount
        expert.save(update_fields=["available_balance"])

        # Record transaction
        ExpertEarningsTransaction.objects.create(
            expert=expert,
            transaction_type="withdrawal",
            amount=-amount,
            balance_after=expert.available_balance,
            description=f"Payout request #{payout.id}",
        )

        return Response(
            {
                "success": True,
                "payout_id": payout.id,
                "amount": float(amount),
                "status": payout.status,
            },
            status=status.HTTP_201_CREATED,
        )


class ExpertBankDetailsAPI(APIView):
    """Manage expert bank details"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get bank details"""
        from .models import ExpertProfile

        try:
            expert = request.user.expert_profile
        except ExpertProfile.DoesNotExist:
            return Response(
                {"error": "Not an expert account"},
                status=status.HTTP_403_FORBIDDEN,
            )

        account_number = expert.account_number
        masked_account = (
            f"****{account_number[-4:]}"
            if account_number and len(account_number) > 4
            else ""
        )

        return Response(
            {
                "bank_name": expert.bank_name,
                "account_number": masked_account,
                "ifsc_code": expert.ifsc_code,
                "account_holder_name": expert.account_holder_name,
                "upi_id": expert.upi_id,
                "has_bank_details": bool(expert.bank_name and expert.account_number),
                "has_upi": bool(expert.upi_id),
            },
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        """Update bank details"""
        from .models import ExpertProfile

        try:
            expert = request.user.expert_profile
        except ExpertProfile.DoesNotExist:
            return Response(
                {"error": "Not an expert account"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Update fields
        if "bank_name" in request.data:
            expert.bank_name = request.data["bank_name"]
        if "account_number" in request.data:
            expert.account_number = request.data["account_number"]
        if "ifsc_code" in request.data:
            expert.ifsc_code = request.data["ifsc_code"]
        if "account_holder_name" in request.data:
            expert.account_holder_name = request.data["account_holder_name"]
        if "upi_id" in request.data:
            expert.upi_id = request.data["upi_id"]

        expert.save()

        return Response(
            {"success": True, "message": "Bank details updated"},
            status=status.HTTP_200_OK,
        )


class AdminExpertProjectAssignmentAPI(APIView):
    """
    Admin API to assign experts to projects.
    Only accessible by superusers or organization admins.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """List all expert-project assignments"""
        from .models import ExpertProjectAssignment, ExpertProfile

        # Check if user is admin/superuser
        if not request.user.is_superuser:
            return Response(
                {"error": "Admin access required"},
                status=status.HTTP_403_FORBIDDEN,
            )

        assignments = ExpertProjectAssignment.objects.select_related(
            "expert__user", "project"
        ).all()

        return Response(
            {
                "assignments": [
                    {
                        "id": a.id,
                        "expert_id": a.expert.id,
                        "expert_email": a.expert.user.email,
                        "expert_name": a.expert.user.get_full_name(),
                        "project_id": a.project.id,
                        "project_title": a.project.title,
                        "is_active": a.is_active,
                        "review_all_tasks": a.review_all_tasks,
                        "tasks_reviewed": a.tasks_reviewed,
                        "assigned_at": a.assigned_at.isoformat(),
                    }
                    for a in assignments
                ]
            }
        )

    def post(self, request):
        """Assign an expert to a project"""
        from .models import ExpertProjectAssignment, ExpertProfile
        from projects.models import Project

        # Check if user is admin/superuser
        if not request.user.is_superuser:
            return Response(
                {"error": "Admin access required"},
                status=status.HTTP_403_FORBIDDEN,
            )

        expert_id = request.data.get("expert_id")
        project_id = request.data.get("project_id")

        if not expert_id or not project_id:
            return Response(
                {"error": "expert_id and project_id are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            expert = ExpertProfile.objects.get(id=expert_id)
        except ExpertProfile.DoesNotExist:
            return Response(
                {"error": "Expert not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            return Response(
                {"error": "Project not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Create or update assignment
        assignment, created = ExpertProjectAssignment.objects.get_or_create(
            expert=expert,
            project=project,
            defaults={
                "is_active": True,
                "review_all_tasks": request.data.get("review_all_tasks", False),
                "assigned_by": request.user,
            },
        )

        if not created:
            assignment.is_active = True
            assignment.save(update_fields=["is_active"])

        return Response(
            {
                "success": True,
                "message": f"Expert {expert.user.email} assigned to project {project.title}",
                "assignment_id": assignment.id,
                "created": created,
            },
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

    def delete(self, request):
        """Remove an expert from a project"""
        from .models import ExpertProjectAssignment

        # Check if user is admin/superuser
        if not request.user.is_superuser:
            return Response(
                {"error": "Admin access required"},
                status=status.HTTP_403_FORBIDDEN,
            )

        assignment_id = request.data.get("assignment_id")

        if not assignment_id:
            return Response(
                {"error": "assignment_id is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            assignment = ExpertProjectAssignment.objects.get(id=assignment_id)
            assignment.is_active = False
            assignment.save(update_fields=["is_active"])
            return Response(
                {"success": True, "message": "Assignment deactivated"},
                status=status.HTTP_200_OK,
            )
        except ExpertProjectAssignment.DoesNotExist:
            return Response(
                {"error": "Assignment not found"},
                status=status.HTTP_404_NOT_FOUND,
            )


class AdminListExpertsAPI(APIView):
    """
    Admin API to list all experts.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """List all experts"""
        from .models import ExpertProfile

        # Check if user is admin/superuser
        if not request.user.is_superuser:
            return Response(
                {"error": "Admin access required"},
                status=status.HTTP_403_FORBIDDEN,
            )

        experts = ExpertProfile.objects.select_related("user").all()

        return Response(
            {
                "experts": [
                    {
                        "id": e.id,
                        "user_id": e.user.id,
                        "email": e.user.email,
                        "name": e.user.get_full_name(),
                        "status": e.status,
                        "expertise_level": e.expertise_level,
                        "expertise_areas": e.expertise_areas,
                        "total_reviews_completed": e.total_reviews_completed,
                        "is_available": e.is_available,
                    }
                    for e in experts
                ]
            }
        )


# ==============================================================================
# EXPERT REVIEW ACCEPT/REJECT APIs
# ==============================================================================


class ExpertReviewActionAPI(APIView):
    """
    Accept or reject a consolidated annotation (expert review action)
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, task_id):
        """
        POST /api/annotators/expert/review/<task_id>/action

        Body:
        {
            "action": "accept" | "reject",
            "review_notes": "optional notes",
            "rejection_reason": "low_quality" | "disagreement" | "incorrect_labels" | "incomplete" | "ambiguous" | "other" (required for reject),
            "require_reannotation": true | false (default true, only for reject),
            "corrected_result": {...} (optional, for accept with corrections)
        }
        """
        from tasks.models import Task
        from .expert_service import ExpertService

        # Verify user is an expert
        try:
            expert_profile = request.user.expert_profile
        except AttributeError:
            return Response(
                {"error": "Only experts can perform review actions"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Get task
        try:
            task = Task.objects.get(id=task_id)
        except Task.DoesNotExist:
            return Response(
                {"error": "Task not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Parse request data
        action = request.data.get("action")
        review_notes = request.data.get("review_notes", "")

        if action not in ["accept", "reject"]:
            return Response(
                {"error": "Invalid action. Must be 'accept' or 'reject'"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Handle ACCEPT
        if action == "accept":
            corrected_result = request.data.get("corrected_result")

            result = ExpertService.accept_consolidated_annotation(
                task=task,
                expert_user=request.user,
                review_notes=review_notes,
                corrected_result=corrected_result,
            )

            if result.get("success"):
                return Response(result, status=status.HTTP_200_OK)
            else:
                return Response(result, status=status.HTTP_400_BAD_REQUEST)

        # Handle REJECT
        elif action == "reject":
            rejection_reason = request.data.get("rejection_reason")
            require_reannotation = request.data.get("require_reannotation", True)

            if not rejection_reason:
                return Response(
                    {"error": "rejection_reason is required for reject action"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            valid_reasons = [
                "low_quality",
                "disagreement",
                "incorrect_labels",
                "incomplete",
                "ambiguous",
                "other",
            ]
            if rejection_reason not in valid_reasons:
                return Response(
                    {
                        "error": f"Invalid rejection_reason. Must be one of: {', '.join(valid_reasons)}"
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            result = ExpertService.reject_consolidated_annotation(
                task=task,
                expert_user=request.user,
                rejection_reason=rejection_reason,
                review_notes=review_notes,
                notify_annotators=True,
                require_reannotation=require_reannotation,
            )

            if result.get("success"):
                return Response(result, status=status.HTTP_200_OK)
            else:
                return Response(result, status=status.HTTP_400_BAD_REQUEST)


class ExpertReviewTaskDetailAPI(APIView):
    """
    Get detailed information for expert to review a task
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, task_id):
        """
        GET /api/annotators/expert/review/<task_id>/details

        Returns:
        - Task data
        - All individual annotations
        - Consolidated result
        - Agreement metrics
        - Review status
        """
        from tasks.models import Task
        from .expert_service import ExpertService

        # Verify user is an expert
        try:
            expert_profile = request.user.expert_profile
        except AttributeError:
            return Response(
                {"error": "Only experts can access review details"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Get task
        try:
            task = Task.objects.get(id=task_id)
        except Task.DoesNotExist:
            return Response(
                {"error": "Task not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Get review details
        result = ExpertService.get_review_task_details(task, request.user)

        if result.get("success"):
            return Response(result, status=status.HTTP_200_OK)
        else:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)


class ExpertPendingReviewsAPI(APIView):
    """
    Get list of tasks pending expert review.
    Only returns tasks that are explicitly assigned to this expert via ExpertReviewTask.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        GET /api/annotators/expert/pending-reviews

        Query params:
        - project_id: Filter by project (optional)
        - page: Page number (default 1)
        - page_size: Items per page (default 20)

        Returns only tasks assigned to this expert via ExpertReviewTask model.
        """
        from .models import ExpertProfile, ExpertReviewTask

        # Verify user is an expert
        try:
            expert_profile = request.user.expert_profile
        except AttributeError:
            return Response(
                {"error": "Only experts can access pending reviews"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Parse query params
        project_id = request.query_params.get("project_id")
        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 20))
        offset = (page - 1) * page_size

        # Get tasks assigned to THIS expert via ExpertReviewTask
        # Only show pending and in_review tasks (not already completed ones)
        queryset = ExpertReviewTask.objects.filter(
            expert=expert_profile, status__in=["pending", "in_review"]
        ).select_related("task", "task__project", "task_consensus")

        if project_id:
            queryset = queryset.filter(task__project_id=project_id)

        total = queryset.count()
        reviews = queryset.order_by("-assigned_at")[offset : offset + page_size]

        # Get project title for the response (if filtering by project_id)
        project_title = None
        if project_id and reviews:
            project_title = reviews[0].task.project.title

        return Response(
            {
                "count": total,  # Frontend expects 'count'
                "total": total,
                "page": page,
                "page_size": page_size,
                "project_title": project_title,
                "tasks": [  # Frontend expects 'tasks' array
                    {
                        "id": r.id,  # ExpertReviewTask ID
                        "task_id": r.task_id,
                        "project_id": r.task.project_id,
                        "project_title": r.task.project.title,
                        "status": r.status,
                        "assignment_reason": r.assignment_reason or "review_required",
                        "disagreement_score": float(r.disagreement_score or 0),
                        "assigned_at": r.assigned_at.isoformat(),
                        "is_overdue": r.is_overdue,
                        # Additional fields for detailed view
                        "consensus_id": r.task_consensus_id,
                        "average_agreement": (
                            float(r.task_consensus.average_agreement or 0)
                            if r.task_consensus
                            else 0
                        ),
                        "current_annotations": (
                            r.task_consensus.current_annotations
                            if r.task_consensus
                            else 0
                        ),
                        "required_annotations": (
                            r.task_consensus.required_annotations
                            if r.task_consensus
                            else 0
                        ),
                        "consolidation_method": (
                            r.task_consensus.consolidation_method
                            if r.task_consensus
                            else None
                        ),
                    }
                    for r in reviews
                ],
                # Also keep 'reviews' for backward compatibility with any other consumers
                "reviews": [
                    {
                        "id": r.id,
                        "task_id": r.task_id,
                        "project_id": r.task.project_id,
                        "project_title": r.task.project.title,
                        "status": r.status,
                        "assignment_reason": r.assignment_reason or "review_required",
                        "disagreement_score": float(r.disagreement_score or 0),
                        "assigned_at": r.assigned_at.isoformat(),
                        "is_overdue": r.is_overdue,
                    }
                    for r in reviews
                ],
            },
            status=status.HTTP_200_OK,
        )


# ============================================================================
# EXPERT TASK ASSIGNMENT APIs
# ============================================================================


class ExpertTaskQueueAPI(APIView):
    """
    Get expert's task queue - simplified view for expert project cards.
    Only shows relevant info: task count, disagreement level, priority.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        GET /api/annotators/expert/task-queue

        Returns the expert's pending task queue with simplified project info.
        """
        from .models import ExpertProfile
        from .expert_assignment_service import ExpertTaskAssignmentService

        try:
            expert = request.user.expert_profile
        except ExpertProfile.DoesNotExist:
            return Response(
                {"error": "Not an expert account"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Get task queue
        task_queue = ExpertTaskAssignmentService.get_expert_task_queue(expert)

        # Group by project for simplified view
        projects = {}
        for task in task_queue:
            project_id = task["project_id"]
            if project_id not in projects:
                projects[project_id] = {
                    "project_id": project_id,
                    "project_title": task["project_title"],
                    "pending_count": 0,
                    "critical_count": 0,
                    "high_priority_count": 0,
                    "avg_disagreement": 0,
                    "tasks": [],
                }

            projects[project_id]["pending_count"] += 1
            projects[project_id]["avg_disagreement"] += task["disagreement_score"]

            if task["priority"] == "critical":
                projects[project_id]["critical_count"] += 1
            elif task["priority"] == "high":
                projects[project_id]["high_priority_count"] += 1

            projects[project_id]["tasks"].append(task)

        # Calculate averages
        for project in projects.values():
            if project["pending_count"] > 0:
                project["avg_disagreement"] = round(
                    project["avg_disagreement"] / project["pending_count"], 1
                )

        return Response(
            {
                "total_pending": len(task_queue),
                "projects": list(projects.values()),
                "task_queue": task_queue[:20],  # First 20 tasks
            }
        )


class ExpertPendingTasksAPI(APIView):
    """
    Get tasks pending expert assignment (admin/lead view).
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        GET /api/annotators/expert/pending-tasks?project_id=1

        Returns tasks that need expert review but haven't been assigned.
        """
        from .models import ExpertProfile
        from .expert_assignment_service import ExpertTaskAssignmentService
        from projects.models import Project

        # Verify user is an expert or admin
        if not (request.user.is_staff or hasattr(request.user, "expert_profile")):
            return Response(
                {"error": "Access denied"},
                status=status.HTTP_403_FORBIDDEN,
            )

        project_id = request.query_params.get("project_id")
        project = None
        if project_id:
            try:
                project = Project.objects.get(id=project_id)
            except Project.DoesNotExist:
                return Response(
                    {"error": "Project not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )

        pending_tasks = ExpertTaskAssignmentService.get_pending_tasks_for_assignment(
            project=project, limit=100
        )

        return Response(
            {
                "count": len(pending_tasks),
                "tasks": pending_tasks,
            }
        )


class ExpertAvailableExpertsAPI(APIView):
    """
    Get available experts for task assignment (admin view).
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        GET /api/annotators/expert/available-experts?project_id=1

        Returns experts available for assignment.
        """
        from .expert_assignment_service import ExpertTaskAssignmentService
        from projects.models import Project

        # Only admins can view all experts
        if not request.user.is_staff:
            return Response(
                {"error": "Admin access required"},
                status=status.HTTP_403_FORBIDDEN,
            )

        project_id = request.query_params.get("project_id")
        project = None
        if project_id:
            try:
                project = Project.objects.get(id=project_id)
            except Project.DoesNotExist:
                return Response(
                    {"error": "Project not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )

        available = ExpertTaskAssignmentService.get_available_experts(project=project)

        return Response(
            {
                "count": len(available),
                "experts": available,
            }
        )


class ExpertAssignTaskAPI(APIView):
    """
    Manually assign a task to an expert.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        POST /api/annotators/expert/assign-task

        Body:
        {
            "consensus_id": 123,
            "expert_id": 456  // optional, auto-select if not provided
        }
        """
        from .models import ExpertProfile, TaskConsensus
        from .expert_assignment_service import ExpertTaskAssignmentService

        # Only admins can manually assign
        if not request.user.is_staff:
            return Response(
                {"error": "Admin access required"},
                status=status.HTTP_403_FORBIDDEN,
            )

        consensus_id = request.data.get("consensus_id")
        expert_id = request.data.get("expert_id")

        if not consensus_id:
            return Response(
                {"error": "consensus_id is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            consensus = TaskConsensus.objects.get(id=consensus_id)
        except TaskConsensus.DoesNotExist:
            return Response(
                {"error": "Consensus not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        expert = None
        if expert_id:
            try:
                expert = ExpertProfile.objects.get(id=expert_id)
            except ExpertProfile.DoesNotExist:
                return Response(
                    {"error": "Expert not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )

        result = ExpertTaskAssignmentService.assign_task_to_expert(
            task_consensus=consensus,
            expert=expert,
            assignment_reason="manual_assignment",
            manual=True,
        )

        if result["success"]:
            return Response(result, status=status.HTTP_201_CREATED)
        else:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)


class ExpertBatchAssignAPI(APIView):
    """
    Batch assign pending tasks to available experts.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        POST /api/annotators/expert/batch-assign

        Body:
        {
            "project_id": 123,  // optional
            "max_assignments": 50  // optional, default 50
        }
        """
        from .expert_assignment_service import ExpertTaskAssignmentService
        from projects.models import Project

        # Only admins can trigger batch assignment
        if not request.user.is_staff:
            return Response(
                {"error": "Admin access required"},
                status=status.HTTP_403_FORBIDDEN,
            )

        project_id = request.data.get("project_id")
        max_assignments = int(request.data.get("max_assignments", 50))

        project = None
        if project_id:
            try:
                project = Project.objects.get(id=project_id)
            except Project.DoesNotExist:
                return Response(
                    {"error": "Project not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )

        result = ExpertTaskAssignmentService.batch_assign_pending_tasks(
            project=project,
            max_assignments=max_assignments,
        )

        return Response(result)


class ExpertAssignmentStatsAPI(APIView):
    """
    Get statistics about expert task assignments.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        GET /api/annotators/expert/assignment-stats?project_id=1

        Returns assignment statistics.
        """
        from .expert_assignment_service import ExpertTaskAssignmentService
        from projects.models import Project

        # Verify user is an expert or admin
        if not (request.user.is_staff or hasattr(request.user, "expert_profile")):
            return Response(
                {"error": "Access denied"},
                status=status.HTTP_403_FORBIDDEN,
            )

        project_id = request.query_params.get("project_id")
        project = None
        if project_id:
            try:
                project = Project.objects.get(id=project_id)
            except Project.DoesNotExist:
                return Response(
                    {"error": "Project not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )

        stats = ExpertTaskAssignmentService.get_assignment_stats(project=project)

        return Response(stats)


# ============================================================================
# EXPERT PAYMENT APIs
# ============================================================================


class ExpertPaymentDashboardAPI(APIView):
    """Get expert payment dashboard with balance, earnings, and payout info"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        GET /api/annotators/expert/payment/dashboard

        Returns payment overview for the expert user
        """
        from .models import ExpertProfile

        # Verify user is an expert
        try:
            expert = request.user.expert_profile
        except AttributeError:
            return Response(
                {"error": "Only experts can access payment dashboard"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Check if can request payout
        can_request_payout = (
            expert.pending_payout >= expert.minimum_payout
            and not expert.payout_requests.filter(status="pending").exists()
        )

        # Get last payout info
        last_payout = (
            expert.payout_requests.filter(status="completed")
            .order_by("-processed_at")
            .first()
        )

        # Calculate this month earnings
        from django.utils import timezone
        from datetime import datetime

        now = timezone.now()
        month_start = datetime(now.year, now.month, 1, tzinfo=now.tzinfo)

        month_earnings = expert.earnings_transactions.filter(
            created_at__gte=month_start, transaction_type__in=["review_payment"]
        ).aggregate(total=models.Sum("amount"))["total"] or Decimal("0")

        # Bank details configured
        bank_details_configured = bool(
            expert.bank_details
            or (expert.payment_method == "upi" and expert.upi_id)
            or (
                expert.payment_method == "bank_transfer"
                and expert.account_number
                and expert.ifsc_code
            )
        )

        return Response(
            {
                "pending_payout": float(expert.pending_payout),
                "total_earned": float(expert.total_earned),
                "total_payouts": expert.total_payouts_count,
                "total_withdrawn": float(expert.total_withdrawn),
                "last_payout_date": (
                    last_payout.processed_at.isoformat() if last_payout else None
                ),
                "last_payout_amount": (float(last_payout.amount) if last_payout else 0),
                "this_month_earnings": float(month_earnings),
                "can_request_payout": can_request_payout,
                "minimum_payout": float(expert.minimum_payout),
                "payment_method": expert.payment_method,
                "bank_details_configured": bank_details_configured,
                "average_review_time": expert.average_review_time,
                "custom_rates": {
                    "base_rate": (
                        float(expert.custom_base_rate)
                        if expert.custom_base_rate
                        else None
                    ),
                    "level_multiplier": (
                        float(expert.custom_level_multiplier)
                        if expert.custom_level_multiplier
                        else None
                    ),
                },
            },
            status=status.HTTP_200_OK,
        )


class ExpertTransactionHistoryAPI(APIView):
    """Get expert transaction history with pagination"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        GET /api/annotators/expert/payment/transactions?page=1&page_size=20&type=review_payment

        Returns paginated transaction history
        """
        from .models import ExpertProfile, ExpertEarningsTransaction

        # Verify user is an expert
        try:
            expert = request.user.expert_profile
        except AttributeError:
            return Response(
                {"error": "Only experts can access transaction history"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Get query parameters
        page = int(request.GET.get("page", 1))
        page_size = int(request.GET.get("page_size", 20))
        transaction_type = request.GET.get("type")

        # Build query
        transactions = expert.earnings_transactions.all()

        if transaction_type:
            transactions = transactions.filter(transaction_type=transaction_type)

        # Paginate
        from django.core.paginator import Paginator

        paginator = Paginator(transactions, page_size)
        page_obj = paginator.get_page(page)

        return Response(
            {
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "current_page": page,
                "page_size": page_size,
                "results": [
                    {
                        "id": t.id,
                        "type": t.transaction_type,
                        "amount": float(t.amount),
                        "balance_after": float(t.balance_after),
                        "description": t.description,
                        "created_at": t.created_at.isoformat(),
                        "review_task_id": t.review_task_id,
                        "task_id": (t.review_task.task_id if t.review_task else None),
                        "metadata": t.metadata,
                    }
                    for t in page_obj
                ],
            },
            status=status.HTTP_200_OK,
        )


class ExpertRequestPayoutAPI(APIView):
    """Request payout from pending balance"""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        POST /api/annotators/expert/payment/request-payout

        Body:
        {
            "amount": 1000.00,
            "payout_method": "bank_transfer" | "upi"  # optional, uses profile default
        }
        """
        from .models import ExpertProfile, ExpertPayoutRequest
        from django.db import transaction

        # Verify user is an expert
        try:
            expert = request.user.expert_profile
        except AttributeError:
            return Response(
                {"error": "Only experts can request payouts"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Parse request
        amount = request.data.get("amount")
        payout_method = request.data.get("payout_method", expert.payment_method)

        # Validate amount
        if not amount:
            return Response(
                {"error": "Amount is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            amount = Decimal(str(amount))
        except (ValueError, TypeError):
            return Response(
                {"error": "Invalid amount"}, status=status.HTTP_400_BAD_REQUEST
            )

        if amount <= 0:
            return Response(
                {"error": "Amount must be greater than 0"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if amount > expert.pending_payout:
            return Response(
                {"error": f"Insufficient balance. Available: ₹{expert.pending_payout}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if amount < expert.minimum_payout:
            return Response(
                {
                    "error": f"Amount must be at least ₹{expert.minimum_payout} (minimum payout threshold)"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check for existing pending request
        if expert.payout_requests.filter(status="pending").exists():
            return Response(
                {"error": "You already have a pending payout request"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validate payment details
        if payout_method == "bank_transfer":
            if not expert.bank_details and not (
                expert.account_number and expert.ifsc_code
            ):
                return Response(
                    {
                        "error": "Bank details not configured. Please update your payment details first."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
        elif payout_method == "upi":
            if not expert.upi_id:
                return Response(
                    {
                        "error": "UPI ID not configured. Please update your payment details first."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # Create payout request
        with transaction.atomic():
            # Snapshot bank details
            if payout_method == "bank_transfer":
                bank_details_snapshot = expert.bank_details or {
                    "account_holder": expert.account_holder_name,
                    "account_number": expert.account_number,
                    "ifsc_code": expert.ifsc_code,
                    "bank_name": expert.bank_name,
                }
            else:  # UPI
                bank_details_snapshot = {"upi_id": expert.upi_id}

            payout_request = ExpertPayoutRequest.objects.create(
                expert=expert,
                amount=amount,
                payout_method=payout_method,
                bank_details=bank_details_snapshot,
            )

            # TODO: Send notification to admin
            # TODO: Send confirmation email to expert

        return Response(
            {
                "success": True,
                "payout_request_id": payout_request.id,
                "amount": float(amount),
                "status": payout_request.status,
                "message": f"Payout request of ₹{amount} submitted successfully. Processing within 3-5 business days.",
            },
            status=status.HTTP_201_CREATED,
        )


class ExpertPayoutRequestsAPI(APIView):
    """Get list of expert's payout requests"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        GET /api/annotators/expert/payment/payout-requests?status=pending&page=1

        Returns paginated payout requests
        """
        from .models import ExpertProfile

        # Verify user is an expert
        try:
            expert = request.user.expert_profile
        except AttributeError:
            return Response(
                {"error": "Only experts can access payout requests"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Get query parameters
        request_status = request.GET.get("status")
        page = int(request.GET.get("page", 1))
        page_size = int(request.GET.get("page_size", 20))

        # Build query
        payout_requests = expert.payout_requests.all()

        if request_status:
            payout_requests = payout_requests.filter(status=request_status)

        # Paginate
        from django.core.paginator import Paginator

        paginator = Paginator(payout_requests, page_size)
        page_obj = paginator.get_page(page)

        return Response(
            {
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "current_page": page,
                "results": [
                    {
                        "id": p.id,
                        "amount": float(p.amount),
                        "status": p.status,
                        "payout_method": p.payout_method,
                        "requested_at": p.requested_at.isoformat(),
                        "processed_at": (
                            p.processed_at.isoformat() if p.processed_at else None
                        ),
                        "transaction_id": p.transaction_id,
                        "failure_reason": p.failure_reason,
                    }
                    for p in page_obj
                ],
            },
            status=status.HTTP_200_OK,
        )


class ExpertUpdatePaymentDetailsAPI(APIView):
    """Update expert payment details"""

    permission_classes = [IsAuthenticated]

    def put(self, request):
        """
        PUT /api/annotators/expert/payment/update-details

        Body:
        {
            "payment_method": "bank_transfer" | "upi",
            "bank_details": {
                "account_holder": "John Doe",
                "account_number": "123456789",
                "ifsc_code": "HDFC0001234",
                "bank_name": "HDFC Bank"
            },
            "upi_id": "johndoe@paytm"
        }
        """
        from .models import ExpertProfile

        # Verify user is an expert
        try:
            expert = request.user.expert_profile
        except AttributeError:
            return Response(
                {"error": "Only experts can update payment details"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Parse request
        payment_method = request.data.get("payment_method")
        bank_details = request.data.get("bank_details")
        upi_id = request.data.get("upi_id")

        # Validate payment method
        if payment_method and payment_method not in dict(
            ExpertProfile.PAYMENT_METHOD_CHOICES
        ):
            return Response(
                {"error": "Invalid payment method"}, status=status.HTTP_400_BAD_REQUEST
            )

        # Update fields
        if payment_method:
            expert.payment_method = payment_method

        if bank_details:
            # Validate bank details
            required_fields = [
                "account_holder",
                "account_number",
                "ifsc_code",
                "bank_name",
            ]
            if not all(bank_details.get(f) for f in required_fields):
                return Response(
                    {"error": "All bank details fields are required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            expert.bank_details = bank_details
            # Also update individual fields for backward compatibility
            expert.account_holder_name = bank_details.get("account_holder")
            expert.account_number = bank_details.get("account_number")
            expert.ifsc_code = bank_details.get("ifsc_code")
            expert.bank_name = bank_details.get("bank_name")

        if upi_id:
            expert.upi_id = upi_id

        expert.save()

        return Response(
            {
                "success": True,
                "message": "Payment details updated successfully",
                "payment_method": expert.payment_method,
                "bank_details_configured": bool(expert.bank_details),
                "upi_configured": bool(expert.upi_id),
            },
            status=status.HTTP_200_OK,
        )


# ============================================================================
# ADMIN PAYMENT APIs
# ============================================================================


class AdminPendingPayoutsAPI(APIView):
    """Get pending payout requests for admin approval"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        GET /api/annotators/admin/expert-payouts/pending?page=1&page_size=20

        Returns paginated list of pending payout requests (admin only)
        """
        from .models import ExpertPayoutRequest

        # Check if user is staff
        if not request.user.is_staff:
            return Response(
                {"error": "Only admins can access this endpoint"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Get query parameters
        page = int(request.GET.get("page", 1))
        page_size = int(request.GET.get("page_size", 20))

        # Get pending requests
        payout_requests = ExpertPayoutRequest.objects.filter(
            status="pending"
        ).select_related("expert__user")

        # Calculate total amount
        total_amount = payout_requests.aggregate(total=models.Sum("amount"))[
            "total"
        ] or Decimal("0")

        # Paginate
        from django.core.paginator import Paginator

        paginator = Paginator(payout_requests, page_size)
        page_obj = paginator.get_page(page)

        return Response(
            {
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "current_page": page,
                "total_amount": float(total_amount),
                "results": [
                    {
                        "id": p.id,
                        "expert": {
                            "id": p.expert.id,
                            "name": p.expert.user.get_full_name()
                            or p.expert.user.email,
                            "email": p.expert.user.email,
                            "expertise_level": p.expert.expertise_level,
                            "total_earned": float(p.expert.total_earned),
                            "total_withdrawn": float(p.expert.total_withdrawn),
                        },
                        "amount": float(p.amount),
                        "payout_method": p.payout_method,
                        "bank_details": p.bank_details,
                        "requested_at": p.requested_at.isoformat(),
                    }
                    for p in page_obj
                ],
            },
            status=status.HTTP_200_OK,
        )


class AdminProcessPayoutAPI(APIView):
    """Process (approve/reject) a payout request"""

    permission_classes = [IsAuthenticated]

    def post(self, request, payout_id):
        """
        POST /api/annotators/admin/expert-payouts/<payout_id>/process

        Body:
        {
            "action": "approve" | "reject",
            "transaction_id": "TXN123456",  # Required for approve
            "failure_reason": "reason text"  # Required for reject
        }
        """
        from .models import ExpertPayoutRequest, ExpertEarningsTransaction
        from django.db import transaction as db_transaction
        from django.utils import timezone

        # Check if user is staff
        if not request.user.is_staff:
            return Response(
                {"error": "Only admins can process payouts"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Get payout request
        try:
            payout_request = ExpertPayoutRequest.objects.select_related("expert").get(
                id=payout_id
            )
        except ExpertPayoutRequest.DoesNotExist:
            return Response(
                {"error": "Payout request not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Check if already processed
        if payout_request.status != "pending":
            return Response(
                {"error": f"Payout request is already {payout_request.status}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Parse request
        action = request.data.get("action")
        transaction_id = request.data.get("transaction_id")
        failure_reason = request.data.get("failure_reason")

        if action not in ["approve", "reject"]:
            return Response(
                {"error": "Invalid action. Must be 'approve' or 'reject'"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if action == "approve" and not transaction_id:
            return Response(
                {"error": "transaction_id is required for approval"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if action == "reject" and not failure_reason:
            return Response(
                {"error": "failure_reason is required for rejection"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Process payout
        with db_transaction.atomic():
            if action == "approve":
                # Update payout request
                payout_request.status = "completed"
                payout_request.transaction_id = transaction_id
                payout_request.processed_at = timezone.now()
                payout_request.processed_by = request.user
                payout_request.save()

                # Update expert balances
                expert = payout_request.expert
                expert.pending_payout = Decimal(str(expert.pending_payout)) - Decimal(
                    str(payout_request.amount)
                )
                expert.total_withdrawn = Decimal(str(expert.total_withdrawn)) + Decimal(
                    str(payout_request.amount)
                )
                expert.total_payouts_count += 1
                expert.total_payouts_amount = Decimal(
                    str(expert.total_payouts_amount)
                ) + Decimal(str(payout_request.amount))
                expert.last_payout_at = timezone.now()
                expert.save()

                # Create withdrawal transaction
                ExpertEarningsTransaction.objects.create(
                    expert=expert,
                    transaction_type="withdrawal",
                    amount=-payout_request.amount,  # Negative for withdrawal
                    balance_after=expert.pending_payout,
                    description=f"Payout processed: ₹{payout_request.amount} via {payout_request.payout_method}",
                    metadata={
                        "payout_request_id": payout_request.id,
                        "transaction_id": transaction_id,
                        "processed_by": request.user.email,
                    },
                )

                # TODO: Send confirmation email to expert

                return Response(
                    {
                        "success": True,
                        "message": f"Payout of ₹{payout_request.amount} approved successfully",
                        "transaction_id": transaction_id,
                        "expert_new_balance": float(expert.pending_payout),
                    },
                    status=status.HTTP_200_OK,
                )

            else:  # reject
                # Update payout request
                payout_request.status = "failed"
                payout_request.failure_reason = failure_reason
                payout_request.processed_at = timezone.now()
                payout_request.processed_by = request.user
                payout_request.save()

                # TODO: Send rejection email to expert

                return Response(
                    {
                        "success": True,
                        "message": f"Payout request rejected",
                        "failure_reason": failure_reason,
                    },
                    status=status.HTTP_200_OK,
                )


class AdminExpertPaymentAnalyticsAPI(APIView):
    """Get payment analytics for an expert"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        GET /api/annotators/admin/expert-analytics?expert_id=12&date_from=2025-12-01&date_to=2025-12-31

        Returns detailed payment analytics for an expert (admin only)
        """
        from .models import ExpertProfile, ExpertReviewTask
        from datetime import datetime
        from django.utils import timezone

        # Check if user is staff
        if not request.user.is_staff:
            return Response(
                {"error": "Only admins can access analytics"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Get parameters
        expert_id = request.GET.get("expert_id")
        date_from = request.GET.get("date_from")
        date_to = request.GET.get("date_to")

        if not expert_id:
            return Response(
                {"error": "expert_id is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        # Get expert
        try:
            expert = ExpertProfile.objects.get(id=expert_id)
        except ExpertProfile.DoesNotExist:
            return Response(
                {"error": "Expert not found"}, status=status.HTTP_404_NOT_FOUND
            )

        # Parse dates
        if date_from:
            date_from = datetime.fromisoformat(date_from).replace(
                tzinfo=timezone.get_current_timezone()
            )
        else:
            date_from = timezone.now().replace(day=1, hour=0, minute=0, second=0)

        if date_to:
            date_to = datetime.fromisoformat(date_to).replace(
                tzinfo=timezone.get_current_timezone()
            )
        else:
            date_to = timezone.now()

        # Get review tasks in period
        reviews = ExpertReviewTask.objects.filter(
            expert=expert, completed_at__gte=date_from, completed_at__lte=date_to
        )

        # Get transactions in period
        transactions = expert.earnings_transactions.filter(
            created_at__gte=date_from, created_at__lte=date_to
        )

        # Calculate stats
        total_reviews = reviews.count()
        total_earned = transactions.filter(transaction_type="review_payment").aggregate(
            total=models.Sum("amount")
        )["total"] or Decimal("0")

        # Reviews by action
        reviews_by_action = {
            "approved": reviews.filter(review_action="approved").count(),
            "rejected": reviews.filter(review_action="rejected").count(),
            "corrected": reviews.filter(review_action="corrected").count(),
            "escalated": reviews.filter(review_action="escalated").count(),
        }

        # Bonuses earned
        bonuses_earned = {
            "speed_bonus": Decimal("0"),
            "volume_bonus": Decimal("0"),
            "accuracy_bonus": Decimal("0"),
        }

        for transaction in transactions:
            metadata = transaction.metadata or {}
            bonuses = metadata.get("bonuses", 0)
            if bonuses > 0:
                # This is simplified - in reality you'd track which bonus types
                bonuses_earned["speed_bonus"] += Decimal(str(bonuses))

        # Payouts in period
        payouts = expert.payout_requests.filter(
            processed_at__gte=date_from,
            processed_at__lte=date_to,
            status="completed",
        )

        total_payouts = payouts.count()
        total_paid = payouts.aggregate(total=models.Sum("amount"))["total"] or Decimal(
            "0"
        )

        return Response(
            {
                "expert": {
                    "id": expert.id,
                    "name": expert.user.get_full_name() or expert.user.email,
                    "email": expert.user.email,
                    "expertise_level": expert.expertise_level,
                },
                "period": {
                    "from": date_from.isoformat(),
                    "to": date_to.isoformat(),
                },
                "statistics": {
                    "total_reviews": total_reviews,
                    "total_earned": float(total_earned),
                    "average_per_review": (
                        float(total_earned / total_reviews) if total_reviews > 0 else 0
                    ),
                    "total_payouts": total_payouts,
                    "total_paid": float(total_paid),
                    "pending_payout": float(expert.pending_payout),
                    "reviews_by_action": reviews_by_action,
                    "bonuses_earned": {k: float(v) for k, v in bonuses_earned.items()},
                },
                "lifetime": {
                    "total_earned": float(expert.total_earned),
                    "total_withdrawn": float(expert.total_withdrawn),
                    "total_reviews": expert.total_reviews,
                    "total_approvals": expert.total_approvals,
                    "total_rejections": expert.total_rejections,
                    "approval_rate": float(expert.approval_rate),
                },
            },
            status=status.HTTP_200_OK,
        )


# ============================================================================
# NOTIFICATION APIs
# ============================================================================


class AnnotatorNotificationsAPI(APIView):
    """
    API for annotators to view their notifications.

    GET: List all notifications (with optional filters)
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        from .models import AnnotatorNotification, AnnotatorProfile

        try:
            profile = request.user.annotator_profile
        except AnnotatorProfile.DoesNotExist:
            return Response(
                {"error": "User is not an annotator"}, status=status.HTTP_403_FORBIDDEN
            )

        # Get query params
        unread_only = request.query_params.get("unread_only", "false").lower() == "true"
        notification_type = request.query_params.get("type")
        limit = int(request.query_params.get("limit", 50))

        # Build query
        notifications = AnnotatorNotification.objects.filter(annotator=profile)

        if unread_only:
            notifications = notifications.filter(is_read=False)

        if notification_type:
            notifications = notifications.filter(notification_type=notification_type)

        notifications = notifications.order_by("-created_at")[:limit]

        # Count unread
        unread_count = AnnotatorNotification.objects.filter(
            annotator=profile, is_read=False
        ).count()

        # Serialize
        data = []
        for n in notifications:
            data.append(
                {
                    "id": n.id,
                    "type": n.notification_type,
                    "priority": n.priority,
                    "title": n.title,
                    "message": n.message,
                    "task_id": n.task_id,
                    "project_id": n.project_id,
                    "is_read": n.is_read,
                    "created_at": n.created_at.isoformat(),
                    "read_at": n.read_at.isoformat() if n.read_at else None,
                }
            )

        return Response(
            {
                "notifications": data,
                "unread_count": unread_count,
                "total_count": len(data),
            }
        )


class AnnotatorNotificationMarkReadAPI(APIView):
    """
    Mark notification(s) as read.

    POST: Mark single or multiple notifications as read
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, notification_id=None):
        from .models import AnnotatorNotification, AnnotatorProfile

        try:
            profile = request.user.annotator_profile
        except AnnotatorProfile.DoesNotExist:
            return Response(
                {"error": "User is not an annotator"}, status=status.HTTP_403_FORBIDDEN
            )

        if notification_id:
            # Mark single notification
            try:
                notification = AnnotatorNotification.objects.get(
                    id=notification_id, annotator=profile
                )
                notification.mark_as_read()
                return Response({"success": True, "marked_read": 1})
            except AnnotatorNotification.DoesNotExist:
                return Response(
                    {"error": "Notification not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )
        else:
            # Mark all as read
            mark_all = request.data.get("mark_all", False)
            notification_ids = request.data.get("notification_ids", [])

            if mark_all:
                count = AnnotatorNotification.objects.filter(
                    annotator=profile, is_read=False
                ).update(is_read=True, read_at=timezone.now())
            elif notification_ids:
                count = AnnotatorNotification.objects.filter(
                    annotator=profile, id__in=notification_ids, is_read=False
                ).update(is_read=True, read_at=timezone.now())
            else:
                return Response(
                    {"error": "Provide notification_ids or mark_all=true"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            return Response({"success": True, "marked_read": count})


class AnnotatorReworkTasksAPI(APIView):
    """
    API to get tasks that need re-annotation by the annotator.
    These are tasks that were rejected by an expert and assigned back.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        from .models import TaskAssignment, AnnotatorProfile

        try:
            profile = request.user.annotator_profile
        except AnnotatorProfile.DoesNotExist:
            return Response(
                {"error": "User is not an annotator"}, status=status.HTTP_403_FORBIDDEN
            )

        # Get tasks that need rework (flagged for review with status assigned)
        rework_assignments = TaskAssignment.objects.filter(
            annotator=profile, status="assigned", flagged_for_review=True
        ).select_related("task", "task__project")

        tasks = []
        for assignment in rework_assignments:
            task = assignment.task
            tasks.append(
                {
                    "id": task.id,
                    "project_id": task.project_id,
                    "project_title": task.project.title,
                    "rejection_reason": assignment.flag_reason,
                    "assigned_at": (
                        assignment.assigned_at.isoformat()
                        if assignment.assigned_at
                        else None
                    ),
                    "data_preview": str(task.data)[:200] if task.data else None,
                }
            )

        return Response(
            {
                "rework_tasks": tasks,
                "count": len(tasks),
            }
        )


# ============================================================================
# ACCURACY AND PERFORMANCE APIs
# ============================================================================


class AnnotatorAccuracyStatsAPI(APIView):
    """
    API for annotators to view their accuracy statistics and performance metrics.

    GET: Returns accuracy summary, recent scores, and performance trends
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        from .models import AnnotatorProfile, TrustLevel, TaskAssignment
        from .accuracy_service import AccuracyService

        try:
            profile = request.user.annotator_profile
        except AnnotatorProfile.DoesNotExist:
            return Response(
                {"error": "User is not an annotator"}, status=status.HTTP_403_FORBIDDEN
            )

        # Get accuracy summary
        accuracy_summary = AccuracyService.get_annotator_accuracy_summary(profile)

        # Get trust level info
        try:
            trust_level = profile.trust_level
            trust_info = {
                "level": trust_level.level,
                "multiplier": float(trust_level.multiplier),
                "tasks_completed": trust_level.tasks_completed,
                "accuracy_score": float(trust_level.accuracy_score),
                "honeypot_pass_rate": float(trust_level.honeypot_pass_rate),
                "ground_truth_evaluations": trust_level.ground_truth_evaluations or 0,
            }
        except TrustLevel.DoesNotExist:
            trust_info = {
                "level": "new",
                "multiplier": 0.8,
                "tasks_completed": 0,
                "accuracy_score": 0,
                "honeypot_pass_rate": 0,
                "ground_truth_evaluations": 0,
            }

        # Get recent task accuracy breakdown
        recent_tasks = (
            TaskAssignment.objects.filter(
                annotator=profile,
                ground_truth_accuracy__isnull=False,
            )
            .select_related("task", "task__project")
            .order_by("-completed_at")[:10]
        )

        recent_task_accuracy = []
        for assignment in recent_tasks:
            recent_task_accuracy.append(
                {
                    "task_id": assignment.task_id,
                    "project_title": (
                        assignment.task.project.title
                        if assignment.task.project
                        else "Unknown"
                    ),
                    "accuracy_score": float(assignment.ground_truth_accuracy),
                    "accuracy_level": assignment.accuracy_level,
                    "bonus_multiplier": float(assignment.accuracy_bonus_multiplier),
                    "completed_at": (
                        assignment.completed_at.isoformat()
                        if assignment.completed_at
                        else None
                    ),
                }
            )

        # Calculate accuracy distribution
        all_accuracy_assignments = TaskAssignment.objects.filter(
            annotator=profile,
            ground_truth_accuracy__isnull=False,
        ).values_list("accuracy_level", flat=True)

        accuracy_distribution = {
            "excellent": 0,
            "good": 0,
            "acceptable": 0,
            "poor": 0,
            "very_poor": 0,
        }
        for level in all_accuracy_assignments:
            if level in accuracy_distribution:
                accuracy_distribution[level] += 1

        return Response(
            {
                "summary": accuracy_summary,
                "trust_level": trust_info,
                "recent_tasks": recent_task_accuracy,
                "accuracy_distribution": accuracy_distribution,
                "total_evaluated_tasks": sum(accuracy_distribution.values()),
            }
        )


class AnnotatorPerformanceHistoryAPI(APIView):
    """
    API for annotators to view their performance history over time.

    GET: Returns performance history with optional date range filtering
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        from .models import AnnotatorProfile, AnnotatorPerformanceHistory

        try:
            profile = request.user.annotator_profile
        except AnnotatorProfile.DoesNotExist:
            return Response(
                {"error": "User is not an annotator"}, status=status.HTTP_403_FORBIDDEN
            )

        # Get query params
        limit = int(request.query_params.get("limit", 50))
        metric_type = request.query_params.get("metric_type")

        # Build query
        history_query = AnnotatorPerformanceHistory.objects.filter(
            annotator=profile
        ).order_by("-created_at")

        if metric_type:
            history_query = history_query.filter(metric_type=metric_type)

        history = history_query[:limit]

        history_data = []
        for record in history:
            history_data.append(
                {
                    "id": record.id,
                    "metric_type": record.metric_type,
                    "old_value": float(record.old_value) if record.old_value else None,
                    "new_value": float(record.new_value) if record.new_value else None,
                    "change_reason": record.change_reason,
                    "task_id": record.task_id,
                    "details": record.details,
                    "created_at": record.created_at.isoformat(),
                }
            )

        return Response(
            {
                "history": history_data,
                "count": len(history_data),
                "metric_types": [
                    {"key": "ground_truth_accuracy", "label": "Ground Truth Accuracy"},
                    {"key": "honeypot_accuracy", "label": "Honeypot Accuracy"},
                    {"key": "peer_agreement", "label": "Peer Agreement"},
                    {"key": "level_change", "label": "Trust Level Change"},
                ],
            }
        )


# ============================================================================
# EXPERTISE SYSTEM APIs
# ============================================================================


class ExpertiseCategoryListAPI(APIView):
    """
    List all active expertise categories with their specializations.
    
    GET: Returns all categories (no auth required for browsing)
    """
    
    permission_classes = [AllowAny]
    
    def get(self, request):
        from .models import ExpertiseCategory
        from .serializers import ExpertiseCategorySerializer, ExpertiseCategoryListSerializer
        
        include_specializations = request.query_params.get('include_specializations', 'true').lower() == 'true'
        
        categories = ExpertiseCategory.objects.filter(is_active=True).prefetch_related(
            'specializations'
        ).order_by('display_order', 'name')
        
        if include_specializations:
            serializer = ExpertiseCategorySerializer(categories, many=True)
        else:
            serializer = ExpertiseCategoryListSerializer(categories, many=True)
        
        return Response({
            'categories': serializer.data,
            'total': len(serializer.data)
        })


class ExpertiseCategoryDetailAPI(APIView):
    """
    Get details of a specific category with all specializations.
    
    GET: Returns category with specializations
    """
    
    permission_classes = [AllowAny]
    
    def get(self, request, category_slug):
        from .models import ExpertiseCategory
        from .serializers import ExpertiseCategorySerializer
        
        try:
            category = ExpertiseCategory.objects.prefetch_related(
                'specializations'
            ).get(slug=category_slug, is_active=True)
        except ExpertiseCategory.DoesNotExist:
            return Response(
                {'error': 'Category not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = ExpertiseCategorySerializer(category)
        return Response(serializer.data)


class AnnotatorExpertiseListAPI(APIView):
    """
    List and manage annotator's expertise.
    
    GET: List annotator's claimed expertise
    POST: Claim a new expertise
    """
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        from .models import AnnotatorExpertise
        from .serializers import AnnotatorExpertiseSerializer
        
        try:
            profile = request.user.annotator_profile
        except AnnotatorProfile.DoesNotExist:
            return Response(
                {'error': 'Not an annotator account'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get optional status filter
        status_filter = request.query_params.get('status')
        
        expertise_query = AnnotatorExpertise.objects.filter(
            annotator=profile
        ).select_related('category', 'specialization')
        
        if status_filter:
            expertise_query = expertise_query.filter(status=status_filter)
        
        serializer = AnnotatorExpertiseSerializer(expertise_query, many=True)
        
        # Group by status for dashboard
        verified = [e for e in serializer.data if e['status'] == 'verified']
        pending = [e for e in serializer.data if e['status'] in ['claimed', 'testing']]
        failed = [e for e in serializer.data if e['status'] == 'failed']
        
        return Response({
            'expertise': serializer.data,
            'summary': {
                'total': len(serializer.data),
                'verified': len(verified),
                'pending': len(pending),
                'failed': len(failed),
            },
            'verified_expertise': verified,
            'pending_expertise': pending,
            'failed_expertise': failed,
        })
    
    def post(self, request):
        from .models import ExpertiseCategory, ExpertiseSpecialization, AnnotatorExpertise
        from .serializers import AnnotatorExpertiseCreateSerializer, AnnotatorExpertiseSerializer
        
        try:
            profile = request.user.annotator_profile
        except AnnotatorProfile.DoesNotExist:
            return Response(
                {'error': 'Not an annotator account'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = AnnotatorExpertiseCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        category = ExpertiseCategory.objects.get(id=data['category_id'])
        specialization = None
        if data.get('specialization_id'):
            specialization = ExpertiseSpecialization.objects.get(id=data['specialization_id'])
        
        # Check if already claimed
        existing = AnnotatorExpertise.objects.filter(
            annotator=profile,
            category=category,
            specialization=specialization
        ).first()
        
        if existing:
            # Allow retry if failed
            if existing.status == 'failed' and existing.can_retry_test():
                existing.status = 'claimed'
                existing.save()
                return Response(
                    AnnotatorExpertiseSerializer(existing).data,
                    status=status.HTTP_200_OK
                )
            elif existing.status == 'verified':
                return Response(
                    {'error': 'You already have this expertise verified'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            else:
                return Response(
                    {'error': 'You already claimed this expertise'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Create new expertise claim
        expertise = AnnotatorExpertise.objects.create(
            annotator=profile,
            category=category,
            specialization=specialization,
            self_rating=data.get('self_rating', 5),
            years_experience=data.get('years_experience', 0),
            notes=data.get('notes', ''),
            status='claimed'
        )
        
        return Response(
            AnnotatorExpertiseSerializer(expertise).data,
            status=status.HTTP_201_CREATED
        )


class AnnotatorExpertiseDetailAPI(APIView):
    """
    Get, update, or delete a specific expertise claim.
    
    GET: Get expertise details
    PUT: Update expertise info (rating, notes, etc.)
    DELETE: Remove expertise claim
    """
    
    permission_classes = [IsAuthenticated]
    
    def get_expertise(self, request, expertise_id):
        from .models import AnnotatorExpertise
        
        try:
            profile = request.user.annotator_profile
        except AnnotatorProfile.DoesNotExist:
            return None, Response(
                {'error': 'Not an annotator account'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            expertise = AnnotatorExpertise.objects.select_related(
                'category', 'specialization'
            ).get(id=expertise_id, annotator=profile)
        except AnnotatorExpertise.DoesNotExist:
            return None, Response(
                {'error': 'Expertise not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        return expertise, None
    
    def get(self, request, expertise_id):
        from .serializers import AnnotatorExpertiseSerializer
        
        expertise, error = self.get_expertise(request, expertise_id)
        if error:
            return error
        
        return Response(AnnotatorExpertiseSerializer(expertise).data)
    
    def put(self, request, expertise_id):
        from .serializers import AnnotatorExpertiseSerializer
        
        expertise, error = self.get_expertise(request, expertise_id)
        if error:
            return error
        
        # Only allow updating certain fields
        if 'self_rating' in request.data:
            expertise.self_rating = min(10, max(1, int(request.data['self_rating'])))
        if 'years_experience' in request.data:
            expertise.years_experience = max(0, int(request.data['years_experience']))
        if 'notes' in request.data:
            expertise.notes = request.data['notes']
        
        expertise.save()
        
        return Response(AnnotatorExpertiseSerializer(expertise).data)
    
    def delete(self, request, expertise_id):
        expertise, error = self.get_expertise(request, expertise_id)
        if error:
            return error
        
        # Don't allow deleting verified expertise with completed tasks
        if expertise.status == 'verified' and expertise.tasks_completed > 0:
            return Response(
                {'error': 'Cannot delete expertise with completed tasks'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        expertise.delete()
        return Response({'message': 'Expertise removed'}, status=status.HTTP_204_NO_CONTENT)


class ExpertiseTestStartAPI(APIView):
    """
    Start an expertise qualification test.
    
    POST: Start a new test for a specific expertise
    """
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request, expertise_id):
        from .models import (
            AnnotatorExpertise, ExpertiseTestQuestion, ExpertiseTest
        )
        from .serializers import ExpertiseTestSerializer
        import random
        
        try:
            profile = request.user.annotator_profile
        except AnnotatorProfile.DoesNotExist:
            return Response(
                {'error': 'Not an annotator account'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            expertise = AnnotatorExpertise.objects.select_related(
                'category', 'specialization'
            ).get(id=expertise_id, annotator=profile)
        except AnnotatorExpertise.DoesNotExist:
            return Response(
                {'error': 'Expertise not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if can take test
        if expertise.status == 'verified':
            return Response(
                {'error': 'Expertise already verified'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if expertise.status == 'failed' and not expertise.can_retry_test():
            return Response(
                {'error': 'Cannot retry test yet. Please wait for cooldown period.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check for existing in-progress test
        existing_test = ExpertiseTest.objects.filter(
            expertise=expertise,
            status='in_progress'
        ).first()
        
        if existing_test:
            # Check if test expired (time limit exceeded)
            if existing_test.started_at:
                elapsed = timezone.now() - existing_test.started_at
                if elapsed.total_seconds() > existing_test.time_limit_minutes * 60:
                    # Test expired - mark as failed
                    existing_test.status = 'failed'
                    existing_test.save()
                    expertise.record_test_attempt(0, False)
                else:
                    # Return existing test
                    serializer = ExpertiseTestSerializer(existing_test)
                    return Response(serializer.data)
        
        # Get questions for this expertise
        questions_query = ExpertiseTestQuestion.objects.filter(
            category=expertise.category,
            is_active=True
        )
        
        # Filter by specialization if set
        if expertise.specialization:
            # Include both specialization-specific and general category questions
            questions_query = questions_query.filter(
                models.Q(specialization=expertise.specialization) |
                models.Q(specialization__isnull=True)
            )
        else:
            # Only general category questions (no specialization)
            questions_query = questions_query.filter(specialization__isnull=True)
        
        questions = list(questions_query)
        
        if not questions:
            return Response(
                {'error': 'No test questions available for this expertise. Please try again later.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Determine number of questions
        min_questions = expertise.specialization.min_test_questions if expertise.specialization else 10
        num_questions = min(len(questions), max(min_questions, 10))
        
        # Select random questions (mix difficulties)
        selected_questions = random.sample(questions, num_questions)
        
        # Create test
        test = ExpertiseTest.objects.create(
            annotator=profile,
            expertise=expertise,
            status='in_progress',
            started_at=timezone.now(),
            time_limit_minutes=30,
            max_score=sum(q.points for q in selected_questions)
        )
        test.questions.set(selected_questions)
        
        # Update expertise status
        expertise.status = 'testing'
        expertise.save()
        
        serializer = ExpertiseTestSerializer(test)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ExpertiseTestSubmitAPI(APIView):
    """
    Submit answers for an expertise test.
    
    POST: Submit test answers and get results
    """
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request, test_id):
        from .models import ExpertiseTest
        from .serializers import ExpertiseTestResultSerializer
        
        try:
            profile = request.user.annotator_profile
        except AnnotatorProfile.DoesNotExist:
            return Response(
                {'error': 'Not an annotator account'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            test = ExpertiseTest.objects.select_related(
                'expertise__category', 'expertise__specialization'
            ).prefetch_related('questions').get(
                id=test_id,
                annotator=profile
            )
        except ExpertiseTest.DoesNotExist:
            return Response(
                {'error': 'Test not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if test.status != 'in_progress':
            return Response(
                {'error': f'Test is not in progress (status: {test.status})'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check time limit
        if test.started_at:
            elapsed = timezone.now() - test.started_at
            if elapsed.total_seconds() > test.time_limit_minutes * 60:
                test.status = 'failed'
                test.save()
                test.expertise.record_test_attempt(0, False)
                return Response(
                    {'error': 'Test time expired'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Get answers from request
        answers = request.data.get('answers', {})
        
        if not answers:
            return Response(
                {'error': 'No answers provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Grade the test
        test.submit(answers)
        
        # Generate feedback
        if test.passed:
            test.feedback = (
                f"Congratulations! You passed the {test.expertise.category.name} "
                f"qualification test with a score of {test.percentage:.1f}%. "
                "You can now receive tasks in this expertise area."
            )
        else:
            passing_score = test.expertise.specialization.passing_score if test.expertise.specialization else 70
            test.feedback = (
                f"You scored {test.percentage:.1f}%, but {passing_score}% is required to pass. "
                "You can retry the test after a 7-day cooldown period. "
                "Review the study materials to improve your knowledge."
            )
        test.save()
        
        serializer = ExpertiseTestResultSerializer(test)
        return Response(serializer.data)


class ExpertiseTestDetailAPI(APIView):
    """
    Get details of a specific test (for viewing results).
    
    GET: Get test details and results
    """
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request, test_id):
        from .models import ExpertiseTest
        from .serializers import ExpertiseTestResultSerializer, ExpertiseTestSerializer
        
        try:
            profile = request.user.annotator_profile
        except AnnotatorProfile.DoesNotExist:
            return Response(
                {'error': 'Not an annotator account'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            test = ExpertiseTest.objects.select_related(
                'expertise__category', 'expertise__specialization'
            ).prefetch_related('questions').get(
                id=test_id,
                annotator=profile
            )
        except ExpertiseTest.DoesNotExist:
            return Response(
                {'error': 'Test not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Return full results if submitted, otherwise just test info
        if test.status in ['passed', 'failed', 'submitted']:
            serializer = ExpertiseTestResultSerializer(test)
        else:
            serializer = ExpertiseTestSerializer(test)
        
        return Response(serializer.data)


class AnnotatorExpertiseSummaryAPI(APIView):
    """
    Get a summary of annotator's expertise for the earnings dashboard.
    
    GET: Returns expertise summary with task counts
    """
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        from .models import AnnotatorExpertise, TaskAssignment
        from django.db.models import Count, Sum
        
        try:
            profile = request.user.annotator_profile
        except AnnotatorProfile.DoesNotExist:
            return Response(
                {'error': 'Not an annotator account'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get all expertise
        expertise_list = AnnotatorExpertise.objects.filter(
            annotator=profile
        ).select_related('category', 'specialization')
        
        # Build summary
        verified = []
        pending = []
        
        for exp in expertise_list:
            exp_data = {
                'id': exp.id,
                'category': exp.category.name,
                'category_slug': exp.category.slug,
                'specialization': exp.specialization.name if exp.specialization else None,
                'specialization_slug': exp.specialization.slug if exp.specialization else None,
                'status': exp.status,
                'tasks_completed': exp.tasks_completed,
                'accuracy_score': float(exp.accuracy_score),
                'verified_at': exp.verified_at.isoformat() if exp.verified_at else None,
            }
            
            if exp.status == 'verified':
                verified.append(exp_data)
            else:
                pending.append(exp_data)
        
        # Calculate totals
        total_tasks = sum(e['tasks_completed'] for e in verified)
        
        return Response({
            'verified_expertise': verified,
            'pending_expertise': pending,
            'summary': {
                'total_verified': len(verified),
                'total_pending': len(pending),
                'total_tasks_completed': total_tasks,
            }
        })


class ExpertiseApplyAPI(APIView):
    """
    Apply for a new expertise - sends test link via email.
    
    POST: Apply for expertise and receive test link via email
    """
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        from .models import ExpertiseCategory, ExpertiseSpecialization, AnnotatorExpertise
        from .serializers import AnnotatorExpertiseSerializer
        from django.core.mail import send_mail
        from django.template.loader import render_to_string
        from django.utils.html import strip_tags
        from datetime import datetime
        
        try:
            profile = request.user.annotator_profile
        except AnnotatorProfile.DoesNotExist:
            return Response(
                {'error': 'Not an annotator account'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        category_id = request.data.get('category_id')
        specialization_id = request.data.get('specialization_id')
        
        if not category_id:
            return Response(
                {'error': 'category_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            category = ExpertiseCategory.objects.get(id=category_id, is_active=True)
        except ExpertiseCategory.DoesNotExist:
            return Response(
                {'error': 'Invalid category'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        specialization = None
        if specialization_id:
            try:
                specialization = ExpertiseSpecialization.objects.get(
                    id=specialization_id, 
                    category=category,
                    is_active=True
                )
            except ExpertiseSpecialization.DoesNotExist:
                return Response(
                    {'error': 'Invalid specialization'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Find or create expertise record
        expertise, created = AnnotatorExpertise.objects.get_or_create(
            annotator=profile,
            category=category,
            specialization=specialization,
            defaults={
                'status': 'claimed',
                'self_rating': request.data.get('self_rating', 5),
                'years_experience': request.data.get('years_experience', 0),
            }
        )
        
        # Check if already verified
        if expertise.status == 'verified':
            return Response(
                {'error': 'You already have this expertise verified'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Reset status for retries
        if expertise.status == 'failed':
            if not expertise.can_retry_test():
                return Response(
                    {'error': 'You cannot retry yet. Please wait for the cooldown period.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            expertise.status = 'claimed'
        
        # Generate test token
        token = expertise.generate_test_token()
        
        # Build test URL properly
        expertise_name = specialization.name if specialization else category.name
        test_path = f"/annotators/expertise-test?token={token}"
        
        # Use request.build_absolute_uri for proper domain handling
        if request:
            test_url = request.build_absolute_uri(test_path)
            site_url = request.build_absolute_uri('/').rstrip('/')
        else:
            # Fallback to settings.HOSTNAME
            hostname = settings.HOSTNAME.rstrip('/') if settings.HOSTNAME else 'http://localhost:8080'
            test_url = f"{hostname}{test_path}"
            site_url = hostname
        
        # Prepare email context
        email_context = {
            'user_name': profile.user.get_full_name() or profile.user.email.split('@')[0],
            'expertise_name': expertise_name,
            'category_name': category.name,
            'specialization_name': specialization.name if specialization else None,
            'passing_score': specialization.passing_score if specialization else 70,
            'test_url': test_url,
            'site_url': site_url,
            'year': datetime.now().year,
        }
        
        # Render HTML email
        html_message = render_to_string('annotators/emails/expertise_test.html', email_context)
        plain_message = strip_tags(html_message)
        
        subject = f"Synapse - {expertise_name} Qualification Test"
        
        try:
            send_mail(
                subject,
                plain_message,
                settings.DEFAULT_FROM_EMAIL,
                [profile.user.email],
                fail_silently=False,
                html_message=html_message,
            )
            expertise.mark_email_sent()
            email_sent = True
        except Exception as e:
            logger.error(f"Failed to send expertise test email: {e}")
            email_sent = False
        
        expertise.save()
        
        return Response({
            'message': f'Application submitted for {expertise_name}',
            'expertise': AnnotatorExpertiseSerializer(expertise).data,
            'email_sent': email_sent,
            'test_url': test_url,  # Also return URL in case email fails
        }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


class ExpertiseTestByTokenAPI(APIView):
    """
    Access expertise test via email token.
    
    GET: Validate token and get test info
    POST: Start the test
    """
    
    permission_classes = [AllowAny]
    
    def get(self, request):
        from .models import AnnotatorExpertise
        
        token = request.query_params.get('token')
        if not token:
            return Response(
                {'error': 'Token is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            expertise = AnnotatorExpertise.objects.select_related(
                'category', 'specialization', 'annotator__user'
            ).get(test_token=token)
        except AnnotatorExpertise.DoesNotExist:
            return Response(
                {'error': 'Invalid or expired token'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if not expertise.is_test_token_valid():
            return Response(
                {'error': 'Token has expired. Please apply again.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if expertise.status == 'verified':
            return Response({
                'status': 'already_verified',
                'message': 'You already have this expertise verified.',
                'badge_info': expertise.badge_info,
            })
        
        return Response({
            'valid': True,
            'expertise': {
                'id': expertise.id,
                'category_name': expertise.category.name,
                'category_slug': expertise.category.slug,
                'specialization_name': expertise.specialization.name if expertise.specialization else None,
                'specialization_slug': expertise.specialization.slug if expertise.specialization else None,
                'annotator_name': expertise.annotator.user.get_full_name() or expertise.annotator.user.email.split('@')[0],
                'test_attempts': expertise.test_attempts,
            },
            'passing_score': expertise.specialization.passing_score if expertise.specialization else 70,
            'can_start': expertise.status in ['claimed', 'failed'],
        })


class ExpertiseTestSubmitByTokenAPI(APIView):
    """
    Submit expertise test results via token (no login required).
    
    POST: Submit test answers and score
    """
    
    permission_classes = [AllowAny]
    
    def post(self, request):
        from .models import AnnotatorExpertise
        from django.utils import timezone
        
        token = request.data.get('token')
        if not token:
            return Response(
                {'error': 'Token is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            expertise = AnnotatorExpertise.objects.select_related(
                'category', 'specialization', 'annotator'
            ).get(test_token=token)
        except AnnotatorExpertise.DoesNotExist:
            return Response(
                {'error': 'Invalid or expired token'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if not expertise.is_test_token_valid():
            return Response(
                {'error': 'Token has expired'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        score = request.data.get('score', 0)
        passed = request.data.get('passed', False)
        time_taken = request.data.get('time_taken', 0)
        answers = request.data.get('answers', {})
        
        # Update expertise record
        expertise.test_attempts += 1
        expertise.last_test_score = score
        expertise.last_test_at = timezone.now()
        
        passing_score = expertise.specialization.passing_score if expertise.specialization else 70
        
        badge_earned = False
        if score >= passing_score:
            expertise.status = 'verified'
            expertise.verified_at = timezone.now()
            expertise.badge_earned = True
            expertise.badge_earned_at = timezone.now()
            badge_earned = True
        else:
            expertise.status = 'failed'
        
        # Clear token after use
        expertise.test_token = None
        expertise.test_token_created_at = None
        expertise.save()
        
        expertise_name = expertise.specialization.name if expertise.specialization else expertise.category.name
        
        return Response({
            'success': True,
            'score': score,
            'passed': score >= passing_score,
            'passing_score': passing_score,
            'badge_earned': badge_earned,
            'expertise_name': expertise_name,
            'test_attempts': expertise.test_attempts,
        })


class AnnotatorBadgesAPI(APIView):
    """
    Get all badges earned by the annotator.
    
    GET: Returns all earned badges
    """
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        from .models import AnnotatorExpertise
        
        try:
            profile = request.user.annotator_profile
        except AnnotatorProfile.DoesNotExist:
            return Response(
                {'error': 'Not an annotator account'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get all verified expertise with badges
        badges = AnnotatorExpertise.objects.filter(
            annotator=profile,
            badge_earned=True
        ).select_related('category', 'specialization').order_by('-badge_earned_at')
        
        badge_list = []
        for exp in badges:
            badge_list.append({
                'id': exp.id,
                'name': exp.specialization.name if exp.specialization else exp.category.name,
                'category': exp.category.name,
                'category_slug': exp.category.slug,
                'icon': exp.specialization.icon if exp.specialization else exp.category.icon,
                'specialization': exp.specialization.name if exp.specialization else None,
                'earned_at': exp.badge_earned_at.isoformat() if exp.badge_earned_at else None,
                'score': float(exp.last_test_score) if exp.last_test_score else None,
                'tasks_completed': exp.tasks_completed,
                'accuracy_score': float(exp.accuracy_score),
            })
        
        return Response({
            'badges': badge_list,
            'total_badges': len(badge_list),
        })


class ResendExpertiseTestEmailAPI(APIView):
    """
    Resend test invitation email for a specific expertise.
    
    POST: Resend the test email
    """
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request, expertise_id):
        from .models import AnnotatorExpertise
        from django.core.mail import send_mail
        
        try:
            profile = request.user.annotator_profile
        except AnnotatorProfile.DoesNotExist:
            return Response(
                {'error': 'Not an annotator account'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            expertise = AnnotatorExpertise.objects.select_related(
                'category', 'specialization'
            ).get(id=expertise_id, annotator=profile)
        except AnnotatorExpertise.DoesNotExist:
            return Response(
                {'error': 'Expertise not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if expertise.status == 'verified':
            return Response(
                {'error': 'Expertise already verified'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Generate new token
        token = expertise.generate_test_token()
        
        expertise_name = expertise.specialization.name if expertise.specialization else expertise.category.name
        test_path = f"/annotators/expertise-test?token={token}"
        
        # Use request.build_absolute_uri for proper domain handling
        if request:
            test_url = request.build_absolute_uri(test_path)
            site_url = request.build_absolute_uri('/').rstrip('/')
        else:
            hostname = settings.HOSTNAME.rstrip('/') if settings.HOSTNAME else 'http://localhost:8080'
            test_url = f"{hostname}{test_path}"
            site_url = hostname
        
        # Prepare email context
        email_context = {
            'user_name': profile.user.get_full_name() or profile.user.email.split('@')[0],
            'expertise_name': expertise_name,
            'category_name': expertise.category.name,
            'specialization_name': expertise.specialization.name if expertise.specialization else None,
            'passing_score': expertise.specialization.passing_score if expertise.specialization else 70,
            'test_url': test_url,
            'site_url': site_url,
            'year': datetime.now().year,
        }
        
        # Render HTML email
        html_message = render_to_string('annotators/emails/expertise_test.html', email_context)
        plain_message = strip_tags(html_message)
        
        subject = f"Synapse - {expertise_name} Qualification Test"
        
        try:
            send_mail(
                subject,
                plain_message,
                settings.DEFAULT_FROM_EMAIL,
                [profile.user.email],
                fail_silently=False,
                html_message=html_message,
            )
            expertise.mark_email_sent()
            return Response({
                'message': 'Test email sent successfully',
                'test_url': test_url,
            })
        except Exception as e:
            logger.error(f"Failed to send expertise test email: {e}")
            return Response(
                {'error': 'Failed to send email. Please try again.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ============================================================================
# EXPERT EXPERTISE SYSTEM APIs (Admin-assigned expertise for experts)
# ============================================================================

class ExpertExpertiseListAPI(APIView):
    """
    List expert's expertise assignments.
    
    GET: List expert's assigned expertise
    """
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        from .models import ExpertExpertise, ExpertProfile
        from .serializers import ExpertExpertiseSerializer
        
        try:
            profile = ExpertProfile.objects.get(user=request.user)
        except ExpertProfile.DoesNotExist:
            return Response(
                {'error': 'Not an expert account'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get optional status filter
        status_filter = request.query_params.get('status')
        
        expertise_query = ExpertExpertise.objects.filter(
            expert=profile
        ).select_related('category', 'specialization', 'assigned_by')
        
        if status_filter:
            expertise_query = expertise_query.filter(status=status_filter)
        
        serializer = ExpertExpertiseSerializer(expertise_query, many=True)
        
        # Group by status for dashboard
        active = [e for e in serializer.data if e['status'] == 'active']
        assigned = [e for e in serializer.data if e['status'] == 'assigned']
        revoked = [e for e in serializer.data if e['status'] == 'revoked']
        
        return Response({
            'expertise': serializer.data,
            'summary': {
                'total': len(serializer.data),
                'active': len(active),
                'assigned': len(assigned),
                'revoked': len(revoked),
            },
            'active_expertise': active,
            'assigned_expertise': assigned,
            'revoked_expertise': revoked,
        })


class ExpertExpertiseDetailAPI(APIView):
    """
    Get details of a specific expert expertise assignment.
    
    GET: Get expertise details
    """
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request, pk):
        from .models import ExpertExpertise, ExpertProfile
        from .serializers import ExpertExpertiseSerializer
        
        try:
            profile = ExpertProfile.objects.get(user=request.user)
        except ExpertProfile.DoesNotExist:
            return Response(
                {'error': 'Not an expert account'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            expertise = ExpertExpertise.objects.select_related(
                'category', 'specialization', 'assigned_by'
            ).get(pk=pk, expert=profile)
        except ExpertExpertise.DoesNotExist:
            return Response(
                {'error': 'Expertise not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = ExpertExpertiseSerializer(expertise)
        return Response(serializer.data)


class ExpertExpertiseAdminAPI(APIView):
    """
    Admin API for assigning expertise to experts.
    
    POST: Assign expertise to an expert
    PUT: Update expertise assignment
    DELETE: Revoke expertise assignment
    """
    
    permission_classes = [IsAuthenticated]
    
    def check_admin_permission(self, request):
        """Check if user has admin permissions."""
        if not request.user.is_staff:
            return False
        return True
    
    def post(self, request):
        from .models import ExpertExpertise, ExpertProfile, ExpertiseCategory, ExpertiseSpecialization
        from .serializers import ExpertExpertiseSerializer
        
        if not self.check_admin_permission(request):
            return Response(
                {'error': 'Admin permissions required'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        expert_id = request.data.get('expert_id')
        category_id = request.data.get('category_id')
        specialization_id = request.data.get('specialization_id')
        notes = request.data.get('notes', '')
        
        if not expert_id or not category_id:
            return Response(
                {'error': 'expert_id and category_id are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            expert = ExpertProfile.objects.get(pk=expert_id)
        except ExpertProfile.DoesNotExist:
            return Response(
                {'error': 'Expert not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            category = ExpertiseCategory.objects.get(pk=category_id)
        except ExpertiseCategory.DoesNotExist:
            return Response(
                {'error': 'Category not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        specialization = None
        if specialization_id:
            try:
                specialization = ExpertiseSpecialization.objects.get(
                    pk=specialization_id,
                    category=category
                )
            except ExpertiseSpecialization.DoesNotExist:
                return Response(
                    {'error': 'Specialization not found or does not belong to category'},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        # Check for existing expertise
        existing = ExpertExpertise.objects.filter(
            expert=expert,
            category=category,
            specialization=specialization
        ).first()
        
        if existing and existing.status != 'revoked':
            return Response(
                {'error': 'Expert already has this expertise'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if existing and existing.status == 'revoked':
            # Reactivate revoked expertise
            existing.status = 'active'
            existing.assigned_by = request.user
            existing.notes = notes
            existing.save()
            serializer = ExpertExpertiseSerializer(existing)
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        # Create new expertise assignment
        expertise = ExpertExpertise.objects.create(
            expert=expert,
            category=category,
            specialization=specialization,
            status='active',
            assigned_by=request.user,
            notes=notes
        )
        
        serializer = ExpertExpertiseSerializer(expertise)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    def put(self, request, pk):
        from .models import ExpertExpertise
        from .serializers import ExpertExpertiseSerializer
        
        if not self.check_admin_permission(request):
            return Response(
                {'error': 'Admin permissions required'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            expertise = ExpertExpertise.objects.get(pk=pk)
        except ExpertExpertise.DoesNotExist:
            return Response(
                {'error': 'Expertise not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        new_status = request.data.get('status')
        notes = request.data.get('notes')
        
        if new_status:
            if new_status not in ['assigned', 'active', 'revoked']:
                return Response(
                    {'error': 'Invalid status'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            expertise.status = new_status
            if new_status == 'active' and not expertise.assigned_at:
                expertise.activate()
        
        if notes is not None:
            expertise.notes = notes
        
        expertise.save()
        
        serializer = ExpertExpertiseSerializer(expertise)
        return Response(serializer.data)
    
    def delete(self, request, pk):
        from .models import ExpertExpertise
        
        if not self.check_admin_permission(request):
            return Response(
                {'error': 'Admin permissions required'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            expertise = ExpertExpertise.objects.get(pk=pk)
        except ExpertExpertise.DoesNotExist:
            return Response(
                {'error': 'Expertise not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        expertise.revoke()
        return Response({'message': 'Expertise revoked successfully'})


class ExpertExpertiseSummaryAPI(APIView):
    """
    Get summary of expert's expertise for dashboard.
    
    GET: Returns summary statistics
    """
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        from .models import ExpertExpertise, ExpertProfile
        
        try:
            profile = ExpertProfile.objects.get(user=request.user)
        except ExpertProfile.DoesNotExist:
            return Response(
                {'error': 'Not an expert account'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        expertise_list = ExpertExpertise.objects.filter(
            expert=profile
        ).select_related('category', 'specialization')
        
        active_count = expertise_list.filter(status='active').count()
        total_reviews = sum(e.tasks_reviewed for e in expertise_list)
        
        # Get categories with active expertise
        active_categories = list(
            expertise_list.filter(status='active')
            .values_list('category__name', flat=True)
            .distinct()
        )
        
        return Response({
            'active_expertise_count': active_count,
            'total_expertise_count': expertise_list.count(),
            'total_tasks_reviewed': total_reviews,
            'active_categories': active_categories,
        })
