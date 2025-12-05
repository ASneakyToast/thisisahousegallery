# ruff: noqa: E501
from .base import *  # noqa: F403
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
# Explicit ALLOWED_HOSTS for production and dev domains
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=[
    "thisisahousegallery.com",
    "www.thisisahousegallery.com",
    "prod.thisisahousegallery.com",
    "qa.thisisahousegallery.com",
    "housegallery-dev-jrl-service-591747915969.us-west1.run.app"
])


# DATABASES
# ------------------------------------------------------------------------------
DATABASES["default"]["CONN_MAX_AGE"] = env.int("CONN_MAX_AGE", default=300)
DATABASES["default"]["CONN_HEALTH_CHECKS"] = True


# CACHING
# ------------------------------------------------------------------------------
# Database-backed cache - free, no extra GCP services required
# Run `python manage.py createcachetable` once to create the cache table
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.db.DatabaseCache",
        "LOCATION": "django_cache_table",
    }
}

# Use cache for sessions (avoids DB hit on every request)
SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "default"


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
