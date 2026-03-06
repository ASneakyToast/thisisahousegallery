# ruff: noqa: E501
import io
import os

from .base import *  # noqa: F403
from .base import INSTALLED_APPS
from .base import MIDDLEWARE
from .base import WEBPACK_LOADER
from .base import env

from google.cloud import secretmanager

# SECRETS & GCP
# ------------------------------------------------------------------------------
# Load secrets from Secret Manager (same as base.py does for production,
# but done here because local_cloud is excluded from base.py's Secret Manager block).
PROJECT_ID = os.environ.get("GCP_PROJECT")
BUILD_TYPE = os.environ.get("BUILD_TYPE")
if not PROJECT_ID or not BUILD_TYPE:
    raise Exception("No GCP_PROJECT or BUILD_TYPE. Exit")

client = secretmanager.SecretManagerServiceClient()
secret = f"projects/{PROJECT_ID}/secrets/housegallery-settings/versions/latest"
payload = client.access_secret_version(name=secret).payload.data.decode("UTF-8")
env.read_env(io.StringIO(payload))

SECRET_KEY = env("SECRET_KEY")


# GENERAL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#debug
DEBUG = True
# https://docs.djangoproject.com/en/dev/ref/settings/#allowed-hosts
ALLOWED_HOSTS = [
    "localhost",
    "0.0.0.0",
    "127.0.0.1",
]  # noqa: S104

INTERNAL_IPS = ['127.0.0.1']


# DATABASES
# ------------------------------------------------------------------------------
# Build from DATABASE_URL (now available via Secret Manager).
# Override HOST to use the cloud-sql-proxy Docker service by default;
# .env.local can set CLOUD_SQL_PROXY_HOST=localhost for uv run outside Docker.
DATABASES = {"default": env.db()}
DATABASES["default"]["HOST"] = env("CLOUD_SQL_PROXY_HOST", default="cloud-sql-proxy")
DATABASES["default"]["PORT"] = "5432"
DATABASES["default"]["NAME"] = f"housegallery-{BUILD_TYPE}"
DATABASES["default"]["ATOMIC_REQUESTS"] = True


# TEMPLATES
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#templates
BASE_URL = 'http://localhost:8000'
WAGTAILADMIN_BASE_URL = 'http://localhost:8000'


# SECURITY
# ------------------------------------------------------------------------------
# Disable forcing HTTPS locally since development server supports HTTP only.
SECURE_SSL_REDIRECT = False

# Disable session expire on browser close
SESSION_COOKIE_AGE = 60 * 20000
SESSION_EXPIRE_AT_BROWSER_CLOSE = False


# CACHES
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#caches
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "",
    },
}


# EMAIL
# ------------------------------------------------------------------------------
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"


# WhiteNoise
# ------------------------------------------------------------------------------
# http://whitenoise.evans.io/en/latest/django.html#using-whitenoise-in-development
INSTALLED_APPS = ["whitenoise.runserver_nostatic", *INSTALLED_APPS]


# django-extensions
# ------------------------------------------------------------------------------
# https://django-extensions.readthedocs.io/en/latest/installation_instructions.html#configuration
INSTALLED_APPS += ["django_extensions"]


# django-querycount
# ------------------------------------------------------------------------------
# https://github.com/bradmontgomery/django-querycount
INSTALLED_APPS += ["querycount"]

# Add querycount middleware
MIDDLEWARE += ["querycount.middleware.QueryCountMiddleware"]

# Configure querycount settings
QUERYCOUNT = {
    'THRESHOLDS': {
        'MEDIUM': 50,
        'HIGH': 200,
        'MIN_TIME_TO_LOG': 0,
        'MIN_QUERY_COUNT_TO_LOG': 0,
    },
    'IGNORE_REQUEST_PATTERNS': [],
    'IGNORE_SQL_PATTERNS': [],
    'DISPLAY_DUPLICATES': None,
    'RESPONSE_HEADER': 'X-DjangoQueryCount-Count'
}


# django-webpack-loader
# ------------------------------------------------------------------------------
WEBPACK_LOADER["DEFAULT"]["CACHE"] = not DEBUG

# Static files
# ------------------------------------------------------------------------------
# This fixes the issue with webpack static files in development
STATIC_ROOT = str(BASE_DIR / "static")

# Fix Wagtail warning about GS_FILE_OVERWRITE
GS_FILE_OVERWRITE = False