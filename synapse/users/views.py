"""This file and its contents are licensed under the Apache License 2.0. Please see the included NOTICE for copyright information and LICENSE for a copy of the license."""

import logging
from urllib.parse import quote

from core.feature_flags import flag_set
from core.middleware import enforce_csrf_checks
from core.utils.common import load_func
from django.conf import settings
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect, render, reverse
from django.utils.http import url_has_allowed_host_and_scheme
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

    # checks if the URL is a safe redirection.
    if not next_page or not url_has_allowed_host_and_scheme(
        url=next_page, allowed_hosts=request.get_host()
    ):
        if flag_set("fflag_all_feat_dia_1777_ls_homepage_short", user):
            next_page = reverse("main")
        else:
            next_page = reverse("projects:project-index")

    login_form = load_func(settings.USER_LOGIN_FORM)
    form = login_form()

    if user.is_authenticated:
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
                return render(
                    request,
                    (
                        "users/user_login.html"
                        if not flag_set(
                            "fflag_feat_front_lsdv_e_297_increase_oss_to_enterprise_adoption_short"
                        )
                        else "users/new-ui/user_login.html"
                    ),
                    {"form": form, "next": quote(next_page)},
                )

            # Check if annotator has passed the test (skip for experts)
            if user.is_annotator and not user.is_expert:
                if user.annotator_status != "approved":
                    if user.annotator_status in [
                        "pending_test",
                        "pending_verification",
                    ]:
                        error_msg = "Please complete the test before logging in. Check your email for the test link."
                    elif user.annotator_status in ["test_submitted", "under_review"]:
                        error_msg = "Your test is under review. You will be notified once it's approved."
                    elif user.annotator_status == "rejected":
                        error_msg = "Your application has been rejected. Please contact support for more information."
                    elif user.annotator_status == "suspended":
                        error_msg = (
                            "Your account has been suspended. Please contact support."
                        )
                    else:
                        error_msg = (
                            "Your account is not yet active. Please contact support."
                        )

                    form.add_error(None, error_msg)
                    return render(
                        request,
                        (
                            "users/user_login.html"
                            if not flag_set(
                                "fflag_feat_front_lsdv_e_297_increase_oss_to_enterprise_adoption_short"
                            )
                            else "users/new-ui/user_login.html"
                        ),
                        {"form": form, "next": quote(next_page)},
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

            return redirect(next_page)

    if flag_set(
        "fflag_feat_front_lsdv_e_297_increase_oss_to_enterprise_adoption_short"
    ):
        return render(
            request,
            "users/new-ui/user_login.html",
            {"form": form, "next": quote(next_page)},
        )

    return render(
        request, "users/user_login.html", {"form": form, "next": quote(next_page)}
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





