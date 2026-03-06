#!/usr/bin/env python
# ruff: noqa
import os
import sys
from pathlib import Path

if __name__ == "__main__":
    # Load .env.local for local development outside Docker (e.g. uv run manage.py ...).
    # Skip when DJANGO_SETTINGS_MODULE is already set (i.e. inside Docker, where
    # compose provides env vars and .env.local values like CLOUD_SQL_PROXY_HOST=localhost
    # would conflict with the Docker service name).
    env_file = Path(__file__).parent / ".env.local"
    if env_file.exists() and "DJANGO_SETTINGS_MODULE" not in os.environ:
        import environ
        environ.Env.read_env(str(env_file), overwrite=False)

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")

    try:
        from django.core.management import execute_from_command_line
    except ImportError:
        # The above import may fail for some other reason. Ensure that the
        # issue is really that Django is missing to avoid masking other
        # exceptions on Python 2.
        try:
            import django
        except ImportError:
            raise ImportError(
                "Couldn't import Django. Are you sure it's installed and "
                "available on your PYTHONPATH environment variable? Did you "
                "forget to activate a virtual environment?"
            )

        raise

    # This allows easy placement of apps within the interior
    # housegallery directory.
    current_path = Path(__file__).parent.resolve()
    sys.path.append(str(current_path / "housegallery"))

    execute_from_command_line(sys.argv)
