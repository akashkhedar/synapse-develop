"""This file and its contents are licensed under the Apache License 2.0. Please see the included NOTICE for copyright information and LICENSE for a copy of the license."""

import logging
import os
import uuid
from time import time

from core.utils.common import load_func

logger = logging.getLogger(__name__)
from django import forms
from django.conf import settings
from django.contrib import auth
from django.core.files.images import get_image_dimensions
from django.shortcuts import redirect
from django.urls import reverse
from organizations.models import Organization
from users.models_verification import EmailVerificationToken
from users.email_verification import send_verification_email


def hash_upload(instance, filename):
    filename = str(uuid.uuid4())[0:8] + "-" + filename
    return settings.AVATAR_PATH + "/" + filename


def check_avatar(files):
    images = list(files.items())
    if not images:
        return None

    _, avatar = list(files.items())[0]  # get first file
    w, h = get_image_dimensions(avatar)
    if not w or not h:
        raise forms.ValidationError("Can't read image, try another one")

    # validate dimensions
    max_width = max_height = 1200
    if w > max_width or h > max_height:
        raise forms.ValidationError(
            "Please use an image that is %s x %s pixels or smaller."
            % (max_width, max_height)
        )

    valid_extensions = ["jpeg", "jpg", "gif", "png"]

    filename = avatar.name
    # check file extension
    ext = os.path.splitext(filename)[1].lstrip(".").lower()
    if ext not in valid_extensions:
        raise forms.ValidationError(
            "Please upload a valid image file with extensions: JPEG, JPG, GIF, or PNG."
        )

    # validate content type
    main, sub = avatar.content_type.split("/")
    if not (main == "image" and sub.lower() in valid_extensions):
        raise forms.ValidationError("Please use a JPEG, GIF or PNG image.")

    # validate file size
    max_size = 1024 * 1024
    if len(avatar) > max_size:
        raise forms.ValidationError(
            "Avatar file size may not exceed " + str(max_size / 1024) + " kb"
        )

    return avatar


def save_user(request, next_page, user_form):
    """Save user instance to DB"""
    user = user_form.save()
    user.username = user.email.split("@")[0]

    # Determine role based on user_role field from form
    user_role = user_form.cleaned_data.get("user_role", "client")
    if user_role == "annotator":
        user.is_annotator = True
        user.is_client = False
    else:
        # Default to client
        user.is_client = True
        user.is_annotator = False

    logger.info(f"Creating user {user.email} with role: {user_role}")

    # Save user first to get the ID
    user.save()

    # Check if user is signing up via invite token
    invite_token = request.GET.get("token")
    invited_org = None

    if invite_token:
        try:
            # Find the organization by invite token
            invited_org = Organization.objects.get(token=invite_token)
            logger.info(
                f"User {user.email} signing up with invite token for organization {invited_org.title}"
            )
        except Organization.DoesNotExist:
            logger.warning(
                f"Invalid invite token provided during signup: {invite_token}"
            )
            invited_org = None

    # Set initial status for annotators, skip organization for them
    if user.is_annotator:
        user.annotator_status = "pending_verification"
        user.save(update_fields=["annotator_status"])
        logger.info(f"Set annotator_status to pending_verification for {user.email}")
    else:
        # Create a personal organization for clients
        org_title = f"{user.email.split('@')[0]}'s Organization"
        personal_org = Organization.create_organization(
            created_by=user, title=org_title
        )

        # If user was invited to an organization, add them to it and set as active
        if invited_org:
            invited_org.add_user(user)
            user.active_organization = invited_org
            logger.info(
                f"Added user {user.email} to invited organization {invited_org.title}"
            )
        else:
            # Otherwise, set their personal organization as active
            user.active_organization = personal_org

        user.save(update_fields=["active_organization"])

    # Create email verification token and send email
    token = EmailVerificationToken.create_token(user)
    try:
        send_verification_email(user, token, request)
        logger.info(f"Email verification function called for {user.email}")
    except Exception as e:
        logger.error(f"Failed to send verification email to {user.email}: {str(e)}")
        import traceback

        logger.error(traceback.format_exc())

    request.advanced_json = {
        "email": user.email,
        "allow_newsletters": user.allow_newsletters,
        "update-notifications": 1,
        "new-user": 1,
        "how_find_us": user_form.cleaned_data.get("how_find_us", ""),
    }
    if user_form.cleaned_data.get("how_find_us", "") == "Other":
        request.advanced_json["elaborate"] = user_form.cleaned_data.get("elaborate", "")

    # Store success message in session
    from django.contrib import messages

    messages.success(
        request,
        f"Account created successfully! Please check your email ({user.email}) to verify your account before logging in.",
    )

    # Redirect to login page
    redirect_url = reverse("user-login")
    return redirect(redirect_url)


def proceed_registration(request, user_form, organization_form, next_page):
    """Register a new user for POST user_signup"""
    # save user to db
    save_user = load_func(settings.SAVE_USER)
    response = save_user(request, next_page, user_form)

    return response


def login(request, *args, **kwargs):
    request.session["last_login"] = time()
    return auth.login(request, *args, **kwargs)





