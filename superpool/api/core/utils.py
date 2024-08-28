import random
import string
import uuid
from .emails import PendingVerificationEmail
from django.conf import settings
import hashlib

from core.merchants.models import Merchant

DEFAULT_FROM_EMAIL = settings.DEFAULT_FROM_EMAIL
BASE_URL = settings.BASE_URL


def generate_verification_token() -> str:
    """
    Generates a verification token for email verification
    """
    return "".join(random.choices(string.ascii_letters + string.digits, k=6))


def send_verification_email(
    email: str, token: str, merchant_id: str, merchant_name: str | None = None
) -> None:
    """
    Sends an email to the merchant to verify their email address
    """

    CONFIRMATION_URL = f"{BASE_URL}/merchants/{merchant_id}/verify/?token={token}"

    verification_email = PendingVerificationEmail(
        merchant_name=merchant_name,
        confirm_url=CONFIRMATION_URL,
        to=email,
        from_=DEFAULT_FROM_EMAIL,
        token=token,
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


def generate_tenant_id():
    """
    Generates a tenant ID for a merchant

    The tenant ID is a unique identifier for a merchant that is used to
    identify the merchant in the system during request calls.
    """
    prefix = "SUPERPOOL"
    hsahlib = hashlib.sha256().hexdigest().upper()
    return f"{prefix}_{hsahlib}"
