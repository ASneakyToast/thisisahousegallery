# ruff: noqa: E501
from urllib.parse import urlparse

from .base import *  # noqa: F403
from .base import BUILD_TYPE
from .base import DATABASES
from .base import GS_BUCKET_NAME
from .base import INSTALLED_APPS
from .base import SPECTACULAR_SETTINGS
from .base import env

DEBUG = True
SECRET_KEY = env(
    "DJANGO_SECRET_KEY",
    default="84qabQD6jDUMuJ62oHduh7X0cmZ9CHP5phr2QsixrOE7dhwT6m9EIetnfTmidcyp",
)

# GENERAL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#allowed-hosts
# Known custom domains per environment
_KNOWN_HOSTS = {
    "prod": [
        "thisisahousegallery.com",
        "www.thisisahousegallery.com",
    ],
    "staging": [
        "qa.thisisahousegallery.com",
        "staging.thisisahousegallery.com",
    ],
}

ALLOWED_HOSTS = _KNOWN_HOSTS.get(BUILD_TYPE, [])

# Allow additional hosts from Secret Manager (e.g. DJANGO_ALLOWED_HOSTS=host1,host2)
ALLOWED_HOSTS += env.list("DJANGO_ALLOWED_HOSTS", default=[])

# Non-prod: allow any Cloud Run URL (.run.app subdomain wildcard)
# Prod: only allow Cloud Run URL if explicitly set via CLOUDRUN_SERVICE_URL
if BUILD_TYPE != "prod":
    ALLOWED_HOSTS.append(".run.app")
else:
    _cloudrun_url = env("CLOUDRUN_SERVICE_URL", default=None)
    if _cloudrun_url:
        ALLOWED_HOSTS.append(urlparse(_cloudrun_url).netloc)
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")


# DATABASES
# ------------------------------------------------------------------------------
DATABASES["default"]["CONN_MAX_AGE"] = env.int("CONN_MAX_AGE", default=300)
DATABASES["default"]["CONN_HEALTH_CHECKS"] = True


# CACHING
# ------------------------------------------------------------------------------
# Use database cache as default for persistence across Cloud Run cold starts.
# The kiosk carousel cache and other page-level caches survive container restarts.
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.db.DatabaseCache",
        "LOCATION": "django_cache_table",
    },
    # Keep in-memory cache available for anything that needs speed over persistence
    "locmem": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "housegallery-cache",
        "OPTIONS": {
            "MAX_ENTRIES": 1000,
        },
    },
}

# Use database for sessions (persists across container restarts)
SESSION_ENGINE = "django.contrib.sessions.backends.db"


# STATIC & MEDIA
# ------------------------
STATIC_ROOT = str(BASE_DIR / "staticfiles")

STORAGES = {
    "default": {
        "BACKEND": "storages.backends.gcloud.GoogleCloudStorage",
        "OPTIONS": {
            "bucket_name": GS_BUCKET_NAME,
            "location": "media",
            "file_overwrite": False,
            # Cache headers for browser caching (1 year for immutable media)
            "default_acl": None,
            "querystring_auth": False,
            "object_parameters": {
                "cache_control": "public, max-age=31536000, immutable",
            },
        },
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}
# MEDIA_URL = f"https://storage.googleapis.com/{GS_BUCKET_NAME}/media/" # cca.edu doesn't use this...?


# django-rest-framework
# -------------------------------------------------------------------------------
# Tools that generate code samples can use SERVERS to point to the correct domain
SPECTACULAR_SETTINGS["SERVERS"] = [
    {"url": "https://thisisahousegallery.com", "description": "Production server"},
]
