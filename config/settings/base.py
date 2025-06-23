"""
Django settings for thisisahousegallery.com.

Referenced:
- https://cloud.google.com/python/django/run
- https://github.com/cookiecutter/cookiecutter-django
- https://github.com/cca/cca-edu
"""

from pathlib import Path

import io
import json
import os
from urllib.parse import urlparse

import environ
from google.cloud import secretmanager

env = environ.Env()

BASE_DIR = Path(__file__).resolve(strict=True).parent.parent.parent
APPS_DIR = BASE_DIR / "housegallery"


# GENERAL
# ------------------------------------------------------------------------------
DEBUG = env.bool("DJANGO_DEBUG", False)
TIME_ZONE = "UTC"
LANGUAGE_CODE = "en-us"
SITE_ID = 1
USE_I18N = True
USE_TZ = True
LOCALE_PATHS = [str(BASE_DIR / "locale")]

APP_NAME = env('APP_NAME', default='housegallery')


# Basic configuration
# ---------------------------------------------------------------------------------------
if 'PRIMARY_HOST' in env:
    WAGTAILADMIN_BASE_URL = 'https://%s' % env['PRIMARY_HOST']

if 'CACHE_PURGE_URL' in env:
    INSTALLED_APPS += ('wagtail.contrib.frontend_cache', )  # noqa
    WAGTAILFRONTENDCACHE = {
        'default': {
            'BACKEND': 'wagtail.contrib.frontend_cache.backends.HTTPBackend',
            'LOCATION': env('CACHE_PURGE_URL'),
        },
    }

if env('PREPEND_WWW', default='false').lower().strip() == 'true':
    PREPEND_WWW = True


# SECRETS & GCP
# ------------------------------------------------------------------------------
# Only load GCP secrets for production/staging environments
django_settings = os.environ.get("DJANGO_SETTINGS_MODULE", "")
if django_settings not in ["config.settings.local", "config.settings.local_offline"]:
    if 'SECRET_KEY' in env:
        SECRET_KEY = env('SECRET_KEY')

    # Attempt to load the Project ID or Build Type from env
    PROJECT_ID = os.environ.get("GCP_PROJECT")
    BUILD_TYPE = os.environ.get("BUILD_TYPE")
    if not PROJECT_ID or not BUILD_TYPE:
        raise Exception("No GCP_PROJECT or BUILD_TYPE. Exit")

    # [START cloudrun_django_secret_config]
    def get_secret(project_id, client, secret_name):
        secret = f"projects/{project_id}/secrets/{secret_name}/versions/latest"
        payload = client.access_secret_version(name=secret).payload.data.decode("UTF-8")
        return io.StringIO(payload)

    # Pull conf from Secret Manager
    client = secretmanager.SecretManagerServiceClient()
    env.read_env(get_secret(PROJECT_ID, client, 'housegallery-settings'))
    # [END cloudrun_django_secret_config]


# DATABASES
# ------------------------------------------------------------------------------
# For production/staging environments
if django_settings not in ["config.settings.local", "config.settings.local_offline"]:
    DATABASES = {
        "default": env.db(),    # Raises ImproperlyConfigured expection if DATABASE_URL not in os.env
    }
    DATABASES["default"]["NAME"] = f'housegallery-{BUILD_TYPE}'
    DATABASES["default"]["ATOMIC_REQUESTS"] = True
else:
    # Local development database configuration
    # This will be overridden in local.py for local Postgres
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": "housegallery",
            "USER": "admin",
            "PASSWORD": "password",
            "HOST": "postgres",
            "PORT": "5432",
            "ATOMIC_REQUESTS": True,
        }
    }

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# [START cloudrun_django_csrf]
# SECURITY WARNING: It's recommended that you use this when
# running in production. The URL will be known once you first deploy
# to Cloud Run. This code takes the URL and converts it to both these settings formats.
CLOUDRUN_SERVICE_URL = env("CLOUDRUN_SERVICE_URL", default=None)
if CLOUDRUN_SERVICE_URL:
    ALLOWED_HOSTS = [urlparse(CLOUDRUN_SERVICE_URL).netloc]
    CSRF_TRUSTED_ORIGINS = [CLOUDRUN_SERVICE_URL]
    SECURE_SSL_REDIRECT = True
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
else:
    ALLOWED_HOSTS = ["*"]
# [END cloudrun_django_csrf]


# URLS
# ------------------------------------------------------------------------------
ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"


# APPS
# ------------------------------------------------------------------------------
DJANGO_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.sites",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.admin",
    "django.forms",
]

WAGTAIL_APPS = [
    'wagtail.contrib.forms',
    'wagtail.contrib.redirects',
    'wagtail.contrib.settings',
    'wagtail.embeds',
    'wagtail.sites',
    'wagtail.users',
    'wagtail.snippets',
    'wagtail.documents',
    'wagtail.images',
    'wagtail.search',
    'wagtail.admin',
    'wagtail',
]

THIRD_PARTY_APPS = [
    "modelcluster",
    "taggit",
    "crispy_forms",
    "crispy_bootstrap5",
    "rest_framework",
    "rest_framework.authtoken",
    "corsheaders",
    "drf_spectacular",
    "webpack_loader",
]

GOOGLE_APPS = [
    'storages',
]

LOCAL_APPS = [
    "housegallery.artists",
    "housegallery.artworks",
    "housegallery.core",
    "housegallery.exhibitions",
    "housegallery.home",
    "housegallery.images",
]

INSTALLED_APPS = DJANGO_APPS + WAGTAIL_APPS + THIRD_PARTY_APPS + LOCAL_APPS + GOOGLE_APPS


# MIGRATIONS
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#migration-modules
MIGRATION_MODULES = {"sites": "housegallery.contrib.sites.migrations"}


# AUTHENTICATION
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/1.9/ref/settings/#auth-password-validators
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator', },
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', },
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator', },
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator', },
]


# PASSWORDS
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#password-hashers
PASSWORD_HASHERS = [
    # https://docs.djangoproject.com/en/dev/topics/auth/passwords/#using-argon2-with-django
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
    "django.contrib.auth.hashers.BCryptSHA256PasswordHasher",
]
# https://docs.djangoproject.com/en/dev/ref/settings/#auth-password-validators
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# MIDDLEWARE
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#middleware
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "wagtail.contrib.redirects.middleware.RedirectMiddleware",
]


# MEDIA & STATIC
# ------------------------------------------------------------------------------
# MEDIA_ROOT not used for GSB setup for django-storage
MEDIA_URL = "/media/"

# Static files

STATICFILES_DIRS = [str(APPS_DIR / "static_src")]
STATICFILES_FINDERS = [
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
]
# STATIC_ROOT is not used for GSB setup for django-storage
# STATIC_ROOT = str(BASE_DIR / "staticfiles")
STATIC_URL = "/static/"

# [START cloudrun_django_static_config]
# Define static storage via django-storages[google]
GS_DEFAULT_ACL = "publicRead"
BUILD_TYPE = env('BUILD_TYPE', default='dev')
GS_BUCKET_NAME = f"housegallery-{BUILD_TYPE}"

STORAGES = {
    "default": {
        "BACKEND": "storages.backends.gcloud.GoogleCloudStorage",
        "OPTIONS": {
            "location": "media",
        },
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        "OPTIONS": {
            "location": "static",
        },
    },
}

# [END local staticfiles]


# WAGTAIL settings
# ---------------------------------------------------------------------------------------
WAGTAIL_SITE_NAME = "This is a House Gallery"

WAGTAILDOCS_DOCUMENT_MODEL = "wagtaildocs.Document"

WAGTAILIMAGES_IMAGE_MODEL = "images.CustomImage"
WAGTAILIMAGES_FEATURE_DETECTION_ENABLED = False

# Allows to change the max size of the image that user can upload. Defaults to 6MB
WAGTAILIMAGES_MAX_UPLOAD_SIZE = 6 * 1024 * 1024

WAGTAILIMAGES_EXTENSIONS = ["gif", "jpg", "jpeg", "png", "webp", "svg"]

WAGTAILADMIN_RICH_TEXT_EDITORS = {
    'default': {
        'WIDGET': 'wagtail.admin.rich_text.DraftailRichTextArea',
        'OPTIONS': {
            'features': ['bold', 'italic', 'h3', 'h4', 'ol', 'ul', 'link', 'document-link', 'strikethrough']
        }
    },
    'captions': {
        'WIDGET': 'wagtail.admin.rich_text.DraftailRichTextArea',
        'OPTIONS': {
            'features': ['bold', 'italic', 'link', 'document-link', 'strikethrough']
        }
    },
}

WAGTAIL_MODERATION_ENABLED = False

WAGTAIL_PASSWORD_REQUIRED_TEMPLATE = 'password_required.html'

DEFAULT_PER_PAGE = 20


# TEMPLATES
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#templates
TEMPLATES = [
    {
        # https://docs.djangoproject.com/en/dev/ref/settings/#std:setting-TEMPLATES-BACKEND
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        # https://docs.djangoproject.com/en/dev/ref/settings/#dirs
        "DIRS": [str(APPS_DIR / "templates")],
        # https://docs.djangoproject.com/en/dev/ref/settings/#app-dirs
        "APP_DIRS": True,
        "OPTIONS": {
            # https://docs.djangoproject.com/en/dev/ref/settings/#template-context-processors
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.template.context_processors.i18n",
                "django.template.context_processors.media",
                "django.template.context_processors.static",
                "django.template.context_processors.tz",
                "django.contrib.messages.context_processors.messages",
                'wagtail.contrib.settings.context_processors.settings',
            ],
        },
    },
]

# TODO: Check if I can get rid of these three vars
# https://docs.djangoproject.com/en/dev/ref/settings/#form-renderer
FORM_RENDERER = "django.forms.renderers.TemplatesSetting"

# http://django-crispy-forms.readthedocs.io/en/latest/install.html#template-packs
CRISPY_TEMPLATE_PACK = "bootstrap5"
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"


# FIXTURES
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#fixture-dirs
FIXTURE_DIRS = (str(APPS_DIR / "fixtures"),)


# EMAIL
# ---------------------------------------------------------------------------------------
if 'EMAIL_HOST' in env:
    EMAIL_HOST = env('EMAIL_HOST')

if 'EMAIL_PORT' in env:
    try:
        EMAIL_PORT = int(env('EMAIL_PORT'))
    except ValueError:
        pass

if 'EMAIL_HOST_USER' in env:
    EMAIL_HOST_USER = env('EMAIL_HOST_USER')

if 'EMAIL_HOST_PASSWORD' in env:
    EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD')

if env('EMAIL_USE_TLS', default='false').lower().strip() == 'true':
    EMAIL_USE_TLS = True

if env('EMAIL_USE_SSL', default='false').lower().strip() == 'true':
    EMAIL_USE_SSL = True

if 'EMAIL_SUBJECT_PREFIX' in env:
    EMAIL_SUBJECT_PREFIX = env('EMAIL_SUBJECT_PREFIX')

if 'SERVER_EMAIL' in env:
    SERVER_EMAIL = DEFAULT_FROM_EMAIL = env('SERVER_EMAIL')


# ADMIN
# ------------------------------------------------------------------------------
# Django Admin URL.
ADMIN_URL = "admin/"
# https://docs.djangoproject.com/en/dev/ref/settings/#admins
ADMINS = [("""Joel Lithgow""", "joel-lithgow@thisisahousegallery.com")]
# https://docs.djangoproject.com/en/dev/ref/settings/#managers
MANAGERS = ADMINS


# SECURITY
# ---------------------------------------------------------------------------------------
# This configuration is required to achieve good security rating.
# You can test it using https://securityheaders.com/
# https://docs.djangoproject.com/en/stable/ref/middleware/#module-django.middleware.security

# Force HTTPS redirect
# https://docs.djangoproject.com/en/stable/ref/settings/#secure-ssl-redirect
SECURE_SSL_REDIRECT = env('SECURE_SSL_REDIRECT', default='true').strip().lower() == 'true'
# If SECURE_SSL_REDIRECT == True, we need to exclude monitoring URLs from
# from redirection to allow Google Cloud Load Balancer perform health checks
# Has not effect when SECURE_SSL_REDIRECT == False
SECURE_REDIRECT_EXEMPT = [
    '^healthz/$'
]

# This will allow the cache to swallow the fact that the website is behind TLS
# and inform the Django using "X-Forwarded-Proto" HTTP header.
# https://docs.djangoproject.com/en/stable/ref/settings/#secure-proxy-ssl-header
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# https://docs.djangoproject.com/en/stable/ref/settings/#secure-browser-xss-filter
SECURE_BROWSER_XSS_FILTER = env('SECURE_BROWSER_XSS_FILTER', default='true').lower().strip() == 'true'

# https://docs.djangoproject.com/en/stable/ref/settings/#secure-content-type-nosniff
SECURE_CONTENT_TYPE_NOSNIFF = env('SECURE_CONTENT_TYPE_NOSNIFF', default='true').lower().strip() == 'true'

# This is a setting setting HSTS header. This will enforce the visitors to use
# HTTPS for an amount of time specified in the header. Please make sure you
# consult with sysadmin before setting this.
# https://docs.djangoproject.com/en/stable/ref/settings/#secure-hsts-seconds
if 'SECURE_HSTS_SECONDS' in env:
    SECURE_HSTS_SECONDS = int(env('SECURE_HSTS_SECONDS'))

# Content Security policy settings
# http://django-csp.readthedocs.io/en/latest/configuration.html
if 'CSP_DEFAULT_SRC' in env:
    MIDDLEWARE.append('csp.middleware.CSPMiddleware')

    # The “special” source values of 'self', 'unsafe-inline', 'unsafe-eval', and 'none' must be quoted!
    # e.g.: CSP_DEFAULT_SRC = "'self'" Without quotes they will not work as intended.

    CSP_DEFAULT_SRC = env('CSP_DEFAULT_SRC').split(',')
    if 'CSP_SCRIPT_SRC' in env:
        CSP_SCRIPT_SRC = env('CSP_SCRIPT_SRC').split(',')
    if 'CSP_STYLE_SRC' in env:
        CSP_STYLE_SRC = env('CSP_STYLE_SRC').split(',')
    if 'CSP_IMG_SRC' in env:
        CSP_IMG_SRC = env('CSP_IMG_SRC').split(',')
    if 'CSP_CONNECT_SRC' in env:
        CSP_CONNECT_SRC = env('CSP_CONNECT_SRC').split(',')

# Referrer-policy header settings
# https://django-referrer-policy.readthedocs.io/en/1.0/
REFERRER_POLICY = env('SECURE_REFERRER_POLICY', default='no-referrer-when-downgrade').strip()


# LOGGING
# ------------------------------------------------------------------------------
# See: https://docs.djangoproject.com/en/dev/ref/settings/#logging
# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See https://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.

# only output log to stdout on GCP
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'structured': {
            'format': json.dumps({
                "date": "%(asctime)s",
                "level": "%(levelname)s",
                "name": "%(name)s:%(lineno)s",
                "process": "%(process)d",
                "thread": "%(thread)d",
                "message": "%(message)s"}),
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'stream': 'ext://sys.stdout',
            'formatter': 'structured',
        },
    },
    'loggers': {
        '': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        }
    }
}


# django-rest-framework
# -------------------------------------------------------------------------------
# django-rest-framework - https://www.django-rest-framework.org/api-guide/settings/
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.TokenAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

# django-cors-headers - https://github.com/adamchainz/django-cors-headers#setup
CORS_URLS_REGEX = r"^/api/.*$"

# By Default swagger ui is available only to admin user(s). You can change permission classes to change that
# See more configuration options at https://drf-spectacular.readthedocs.io/en/latest/settings.html#settings
SPECTACULAR_SETTINGS = {
    "TITLE": "housegallery API",
    "DESCRIPTION": "Documentation of API endpoints of housegallery",
    "VERSION": "1.0.0",
    "SERVE_PERMISSIONS": ["rest_framework.permissions.IsAdminUser"],
    "SCHEMA_PATH_PREFIX": "/api/",
}
# django-webpack-loader
# ------------------------------------------------------------------------------
WEBPACK_LOADER = {
    "DEFAULT": {
        "CACHE": not DEBUG,
        "STATS_FILE": BASE_DIR / "webpack-stats.json",
        "POLL_INTERVAL": 0.1,
        "IGNORE": [r".+\.hot-update.js", r".+\.map"],
    },
}
