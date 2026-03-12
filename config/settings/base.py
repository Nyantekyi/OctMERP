"""
config/settings/base.py

Shared settings inherited by development.py, production.py, and testing.py.
"""

import os
from pathlib import Path
from decouple import config, Csv

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# ── Security ─────────────────────────────────────────────────────────────────
SECRET_KEY = config("SECRET_KEY")
DEBUG = config("DEBUG", default=False, cast=bool)
ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="localhost,127.0.0.1", cast=Csv())

# ── Application definition ───────────────────────────────────────────────────
SHARED_APPS = [
    # django-tenants must be first
    "django_tenants",

    # Django builtins that live in the public schema
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django.contrib.admin",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Third-party (public-schema)
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "drf_spectacular",
    "simple_history",
    "auditlog",

    # Public-schema ERP apps
    "apps.company",   # Company (TenantMixin) + Domain lives here
]

TENANT_APPS = [
    # Django builtins replicated per tenant
    "django.contrib.contenttypes",
    "django.contrib.auth",

    # Third-party (per-tenant)
    "django_filters",
    "simple_history",
    "auditlog",

    # ERP tenant apps
    "apps.common",
    "apps.party",
    "apps.contact",
    "apps.department",
    "apps.hr",
    "apps.accounting",
    "apps.inventory",
    "apps.invplan",
    "apps.workflow",
    "apps.procurement",
    "apps.sales",
    "apps.crm",
    "apps.ecommerce",
    "apps.pos",
    "apps.manufacturing",
    "apps.logistics",
    "apps.assets",
    "apps.projects",
    "apps.reporting",
    "apps.notifications",
    "apps.agents",
]

INSTALLED_APPS = list(SHARED_APPS) + [app for app in TENANT_APPS if app not in SHARED_APPS]

# ── django-tenants ────────────────────────────────────────────────────────────
TENANT_MODEL = "company.Company"
TENANT_DOMAIN_MODEL = "company.Domain"

# ── Middleware ────────────────────────────────────────────────────────────────
MIDDLEWARE = [
    "django_tenants.middleware.main.TenantMainMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "auditlog.middleware.AuditlogMiddleware",
    "simple_history.middleware.HistoryRequestMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# ── Database ─────────────────────────────────────────────────────────────────
DATABASES = {
    "default": {
        "ENGINE": "django_tenants.postgresql_backend",
        "NAME": config("DB_NAME", default="erp_db"),
        "USER": config("DB_USER", default="postgres"),
        "PASSWORD": config("DB_PASSWORD", default=""),
        "HOST": config("DB_HOST", default="localhost"),
        "PORT": config("DB_PORT", default="5432"),
    }
}
DATABASE_ROUTERS = ["django_tenants.routers.TenantSyncRouter"]

# ── Authentication ────────────────────────────────────────────────────────────
AUTH_USER_MODEL = "party.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ── REST Framework ────────────────────────────────────────────────────────────
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_PAGINATION_CLASS": "apps.common.pagination.StandardResultsPagination",
    "PAGE_SIZE": 25,
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "EXCEPTION_HANDLER": "apps.common.exceptions.erp_exception_handler",
}

# ── SimpleJWT ─────────────────────────────────────────────────────────────────
from datetime import timedelta

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "ALGORITHM": "HS256",
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# ── drf-spectacular (OpenAPI) ─────────────────────────────────────────────────
SPECTACULAR_SETTINGS = {
    "TITLE": "ERP API",
    "DESCRIPTION": "Multi-tenant ERP REST API",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

# ── CORS ─────────────────────────────────────────────────────────────────────
CORS_ALLOWED_ORIGINS = config("CORS_ALLOWED_ORIGINS", default="http://localhost:3000", cast=Csv())
CORS_ALLOW_CREDENTIALS = True

# ── Channels (WebSockets) ────────────────────────────────────────────────────
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [(config("REDIS_HOST", default="127.0.0.1"), 6379)],
        },
    },
}

# ── Celery ────────────────────────────────────────────────────────────────────
CELERY_BROKER_URL = config("CELERY_BROKER_URL", default="redis://127.0.0.1:6379/0")
CELERY_RESULT_BACKEND = config("CELERY_RESULT_BACKEND", default="redis://127.0.0.1:6379/0")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "Africa/Accra"
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"

# ── Cache ─────────────────────────────────────────────────────────────────────
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": config("REDIS_URL", default="redis://127.0.0.1:6379/1"),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
    }
}

# ── Internationalisation ──────────────────────────────────────────────────────
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Africa/Accra"
USE_I18N = True
USE_TZ = True

# ── Static / Media ────────────────────────────────────────────────────────────
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# ── Default primary key ───────────────────────────────────────────────────────
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ── django-money ─────────────────────────────────────────────────────────────
DEFAULT_CURRENCY = "GHS"

# ── Simple History ────────────────────────────────────────────────────────────
SIMPLE_HISTORY_REVERT_DISABLED = False

# ── Auditlog ─────────────────────────────────────────────────────────────────
AUDITLOG_INCLUDE_ALL_MODELS = True

# ── Logging ───────────────────────────────────────────────────────────────────
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "WARNING",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": config("DJANGO_LOG_LEVEL", default="INFO"),
            "propagate": False,
        },
        "apps": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
}
