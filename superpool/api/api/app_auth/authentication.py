from core.models import Application
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed


class APIKeyAuthentication(BaseAuthentication):
    """
    Custom authentication class to authenticate requests based on X-APP-ID header
    and return the merchant object
    """

    def authenticate(self, request):
        # Get both the X-APP-ID and API-KEY headers
        x_app_id = request.headers.get("X-APP-ID")

        # If X-APP-ID header is not present, return None
        if not x_app_id:
            return None

        try:
            app = Application.objects.get(application_id=x_app_id)

        except Application.DoesNotExist:
            raise AuthenticationFailed("Invalid X-APP-ID")

        request.application = app
        request.merchant = app.merchant

        return (app.merchant, None)

    def authenticate_header(self, request) -> str | None:
        return "X-APP-ID"
