# ruff: noqa: E501
from .base import *  # noqa: F403
from .base import INSTALLED_APPS
from .base import MIDDLEWARE
from .base import WEBPACK_LOADER
from .base import env
import os


# GENERAL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#debug
DEBUG = True
# https://docs.djangoproject.com/en/dev/ref/settings/#secret-key
SECRET_KEY = env(
    "DJANGO_SECRET_KEY",
    default="84qabQD6jDUMuJ62oHduh7X0cmZ9CHP5phr2QsixrOE7dhwT6m9EIetnfTmidcyp",
)
# https://docs.djangoproject.com/en/dev/ref/settings/#allowed-hosts
ALLOWED_HOSTS = [
    "localhost", 
     "0.0.0.0", 
     "127.0.0.1",
 ]  # noqa: S104

INTERNAL_IPS = ['127.0.0.1', ]


# DATABASES
# ------------------------------------------------------------------------------
# Override the database configuration for Cloud SQL proxy if requested
if os.environ.get("USE_CLOUD_DB", "false").lower() == "true":
    # Connect to Cloud SQL via proxy instead of local Postgres
    DATABASES = {
        "default": env.db(),  # Uses DATABASE_URL environment variable
    }
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


# WhiteNoise
# ------------------------------------------------------------------------------
# http://whitenoise.evans.io/en/latest/django.html#using-whitenoise-in-development
INSTALLED_APPS = ["whitenoise.runserver_nostatic", *INSTALLED_APPS]


# django-extensions
# ------------------------------------------------------------------------------
# https://django-extensions.readthedocs.io/en/latest/installation_instructions.html#configuration
INSTALLED_APPS += ["django_extensions"]


# django-webpack-loader
# ------------------------------------------------------------------------------
WEBPACK_LOADER["DEFAULT"]["CACHE"] = not DEBUG

# Static files
# ------------------------------------------------------------------------------
# This fixes the issue with webpack static files in development
STATIC_ROOT = str(BASE_DIR / "static")

# Fix Wagtail warning about GS_FILE_OVERWRITE
GS_FILE_OVERWRITE = False

