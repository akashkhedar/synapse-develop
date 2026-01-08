"""This file and its contents are licensed under the Apache License 2.0. Please see the included NOTICE for copyright information and LICENSE for a copy of the license."""

import json

from core.settings.base import *  # noqa
from core.utils.secret_key import generate_secret_key_if_missing

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = generate_secret_key_if_missing(BASE_DATA_DIR)

DJANGO_DB = get_env("DJANGO_DB", DJANGO_DB_SQLITE)
DATABASES = {"default": DATABASES_ALL[DJANGO_DB]}

MIDDLEWARE.append("organizations.middleware.DummyGetSessionMiddleware")
MIDDLEWARE.append("core.middleware.UpdateLastActivityMiddleware")
if INACTIVITY_SESSION_TIMEOUT_ENABLED:
    MIDDLEWARE.append("core.middleware.InactivitySessionTimeoutMiddleWare")

ADD_DEFAULT_ML_BACKENDS = False

LOGGING["root"]["level"] = get_env("LOG_LEVEL", "WARNING")

DEBUG = get_bool_env("DEBUG", False)

DEBUG_PROPAGATE_EXCEPTIONS = get_bool_env("DEBUG_PROPAGATE_EXCEPTIONS", False)

SESSION_COOKIE_SECURE = get_bool_env("SESSION_COOKIE_SECURE", False)

SESSION_ENGINE = "django.contrib.sessions.backends.signed_cookies"

# Disable Sentry in development - set SENTRY_DSN env var to enable in production
SENTRY_DSN = get_env("SENTRY_DSN", None)
SENTRY_ENVIRONMENT = get_env("SENTRY_ENVIRONMENT", "opensource")

# Disable frontend Sentry in development - set FRONTEND_SENTRY_DSN env var to enable in production
FRONTEND_SENTRY_DSN = get_env("FRONTEND_SENTRY_DSN", None)
FRONTEND_SENTRY_ENVIRONMENT = get_env("FRONTEND_SENTRY_ENVIRONMENT", "opensource")

EDITOR_KEYMAP = json.dumps(get_env("EDITOR_KEYMAP"))

from synapse import __version__
from synapse.core.utils import sentry

sentry.init_sentry(release_name="synapse", release_version=__version__)

# we should do it after sentry init
from synapse.core.utils.common import collect_versions

versions = collect_versions()

# in Synapse Community version, feature flags are always ON
FEATURE_FLAGS_DEFAULT_VALUE = True
# or if file is not set, default is using offline mode
FEATURE_FLAGS_OFFLINE = get_bool_env("FEATURE_FLAGS_OFFLINE", True)

FEATURE_FLAGS_FILE = get_env("FEATURE_FLAGS_FILE", "feature_flags.json")
FEATURE_FLAGS_FROM_FILE = True
try:
    from core.utils.io import find_node

    find_node("synapse", FEATURE_FLAGS_FILE, "file")
except IOError:
    FEATURE_FLAGS_FROM_FILE = False

STORAGE_PERSISTENCE = get_bool_env("STORAGE_PERSISTENCE", True)





