from typing import Any


class MerchantRegistrationError(Exception):
    """
    Raised when an API request cannot successfully create a merchant
    """

    def __init__(self, message: Exception, errors: Any):
        self.message = message
        self.errors = errors


class MerchantNotFound(Exception):
    """
    Raised when an API request cannot successfully find a merchant
    """

    message = "Merchant not found"


class MerchantDeactivationError(Exception):
    """
    Raised when an API request cannot successfully deactivate a merchant
    """

    message = "An error occurred while deactivating the merchant"
