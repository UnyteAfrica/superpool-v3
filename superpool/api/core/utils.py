from core.merchants.models import Merchant


def generate_verification_token(self, merchant: Merchant) -> str:
    """
    Generates a verification token for email verification
    """
    from django.contrib.auth.tokens import default_token_generator

    return default_token_generator.make_token(merchant)


def send_verification_email(self, merchant: Merchant, token: str):
    """
    Sends an email to the merchant to verify their email address
    """
    from core.emails import PendingVerificationEmail
    from django.conf import settings

    CONFIRMATION_URL = f"{settings.BACKEND_URL}/verify-email?token={token}"

    email = PendingVerificationEmail(confirm_url=CONFIRMATION_URL)
    email.send()
