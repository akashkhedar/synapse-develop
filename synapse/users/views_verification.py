"""Email verification views"""

import logging

from django.contrib import messages
from django.contrib.auth import login
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from users.email_verification import resend_verification_email
from users.models import User
from users.models_verification import EmailVerificationToken

logger = logging.getLogger(__name__)


def verification_pending(request):
    """Show verification pending page after signup"""
    return render(request, "users/verification_pending.html")


@require_http_methods(["GET"])
def verify_email(request, token):
    """
    Verify user email address using token

    URL: /user/verify-email/<token>/
    """
    try:
        verification_token = get_object_or_404(EmailVerificationToken, token=token)
        user = verification_token.user

        # Check if token is valid
        if not verification_token.is_valid():
            if verification_token.is_used:
                # Token already used - but check if user is already verified
                if user.email_verified:
                    # Log them in and redirect appropriately
                    login(request, user, backend="django.contrib.auth.backends.ModelBackend")
                    
                    if user.is_annotator:
                        # Check annotator profile status
                        try:
                            profile = user.annotator_profile
                            if profile.status == "pending_test":
                                messages.info(
                                    request, "Your email is already verified. Please complete the test."
                                )
                                return redirect("/annotators/skill-test/")
                            elif profile.status == "approved":
                                messages.success(request, "Welcome back!")
                                return redirect(reverse("projects:project-index"))
                            elif profile.status in ["test_submitted", "under_review"]:
                                messages.info(
                                    request, "Your test is being reviewed. We'll notify you once approved."
                                )
                                return redirect("/annotators/test-result/")
                            else:
                                messages.info(request, f"Your account status: {profile.get_status_display()}")
                                return redirect(reverse("user-login"))
                        except Exception:
                            return redirect(reverse("projects:project-index"))
                    else:
                        messages.success(request, "Welcome back!")
                        return redirect(reverse("projects:project-index"))
                else:
                    messages.warning(
                        request, "This verification link has already been used. Please request a new one below."
                    )
            else:
                messages.error(
                    request,
                    "This verification link has expired. Please request a new one below.",
                )
            return redirect("resend-verification")

        # Mark email as verified
        user = verification_token.user
        user.email_verified = True
        user.email_verified_at = timezone.now()
        user.save(update_fields=["email_verified", "email_verified_at"])

        # Mark token as used
        verification_token.mark_as_used()

        # If user is an annotator, update status and redirect to test
        if user.is_annotator:
            user.annotator_status = "pending_test"
            user.save(update_fields=["annotator_status"])
            logger.info(
                f"Email verified for annotator: {user.email}, status: {user.annotator_status}"
            )

            # Log the user in
            login(request, user, backend="django.contrib.auth.backends.ModelBackend")

            messages.success(
                request,
                "Your email has been verified! Please complete the test to activate your account.",
            )
            # Redirect to test page
            return redirect("/annotators/skill-test/")
        else:
            # For clients, log them in and redirect to dashboard
            login(request, user, backend="django.contrib.auth.backends.ModelBackend")
            messages.success(
                request,
                "Your email has been verified successfully! Welcome to Synapse.",
            )
            logger.info(f"Email verified for user: {user.email}")
            return redirect(reverse("projects:project-index"))

    except EmailVerificationToken.DoesNotExist:
        messages.error(request, "Invalid verification link.")
        return redirect("resend-verification")
    except Exception as e:
        logger.error(f"Error during email verification: {e}")
        messages.error(
            request, "An error occurred during verification. Please try again."
        )
        return redirect("resend-verification")


def resend_verification(request):
    """
    Resend verification email

    URL: /user/resend-verification/
    """
    if request.method == "POST":
        email = request.POST.get("email", "").strip()

        if not email:
            messages.error(request, "Please provide your email address.")
            return render(request, "users/resend_verification.html")

        try:
            user = User.objects.get(email=email)

            # Check if already verified
            if user.email_verified:
                # For annotators, check their status and redirect appropriately
                if user.is_annotator:
                    try:
                        profile = user.annotator_profile
                        if profile.status == "pending_test":
                            messages.info(
                                request, "Your email is already verified! Please log in to take the test."
                            )
                        elif profile.status in ["test_submitted", "under_review"]:
                            messages.info(
                                request, "Your email is verified and test submitted. Please log in to check status."
                            )
                        elif profile.status == "approved":
                            messages.success(
                                request, "Your account is fully approved! Please log in."
                            )
                        else:
                            messages.info(
                                request, "Your email is already verified. Please log in."
                            )
                    except Exception:
                        messages.info(
                            request, "Your email is already verified. You can log in."
                        )
                else:
                    messages.info(
                        request, "Your email is already verified. You can log in."
                    )
                return redirect("user-login")

            # Resend verification email
            if resend_verification_email(user, request):
                messages.success(
                    request,
                    "Verification email has been sent! Please check your inbox.",
                )
                logger.info(f"Verification email resent to: {email}")
            else:
                messages.error(
                    request,
                    "Failed to send verification email. Please try again later.",
                )
                logger.error(f"Failed to resend verification email to: {email}")

        except User.DoesNotExist:
            # Don't reveal if email exists or not for security
            messages.success(
                request,
                "If an account exists with this email, a verification link will be sent.",
            )
            logger.warning(
                f"Verification resend attempted for non-existent email: {email}"
            )

        return render(request, "users/resend_verification.html")

    return render(request, "users/resend_verification.html")





