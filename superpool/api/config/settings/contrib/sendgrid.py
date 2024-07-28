import os

from django.conf import settings

from ..environment import env

if settings.DEBUG:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
    EMAIL_HOST = "localhost"
    EMAIL_PORT = env.int("EMAIL_PORT", default=1025)
    EMAIL_USE_TLS = False
    EMAIL_HOST_USER = ""
    EMAIL_HOST_PASSWORD = ""
    FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="webmaster@localhost.unyte.com")

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = env("EMAIL_HOST", default="smtp.sendgrid.net")
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = "apikey"
EMAIL_HOST_PASSWORD = env("SENDGRID_API_KEY")

FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="tech@unyte.com")
DEFAULT_FROM_EMAIL = FROM_EMAIL
