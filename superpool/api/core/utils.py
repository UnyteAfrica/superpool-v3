from core.merchants.models import Merchant


def generate_verification_token() -> str:
    """
    Generates a verification token for email verification
    """
    import random
    import string

    return random.choice(
        [
            "".join(random.choices(string.ascii_letters + string.digits, k=1))
            for _ in range(6)
        ]
    )


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
