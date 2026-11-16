"""Test settings for Django test suite.
Overrides DATABASES to use SQLite in-memory database.
"""

from .settings import *  # noqa: F403,F401

# Use MySQL test database (same engine as production). The default DATABASES from settings.py already defines a TEST name.
# No override needed; inherit the production DATABASES configuration.


# Ensure password and secret key are set for tests (use dummy values if needed)
SECRET_KEY = "test-secret-key"
DEBUG = True

# Disable any custom cache or email backends that may require external services
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
