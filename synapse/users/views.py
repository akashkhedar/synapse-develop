"""This file and its contents are licensed under the Apache License 2.0. Please see the included NOTICE for copyright information and LICENSE for a copy of the license."""

import logging
from urllib.parse import quote

from core.feature_flags import flag_set
from core.middleware import enforce_csrf_checks
from core.utils.common import load_func
from django.conf import settings
from django.contrib import auth, messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.middleware.csrf import get_token
from django.shortcuts import redirect, render, reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_GET
from organizations.forms import OrganizationSignupForm
from organizations.models import Organization
from rest_framework.authtoken.models import Token
from users import forms
from users.functions import login, proceed_registration
from django.http import JsonResponse

logger = logging.getLogger()


def public_signup(request):
    """
    Public signup page for React-based signup routes.
    No authentication required - uses public template.
    """
    # Use public template (no user authentication context needed)
    return render(request, "home/home_public.html")


def public_annotator_signup(request):
    """
    Public annotator registration page.
    No authentication required - uses public template.
    """
    # Use public template (no user authentication context needed)
    return render(request, "home/home_public.html")


@login_required
def logout(request):
    # Clear any lingering messages before logout to prevent them from showing on login page
    storage = messages.get_messages(request)
    storage.used = True
    
    auth.logout(request)

    if settings.LOGOUT_REDIRECT_URL:
        return redirect(settings.LOGOUT_REDIRECT_URL)

    if settings.HOSTNAME:
        redirect_url = settings.HOSTNAME
        if not redirect_url.endswith("/"):
            redirect_url += "/"
        return redirect(redirect_url)
    return redirect("/")


@enforce_csrf_checks
def user_signup(request):
    """Sign up page"""
    user = request.user
    next_page = request.GET.get("next")
    token = request.GET.get("token")

    # checks if the URL is a safe redirection.
    if not next_page or not url_has_allowed_host_and_scheme(
        url=next_page, allowed_hosts=request.get_host()
    ):
        if flag_set("fflag_all_feat_dia_1777_ls_homepage_short", user):
            next_page = reverse("main")
        else:
            next_page = reverse("projects:project-index")

    user_form = forms.UserSignupForm()
    organization_form = OrganizationSignupForm()

    if user.is_authenticated:
        return redirect(next_page)

    # make a new user
    if request.method == "POST":
        organization = Organization.objects.first()
        if settings.DISABLE_SIGNUP_WITHOUT_LINK is True:
            if not (token and organization and token == organization.token):
                raise PermissionDenied()
        else:
            if token and organization and token != organization.token:
                raise PermissionDenied()

        user_form = forms.UserSignupForm(request.POST)
        organization_form = OrganizationSignupForm(request.POST)

        if user_form.is_valid():
            redirect_response = proceed_registration(
                request, user_form, organization_form, next_page
            )
            if redirect_response:
                return redirect_response

    if flag_set(
        "fflag_feat_front_lsdv_e_297_increase_oss_to_enterprise_adoption_short"
    ):
        return render(
            request,
            "users/new-ui/user_signup.html",
            {
                "user_form": user_form,
                "organization_form": organization_form,
                "next": quote(next_page),
                "token": token,
                "found_us_options": forms.FOUND_US_OPTIONS,
                "elaborate": forms.FOUND_US_ELABORATE,
            },
        )

    return render(
        request,
        "users/user_signup.html",
        {
            "user_form": user_form,
            "organization_form": organization_form,
            "next": quote(next_page),
            "token": token,
        },
    )


@enforce_csrf_checks
def user_login(request):
    """Login page"""
    user = request.user
    next_page = request.GET.get("next")

    # Store whether next_page was explicitly provided
    has_explicit_next = bool(next_page and url_has_allowed_host_and_scheme(
        url=next_page, allowed_hosts=request.get_host()
    ))

    # Set default next_page if not explicitly provided
    if not has_explicit_next:
        # Default will be determined after authentication based on user role
        next_page = None

    login_form = load_func(settings.USER_LOGIN_FORM)
    form = login_form()

    if user.is_authenticated:
        # Determine redirect for already-authenticated users
        if not next_page:
            if user.is_annotator or user.is_expert:
                next_page = reverse("projects:project-index")
            elif flag_set("fflag_all_feat_dia_1777_ls_homepage_short", user):
                next_page = reverse("main")
            else:
                next_page = reverse("projects:project-index")
        return redirect(next_page)

    if request.method == "POST":
        form = login_form(request.POST)
        if form.is_valid():
            user = form.cleaned_data["user"]

            # Check if email is verified
            if not user.email_verified:
                form.add_error(
                    None,
                    "Please verify your email address before logging in. Check your inbox for the verification link.",
                )
                # Provide a default next_page for the template if None
                template_next = next_page if next_page else reverse("projects:project-index")
                return render(
                    request,
                    (
                        "users/user_login.html"
                        if not flag_set(
                            "fflag_feat_front_lsdv_e_297_increase_oss_to_enterprise_adoption_short"
                        )
                        else "users/new-ui/user_login.html"
                    ),
                    {"form": form, "next": quote(template_next)},
                )

            # Check if annotator has passed the test (skip for experts)
            if user.is_annotator and not user.is_expert:
                # Use source of truth from profile if available (fixes desync issues)
                current_status = user.annotator_status
                if hasattr(user, "annotator_profile"):
                    profile_status = user.annotator_profile.status
                    if current_status != profile_status:
                        user.annotator_status = profile_status
                        user.save(update_fields=["annotator_status"])
                        current_status = profile_status

                if current_status != "approved":
                    # Allow pending_test annotators to log in - they need to take the test
                    if current_status == "pending_test":
                        # Log them in and redirect to test page
                        login(request, user, backend="django.contrib.auth.backends.ModelBackend")
                        if form.cleaned_data["persist_session"] is not True:
                            request.session["keep_me_logged_in"] = False
                            request.session.set_expiry(0)
                        messages.info(request, "Please complete the test to activate your account.")
                        return redirect("/annotators/skill-test/")
                    elif current_status == "pending_verification":
                        error_msg = "Please verify your email first."
                        annotator_action = "resend_verification"
                    elif current_status in ["test_submitted", "under_review"]:
                        error_msg = "Your test is under review. You will be notified once it's approved."
                        annotator_action = None
                    elif current_status == "rejected":
                        error_msg = "Your application has been rejected. Please contact support for more information."
                        annotator_action = None
                    elif current_status == "suspended":
                        error_msg = "Your account has been suspended. Please contact support."
                        annotator_action = None
                    else:
                        error_msg = "Your account is not yet active. Please contact support."
                        annotator_action = None

                    form.add_error(None, error_msg)
                    # Provide a default next_page for the template if None
                    template_next = next_page if next_page else reverse("projects:project-index")
                    return render(
                        request,
                        (
                            "users/user_login.html"
                            if not flag_set(
                                "fflag_feat_front_lsdv_e_297_increase_oss_to_enterprise_adoption_short"
                            )
                            else "users/new-ui/user_login.html"
                        ),
                        {
                            "form": form,
                            "next": quote(template_next),
                            "annotator_action": annotator_action,
                            "annotator_email": email,
                        },
                    )

            login(request, user, backend="django.contrib.auth.backends.ModelBackend")
            if form.cleaned_data["persist_session"] is not True:
                # Set the session to expire when the browser is closed
                request.session["keep_me_logged_in"] = False
                request.session.set_expiry(0)

            # Only set organization for clients (not annotators or experts)
            # Experts are like annotators - they don't require organization membership
            if user.is_client and not user.is_annotator and not user.is_expert:
                # user is organization member (client only)
                org_pk = Organization.find_by_user(user).pk
                user.active_organization_id = org_pk
                user.save(update_fields=["active_organization"])
            
            # If the request expects JSON (AJAX/API), return JSON with role flags
            accept = request.headers.get("Accept", "")
            is_xhr = request.META.get("HTTP_X_REQUESTED_WITH") == "XMLHttpRequest"
            if (
                "application/json" in accept
                or is_xhr
                or request.content_type == "application/json"
            ):
                session_key = request.session.session_key
                return JsonResponse(
                    {
                        "message": "Login successful",
                        "user": {
                            "id": user.id,
                            "email": user.email,
                            "first_name": user.first_name,
                            "last_name": user.last_name,
                        },
                        "is_annotator": user.is_annotator,
                        "is_client": user.is_client,
                        "is_expert": user.is_expert,
                        "session_key": session_key,
                    },
                    status=200,
                )

            # Determine the redirect URL based on user role (if not explicitly provided)
            if not has_explicit_next:
                if user.is_annotator or user.is_expert:
                    # Annotators and experts always go to projects page
                    next_page = reverse("projects:project-index")
                elif flag_set("fflag_all_feat_dia_1777_ls_homepage_short", user):
                    # Clients with the feature flag go to dashboard
                    next_page = reverse("main")
                else:
                    # Default for clients without flag - projects page
                    next_page = reverse("projects:project-index")

            return redirect(next_page)

    # Provide a default next_page for the template if None
    template_next = next_page if next_page else reverse("projects:project-index")
    
    if flag_set(
        "fflag_feat_front_lsdv_e_297_increase_oss_to_enterprise_adoption_short"
    ):
        return render(
            request,
            "users/new-ui/user_login.html",
            {"form": form, "next": quote(template_next)},
        )

    return render(
        request, "users/user_login.html", {"form": form, "next": quote(template_next)}
    )


@login_required
def user_account(request, sub_path=None):
    """
    Handle user account view and profile updates.

    This view displays the user's profile information and allows them to update
    it. It requires the user to be authenticated and have an active organization
    or an organization_pk in the session.

    Args:
        request (HttpRequest): The request object.
        sub_path (str, optional): A sub-path parameter for potential URL routing.
            Defaults to None.

    Returns:
        HttpResponse: Renders the user account template with user profile form,
            or redirects to 'main' if no active organization is found,
            or redirects back to user-account after successful profile update.

    Notes:
        - Authentication is required (enforced by @login_required decorator)
        - Retrieves the user's API token for display in the template
        - Form validation happens on POST requests
    """
    user = request.user

    if user.active_organization is None and "organization_pk" not in request.session:
        return redirect(reverse("main"))

    form = forms.UserProfileForm(instance=user)
    token = Token.objects.get(user=user)

    if request.method == "POST":
        form = forms.UserProfileForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return redirect(reverse("user-account"))

    return render(
        request,
        "users/user_account.html",
        {"settings": settings, "user": user, "user_profile_form": form, "token": token},
    )


@require_GET
def refresh_csrf_token(request):
    """
    Returns a fresh CSRF token for the current session.
    
    This endpoint is used to refresh CSRF tokens when a user returns to a 
    login/signup page after their session may have changed (e.g., after 
    clicking an email verification link in a new tab).
    """
    csrf_token = get_token(request)
    return JsonResponse({"csrfToken": csrf_token})

