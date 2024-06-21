from django.core.exceptions import ObjectDoesNotExist


class MerchantDoesNotExist(ObjectDoesNotExist):
    """
    Raised when a merchant does not exist in the database
    """

    message = "Merchant does not exisit"


class MerchantAlreadyExists(Exception):
    """
    Raised when a merchant already exists in the database
    """

    message = "This Merchant already exisit in the database"


class MerchantAccountDeactivated(Exception):
    """
    Raised when a merchant is deactivated
    """

    message = "The provided merchant has been deactivated from the platform"


class InvalidMerchantCredentials(Exception):
    """
    Raised when invalid merchant credentials are provided
    """

    message = "Invalid merchant credential details, please provide valid credentials"
