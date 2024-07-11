import logging

from core.models import APIKey, Application
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

logger = logging.getLogger(__name__)


class APIKeyAuthentication(BaseAuthentication):
    """
    Custom authentication class to authenticate requests based on X-APP-ID header
    and return the merchant object
    """

    def authenticate(self, request):
        # Get both the X-APP-ID and API-KEY headers
        x_app_id = request.headers.get("X-APP-ID")
        key = request.headers.get("API-KEY")

        # If X-APP-ID header is not present, return None
        if not x_app_id and not key:
            return None

        try:
            app = Application.objects.get(application_id=x_app_id)
            apikey_obj = APIKey.objects.select_related("merchant").get(key=key)

        except Application.DoesNotExist:
            raise AuthenticationFailed("Invalid X-APP-ID")
        except APIKey.DoesNotExist:
            raise AuthenticationFailed("Invalid API Key")

        if not (apikey_obj.merchant.short_code == app.merchant.short_code):
            raise Exception("Merchant Objects are not the same")

        return (app.merchant, apikey_obj, None)

    def authenticate_header(self, request) -> str | None:
        return "X-APP-ID"
