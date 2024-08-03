import os

from django.conf import settings

from ..environment import env
import smtplib
import logging

MAILGUN_ENABLED = env.bool("MAILGUN_ENABLED", default=False)
SENDGRID_ENABLED = env.bool("SENDGRID_ENABLED", default=False)
SUPERPOOL_NS_EMAIL = env("SUPERPOOL_NOTIFICATION_SERVICE_FROM_EMAIL")
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL")


# Common properties for all email providers
EMAIL_USE_TLS = env("EMAIL_USE_TLS", default=True)
EMAIL_USE_SSL = env("EMAIL_USE_SSL", default=False)

if MAILGUN_ENABLED and SENDGRID_ENABLED:
    raise ValueError(
        "Only one email provider can be enabled at a time. "
        "Both Mailgun and Sendgrid are enabled. Please disable one."
    )

try:
    match (settings.DEBUG, MAILGUN_ENABLED, SENDGRID_ENABLED):
        # If DEBUG is True, use the console backend
        case (True, _, _):
            EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
            EMAIL_HOST = "localhost"
            EMAIL_PORT = 1025
            EMAIL_USE_TLS = False
            EMAIL_HOST_USER = ""
            EMAIL_HOST_PASSWORD = ""

        # If Mailgun is enabled, use the Mailgun backend
        case (False, True, _):
            EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
            EMAIL_HOST = env("MAILGUN_SMTP_SERVER")
            EMAIL_PORT = env.int("MAILGUN_EMAIL_PORT")
            EMAIL_HOST_USER = env("MAILGUN_EMAIL_USERNAME")
            EMAIL_HOST_PASSWORD = env("MAILGUN_EMAIL_PASSWORD")
            EMAIL_USE_TLS = False
            EMAIL_USE_SSL = True

        # If Sendgrid is enabled, use Sendgrid backend
        case (False, _, True):
            EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
            EMAIL_HOST = env("EMAIL_HOST", default="tech@unyte.africa")
            EMAIL_PORT = env.int("EMAIL_PORT")
            EMAIL_HOST_USER = env("EMAIL_HOST_USER")
            EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD")
            EMAIL_USE_TLS = EMAIL_USE_TLS
            EMAIL_USE_SSL = EMAIL_USE_SSL

        # You fucked up!
        case _:
            # Try using GMAIL if it exist in the configuration otherwise, revolt!
            EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
            EMAIL_HOST = env("GOOGLE_SMTP_SERVER")
            EMAIL_PORT = 465
            EMAIL_HOST_USER = env("GOOGLE_EMAIL_USER")
            EMAIL_HOST_PASSWORD = env("GOOGLE_EMAIL_PASSWORD")
            EMAIL_USE_SSL = env.bool("GOOGLE_EMAIL_USE_SSL", default=True)
            EMAIL_USE_TLS = env.bool("GOOGLE_EMAIL_USE_TLS", default=False)


except KeyError as keyerr:
    raise Exception(f"Missing required configuration for the email provider: {keyerr}")
except smtplib.SMTPConnectError as e:
    logging.error(f"SMTP connection error: {e}")
    raise
except smtplib.SMTPAuthenticationError as e:
    logging.error(f"SMTP authentication error: {e}")
    raise
except smtplib.SMTPException as e:
    logging.error(f"SMTP error: {e}")
    raise

# at any point in time our default sending email should point to our local-host
# not that anyone would forget this though, but rather stay safe, than sory
if not DEFAULT_FROM_EMAIL:
    DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="webmaster@localhost")

# raise ValueError(
#     "No email provider was configured. Please configure either Sendgird or Mailgun"
# )
