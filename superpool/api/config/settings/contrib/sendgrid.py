import os

from django.conf import settings

from ..environment import env

if "SUPERPOOL_ENABLE_SMTP_EMAIL" in os.environ:
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_HOST = (
        "smtp.sendgrid.net" if not env.str("EMAIL_HOST") else env.str("EMAIL_HOST")
    )
    EMAIL_PORT = 587 if not env.int("EMAIL_PORT") else env.int("EMAIL_PORT")
    EMAIL_USE_TLS = True if EMAIL_PORT == 587 else False
    EMAIL_HOST_USER = env.str("EMAIL_HOST_USER")
    EMAIL_HOST_PASSWORD = env.str("EMAIL_HOST_PASSWORD")

    if "SENDGRID_API_KEY" in env:
        SENDGRID_API_KEY = env.str("SENDGRID_API_KEY")

    FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="noreply@unyte.com")

if settings.DEBUG:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
    EMAIL_HOST = "localhost"
    EMAIL_PORT = env.int("EMAIL_PORT", default=1025)
    EMAIL_USE_TLS = False
    EMAIL_HOST_USER = ""
    EMAIL_HOST_PASSWORD = ""
    DEFAULT_FROM_EMAIL = (
        "webmaster@localhost.unyte.com"
        if not env("DEFAULT_FROM_EMAIL")
        else env("DEFAULT_FROM_EMAIL")
    )
