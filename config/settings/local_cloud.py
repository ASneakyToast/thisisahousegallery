# ruff: noqa: E501
from .base import *  # noqa: F403
from .base import INSTALLED_APPS
from .base import MIDDLEWARE
from .base import WEBPACK_LOADER
from .base import env

# GENERAL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#debug
DEBUG = True
# https://docs.djangoproject.com/en/dev/ref/settings/#secret-key
SECRET_KEY = env("DJANGO_SECRET_KEY")
# https://docs.djangoproject.com/en/dev/ref/settings/#allowed-hosts
ALLOWED_HOSTS = [
    "localhost", 
    "0.0.0.0", 
    "127.0.0.1",
]  # noqa: S104

INTERNAL_IPS = ['127.0.0.1']


# DATABASES
# ------------------------------------------------------------------------------
# Cloud SQL via proxy
DATABASES = {
    "default": env.db(),  # Uses DATABASE_URL environment variable
}
DATABASES["default"]["ATOMIC_REQUESTS"] = True


# GCP Integration
# ------------------------------------------------------------------------------
PROJECT_ID = env("GCP_PROJECT")
BUILD_TYPE = env("BUILD_TYPE")


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