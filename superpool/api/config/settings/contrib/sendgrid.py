from config.settings.environment import env

if "SUPERPOOL_ENABLE_SMTP_EMAIL" in env.bool(
    "SUPERPOOL_ENABLE_SMTP_EMAIL", default=False
):
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_HOST = (
        "smtp.sendgrid.net" if not env.str("EMAIL_HOST") else env.str("EMAIL_HOST")
    )
    EMAIL_PORT = 587
    EMAIL_USE_TLS = True if EMAIL_PORT == 587 else False
    EMAIL_HOST_USER = env.str("SENDGRID_USERNAME")
    EMAIL_HOST_PASSWORD = env.str("SENDGRID_PASSWORD")

    DEFAULT_FROM_EMAIL = (
        env.str("DEFAULT_FROM_EMAIL")
        if env.str("DEFAULT_FROM_EMAIL")
        else EMAIL_HOST_USER
    )
else:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
    EMAIL_HOST = "localhost"
    EMAIL_PORT = env.int("EMAIL_PORT", default=1025)
    EMAIL_USE_TLS = False
    EMAIL_HOST_USER = ""
    EMAIL_HOST_PASSWORD = ""
    DEFAULT_FROM_EMAIL = (
        "webmaster@localhost.unyte.com"
        if not env.str("DEFAULT_FROM_EMAIL")
        else env.str("DEFAULT_FROM_EMAIL")
    )
