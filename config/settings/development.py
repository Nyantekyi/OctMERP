"""
config/settings/development.py
"""

from .base import *  # noqa

DEBUG = True

INSTALLED_APPS += [  # noqa
    "debug_toolbar",
]

MIDDLEWARE += [  # noqa
    "debug_toolbar.middleware.DebugToolbarMiddleware",
]

INTERNAL_IPS = ["127.0.0.1"]

# Use console email backend in development
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Relax CORS in dev
CORS_ALLOW_ALL_ORIGINS = True
