from rest_framework.exceptions import APIException


class ProductNotFoundException(APIException):
    """
    Exception for when a product is not found

    """

    status_code = 404
    default_detail = "Product not found"
    default_code = "product_not_found"


class PolicyNotFoundException(APIException):
    """
    Exception for when a policy is not found

    """

    status_code = 404
    default_detail = "Policy not found"
    default_code = "policy_not_found"


class QuoteNotFoundError(Exception):
    pass


class PremiumCalculationError(Exception):
    pass


class ProductNotFoundError(Exception):
    pass
