import functools
import hashlib
import random
import string
import uuid
from typing import Callable, Optional

from django.conf import settings

from .emails import PendingVerificationEmail

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
    prefix = class_name[:3].title()  # First 3 characters of the class name in lowercase

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


def cache_key_generator(*args, **kwargs):
    """
    Generates a cache key for a given set of arguments
    """
    return (
        "_".join(map(str, args)) + "_" + "_".join(f"{k}={v}" for k, v in kwargs.items())
    )


def cache_result(timeout: int = 60, cache_key_func: Optional[Callable] = None):
    """
    Caches the result of a function call, view (Django view function) or (Django view class)
    """
    from django.core.cache import cache

    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if cache_key_func:
                cache_key = cache_key_func(*args, **kwargs)
            else:
                cache_key = f"{func.__module__}:{func.__name__}:{args}:{kwargs}"

            result = cache.get(cache_key)
            if result is None:
                result = func(*args, **kwargs)
                cache.set(cache_key, result, timeout)

            return result

        return wrapper

    return decorator
