"""Landing page view for unauthenticated users"""

from django.shortcuts import render, redirect, reverse
from core.feature_flags import flag_set


def landing_page(request):
    """
    Public landing page for unauthenticated users.
    Redirects authenticated users to the main dashboard.
    """
    user = request.user

    if user.is_authenticated:
        if (
            user.active_organization is None
            and "organization_pk" not in request.session
        ):
            # User has no organization, logout and show landing
            from django.contrib.auth import logout

            logout(request)
            return render(request, "landing/landing_page.html")

        # Redirect authenticated users to dashboard
        if flag_set("fflag_all_feat_dia_1777_ls_homepage_short", user):
            return redirect(reverse("main"))
        else:
            return redirect(reverse("projects:project-index"))

    # Show landing page to unauthenticated users
    return render(request, "landing/landing_page.html")





