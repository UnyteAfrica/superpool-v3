import uuid

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


def generate_id(klass):
    """
    Performant ID generator that generates memory-efficient, unique idenifiers
    for objects
    """
    class_name = klass
    prefix = class_name[:3].lower().encode("utf-8")
    suffix = uuid.uuid4().hex[:16].encode("utf-8")
    # print(f"Prefix: {prefix}")
    # print(f"Suffix: {suffix}")
    return f"{prefix.decode()}_{suffix.decode()}"
