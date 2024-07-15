"""
Settings for Superpool API project

For more information, see https://docs.djangoproject.com/en/5.0/ref/settings
"""

import datetime
import os
import pdb
import pprint
from pathlib import Path

from environ import ImproperlyConfigured, sys  # type: ignore

from .environment import env

BASE_DIR = Path(__file__).resolve().parent.parent

if "SECRET_KEY" in os.environ:
    SECRET_KEY = env.str("SECRET_KEY")
else:
    # TODO: Create a management command that can help users bootstrap
    # SECRET_KEY generation directly from the terminal, in development
    # mode.
    print(
        "Please provide a SECRET_KEY to startup application \n"
        "This can be generated using the helper management command"
    )

DEBUG = env.bool("DJANGO_DEBUG", default=False)

INTERNAL_IPS = env.list("SUPERPOOL_INTERNAL_IPS", default=[])

ALLOWED_HOSTS = [
    "127.0.0.1",
    "localhost",
    "*.unyte.com",
    "https://superpool-v3-dev-ynoamqpukq-uc.a.run.app",
    ".a.run.app",
] + env.list("SUPERPOOL_ALLOWED_HOSTS", default=[])

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party apps
    "rest_framework",
    "drf_spectacular",
    "phonenumber_field",
    "corsheaders",
    "rest_framework_api_key",
    "django_extensions",
    # Local apps
    "core",
    "core.merchants",
    "core.catalog",
    "api",
    "middleware",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    # "middleware.authentication.middleware.APIKeyMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            BASE_DIR.parent / "templates",
        ],
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

# Parses url-like string as database connection urls
# e.g psql://{host}:{port}/{database_name}
# or
# psql://{user}:{pass}@{host}:{port}/{database_name}
# Raises Improperly configured if a database url
# is not provided.

DATABASES = {}
if "DATABASE_URL" in os.environ:
    DATABASES = {
        "default": env.db("DATABASE_URL"),
    }
else:
    try:
        DATABASES = {
            "default": {
                "ENGINE": "django.db.backends.postgresql",
                "NAME": env.str("DATABASE_NAME"),
                "USER": env.str("DATABASE_USER"),
                "PASSWORD": env.str("DATABASE_PASSWORD"),
                "HOST": env.str("DATABASE_HOST"),
                "PORT": env.str("DATABASE_PORT"),
                "CONN_MAX_AGE": env.int("DATABASE_CONN_MAX_AGE", default=500),
            }
        }
        if "DATABASE_OPTIONS" in os.environ:
            DATABASES["default"]["OPTIONS"] = env.dict("DATABASE_OPTIONS", default={})
    except (KeyError, ValueError) as e:
        raise ImproperlyConfigured(
            f"Error loading database configuration: {e} \n",
            "Please provide a DATABASE_URL or DATABASE_NAME, DATABASE_USER, DATABASE_PASSWORD,"
            "DATABASE_HOST, DATABASE_PORT to startup application",
        )

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LANGUAGE_CODE = "en"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True

STATIC_URL = "/static/"
# STATIC_ROOT = BASE_DIR / "staticfiles"
STATIC_ROOT = BASE_DIR.parent / "staticfiles"


MEDIA_URL = "/media/"
# MEDIA_ROOT = BASE_DIR / "mediafiles"
MEDIA_ROOT = BASE_DIR.parent / "mediafiles"


DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

APPEND_SLASH = False

AUTH_USER_MODEL = "core.User"

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": datetime.timedelta(minutes=50),
    "REFRESH_TOKEN_LIFETIME": datetime.timedelta(days=1),
    # "AUTH_HEADER_TYPES": ("Bearer",),
}

CORS_ALLOWED_ORIGINS = [
    "http://localhost",
    "http://127.0.0.1",
    "https://superpool-v3-dev-ynoamqpukq-uc.a.run.app",
]

CORS_ALLOWED_ORIGIN_REGEXES = [
    r"^https://\w+\.a\.run\.app$",
]

# Additional CORS origins or regexes in environment variables
CORS_ALLOWED_ORIGINS += env.list("CORS_ALLOWED_ORIGINS", default=[])
CORS_ALLOWED_ORIGIN_REGEXES += env.list("CORS_ALLOWED_ORIGIN_REGEXES", default=[])

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True


REDIS_ENABLED = env.bool("REDIS_ENABLED")
if REDIS_ENABLED:
    SESSION_ENGINE = "django.contrib.sessions.backends.cache"
    SESSION_CACHE_ALIAS = "default"

    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": env("REDIS_URL"),
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
            },
        }
    }

LOG_LEVEL = env.str("LOG_LEVEL").upper()
# We should dyanmically store logs but keep them under the base directory
LOG_FILE_NAME = env.str("SUPERPOOL_LOG_FILE_NAME", default="superpool.log")
LOG_FILE_PATH = BASE_DIR.parent.parent / "logs" / LOG_FILE_NAME

# Check if a logs directory exists in the parent directory
if not LOG_FILE_PATH.exists():
    # If it doesn't exist, create it
    LOG_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        "file": {
            "class": "logging.FileHandler",
            "filename": LOG_FILE_PATH,
            "formatter": "verbose",
        },
    },
    "formatters": {
        "verbose": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": LOG_LEVEL,
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": LOG_LEVEL,
            "propagate": True,
        },
    },
}

BACKEND_URL = "https://superpool-v3-dev-ynoamqpukq-uc.a.run.app"

# INSURANCE PARTNERS
#
# Heirs Holdings
HEIRS_ASSURANCE_BASE_URL = "https://api.heirsinsurance.com/v1/"
HEIRS_ASSURANCE_STAGING_URL = "https://pubic-api.staging.heirsinsurance.com/v1/"
HEIRS_ASSURANCE_API_KEY = env("HEIRS_API_KEY")
HEIRS_ASSURANCE_APP_ID = env("HEIRS_APP_ID")
