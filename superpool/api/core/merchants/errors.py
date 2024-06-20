class MerchantDoesNotExist(Exception):
    """
    Raised when a merchant does not exist in the database
    """

    pass


class MerchantAlreadyExists(Exception):
    """
    Raised when a merchant already exists in the database
    """

    pass


class MerchantAlreadyDeactivatedError(Exception):
    """
    Raised when a merchant is deactivated
    """

    pass


class InvalidMerchantCredentials(Exception):
    """
    Raised when invalid merchant credentials are provided
    """

    pass
