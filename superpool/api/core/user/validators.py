from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator


class BusinessEmailValidator(EmailValidator):
    """
    Validates that the input is a valid business email address.

    The domain of the email address must be one of the following:
    """

    if not hasattr(EmailValidator, "message"):
        message = "Enter a valid business email address."

    def __init__(self, blacklist=[], *args, **kwargs):
        super().__init__(*args, **kwargs)
        blacklist_domains = ["gmail.com", "yahoo.com", "hotmail.com"]
        self.blacklist = blacklist or blacklist_domains

    def validate_domain(self, value):
        domain = value.split("@")[1]
        if domain in self.blacklist:
            raise ValidationError(self.message, code="invalid_business_email")
        return super().validate_domain_part(domain)
