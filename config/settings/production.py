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
# CLOUDRUN_SERVICE_URLS contains comma-separated URLs with "cloudrun-name" placeholder
# e.g. https://housegallery-cloudrun-name-service-123.us-west1.run.app,https://thisisahousegallery.com
# At runtime, "cloudrun-name" is replaced with BUILD_TYPE (staging, prod, etc.)
CLOUDRUN_SERVICE_URLS = env("CLOUDRUN_SERVICE_URLS", default=None)
if CLOUDRUN_SERVICE_URLS:
    CLOUDRUN_SERVICE_URLS = CLOUDRUN_SERVICE_URLS.replace("cloudrun-name", BUILD_TYPE)
    CSRF_TRUSTED_ORIGINS = CLOUDRUN_SERVICE_URLS.split(",")
    ALLOWED_HOSTS = [urlparse(url).netloc for url in CSRF_TRUSTED_ORIGINS]
    SECURE_SSL_REDIRECT = True
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
else:
    raise Exception("CLOUDRUN_SERVICE_URLS must be set for production/cloud run environments")


# DATABASES
# ------------------------------------------------------------------------------
DATABASES["default"]["CONN_MAX_AGE"] = env.int("CONN_MAX_AGE", default=300)
DATABASES["default"]["CONN_HEALTH_CHECKS"] = True


# CACHING
# ------------------------------------------------------------------------------
# Use in-memory cache for performance (avoids cross-region DB latency)
# Note: Cache is per-container and clears on restart, but for a low-traffic
# site this is fine - first request warms cache, subsequent requests are fast.
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "housegallery-cache",
        "OPTIONS": {
            "MAX_ENTRIES": 1000,
        },
    },
    # Keep database cache available for anything that needs persistence
    "db": {
        "BACKEND": "django.core.cache.backends.db.DatabaseCache",
        "LOCATION": "django_cache_table",
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
            "default_acl": "publicRead",
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
