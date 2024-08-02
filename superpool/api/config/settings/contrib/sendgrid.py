import os

from django.conf import settings

from ..environment import env

MAILGUN_ENABLED = env.bool("MAILGUN_ENABLED", default=False)
SENDGRID_ENABLED = env.bool("SENDGRID_ENABLED", default=False)

SUPERPOOL_NS_EMAIL = env("SUPERPOOL_NOTIFICATION_SERVICE_FROM_EMAIL")
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL")

if MAILGUN_ENABLED and SENDGRID_ENABLED:
    raise ValueError(
        "Only one email provider can be enabled at a time. "
        "Both Mailgun and Sendgrid are enabled. Please disable one."
    )

match (settings.DEBUG, MAILGUN_ENABLED, SENDGRID_ENABLED):
    # If DEBUG is True, use the console backend
    case (True, _, _):
        EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
        EMAIL_HOST = "localhost"
        EMAIL_PORT = 1025
        EMAIL_USE_TLS = False
        EMAIL_HOST_USER = ""
        EMAIL_HOST_PASSWORD = ""
        FROM_EMAIL = env("FROM_EMAIL", default="webmaster@localhost")

    # If Mailgun is enabled, use the Mailgun backend
    case (False, True, _):
        EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
        EMAIL_HOST = env("MAILGUN_SMTP_SERVER")
        EMAIL_PORT = 587
        EMAIL_USE_TLS = True
        EMAIL_HOST_USER = env("MAILGUN_EMAIL_USERNAME")
        EMAIL_HOST_PASSWORD = env("MAILGUN_EMAIL_PASSWORD")

    # If Sendgrid is enabled, use Sendgrid backend
    case (False, _, True):
        EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
        EMAIL_HOST = env("EMAIL_HOST", default="tech@unyte.africa")
        EMAIL_HOST_USER = env("EMAIL_HOST_USER")
        EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD")
        EMAIL_USE_TLS = True
        EMAIL_PORT = env("EMAIL_PORT")

    # You fucked up!
    case _:
        raise ValueError(
            "No email provider was configured. Please configure either Sendgird or Mailgun"
        )
