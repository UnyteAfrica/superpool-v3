from core.merchants.models import Merchant


def generate_verification_token() -> str:
    """
    Generates a verification token for email verification
    """
    from django.contrib.auth.tokens import default_token_generator

    return default_token_generator.make_token()


def send_verification_email(email: str, token: str) -> None:
    """
    Sends an email to the merchant to verify their email address
    """
    from core.emails import PendingVerificationEmail
    from django.conf import settings

    CONFIRMATION_URL = f"{settings.BACKEND_URL}/verify-email?token={token}"

    verification_email = PendingVerificationEmail(
        confirm_url=CONFIRMATION_URL, to=email, from_=settings.FROM_EMAIL
    )
    verification_email.send()
