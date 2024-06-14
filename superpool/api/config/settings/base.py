"""
Settings for Superpool API project

For more information, see https://docs.djangoproject.com/en/5.0/ref/settings
"""

import os
from pathlib import Path

from django.contrib.admin.filters import datetime

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

ALLOWED_HOSTS = ["127.0.0.1", "localhost", "*.run.app"] + env.list(
    "SUPERPOOL_ALLOWED_HOSTS"
)

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
    # Local apps
    "core",
    "api",
    "api.user",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
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
    DATABASES["default"]["ENGINE"] = ("django.db.backends.postgresql",)
    DATABASES["default"]["NAME"] = env.str("DATABASE_NAME", default="superpool")
    DATABASES["default"]["USER"] = env.str("DATABASE_USER", default="superpool")
    DATABASES["default"]["PASSWORD"] = env.str("DATABASE_PASSWORD", default="superpool")
    DATABASES["default"]["HOST"] = env.str("DATABASE_HOST")
    DATABASES["default"]["PORT"] = env.str("DATABASE_PORT")

    if "DATABASE_OPTIONS" in os.environ:
        DATABASES["default"]["OPTIONS"] = env.dict("DATABASE_OPTIONS", default={})

    DATABASES["default"]["CONN_MAX_AGE"] = env.int("DATABASE_CONN_MAX_AGE", default=500)


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
STATIC_ROOT = BASE_DIR / "static"

MEDIA_URL = "/ls/files/"
MEDIA_ROOT = BASE_DIR / "uploads"


DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

APPEND_SLASH = False

AUTH_USER_MODEL = "core.User"

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": datetime.timedelta(minutes=5),
    "REFRESH_TOKEN_LIFETIME": datetime.timedelta(days=1),
    "AUTH_HEADER_TYPES": ("Bearer",),
}

CORS_ALLOWED_ORIGIN = [
    "http://localhost",
    "127.0.0.1",
    "https://superpool-v3-dev-ynoamqpukq-uc.a.run.app",
] + env("SUPERPOOL_ALLOWED_HOSTS")
CORS_ALLOWED_ORIGIN_REGEXES = [""].extend(env.str("SUPERPOOL_ALLOWED_ORIGIN_REGEXES"))
