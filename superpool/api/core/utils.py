import random
import string
import uuid

from core.merchants.models import Merchant


def generate_verification_token() -> str:
    """
    Generates a verification token for email verification
    """
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
    # The logic here is to take a class name, append some random string values to it
    # and str converted UUID suffix (the first block of UUIDs) - totalling upto 18 characters
    #
    # The length of the generated ID will be 17 characters (3 + 1 + 5 + 1 + 8)

    class_name = klass.__name__
    prefix = class_name[:3].lower()  # First 3 characters of the class name in lowercase

    # random string of 5 characters
    random_str = "".join(random.choices(string.ascii_lowercase + string.digits, k=5))

    # first 8 characters of a UUID (this is actually 4 bytes)
    uuid_suffix = uuid.uuid4().hex[:8]
    unique_id = f"{prefix}_{random_str}_{uuid_suffix}"
    return unique_id
