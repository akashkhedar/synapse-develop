"""This file and its contents are licensed under the Apache License 2.0. Please see the included NOTICE for copyright information and LICENSE for a copy of the license."""

from core.feature_flags import all_flags
from core.utils.common import collect_versions
from django.conf import settings as django_settings


def sentry_fe(request):
    # return the value you want as a dictionary, you may add multiple values in there
    return {"SENTRY_FE": django_settings.SENTRY_FE}


def settings(request):
    """Make available django settings on each template page"""
    versions = collect_versions()

    os_release = versions.get("synapse-os-backend", {}).get("commit", "none")[0:6]
    # django templates can't access names with hyphens
    versions["sf"] = versions.get("synapse-frontend", {})
    versions["sf"]["commit"] = versions["sf"].get("commit", os_release)[0:6]

    versions["dm2"] = versions.get("dm2", {})
    versions["dm2"]["commit"] = versions["dm2"].get("commit", os_release)[0:6]

    versions["backend"] = {}
    if "synapse-os-backend" in versions:
        versions["backend"]["commit"] = versions["synapse-os-backend"].get(
            "commit", "none"
        )[0:6]
    if "synapse-enterprise-backend" in versions:
        versions["backend"]["commit"] = versions["synapse-enterprise-backend"].get(
            "commit", "none"
        )[0:6]

    feature_flags = {}
    if hasattr(request, "user"):
        feature_flags = all_flags(request.user)

    return {
        "settings": django_settings,
        "versions": versions,
        "feature_flags": feature_flags,
    }
