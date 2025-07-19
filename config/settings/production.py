# ruff: noqa: E501
from .base import *  # noqa: F403
from .base import DATABASES
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
    "prod.thisisahousegallery.com",
    "qa.thisisahousegallery.com",
    "housegallery-dev-jrl-service-591747915969.us-west1.run.app"
])


# DATABASES
# ------------------------------------------------------------------------------
DATABASES["default"]["CONN_MAX_AGE"] = env.int("CONN_MAX_AGE", default=300)
DATABASES["default"]["CONN_HEALTH_CHECKS"] = True


# STATIC & MEDIA
# ------------------------
STATIC_ROOT = str(BASE_DIR / "staticfiles")

STORAGES = {
    "default": {
        "BACKEND": "storages.backends.gcloud.GoogleCloudStorage",
        "OPTIONS": {
            "location": "media",
            "file_overwrite": False,
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
