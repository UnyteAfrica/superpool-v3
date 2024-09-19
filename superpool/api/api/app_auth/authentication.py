from django.conf import settings
from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.exceptions import AuthenticationFailed

# from rest_framework_api_key.models import APIKey
from core.models import APIKey as APIKeyModel

User = settings.AUTH_USER_MODEL


class APIKeyAuthentication(BaseAuthentication):
    """
    Custom authentication class that uses API Key from request headers.
    """

    def authenticate(self, request):
        KEYWORD = "SUPERPOOL "
        auth_header = get_authorization_header(request).decode("utf-8")
        print(auth_header)

        if not auth_header:
            return None

        # header has to start with the keyword!
        if not auth_header.startswith(KEYWORD):
            return None

        api_key = auth_header[len(KEYWORD) :].strip()

        if not api_key:
            raise AuthenticationFailed(
                "Invalid API key header. No credentials provided."
            )

        return self.authenticate_credentials(api_key)

    def authenticate_credentials(self, key):
        try:
            hashed = APIKeyModel().hash_(key)
            key_obj = APIKeyModel.objects.get(hashedkey=hashed)
        except APIKeyModel.DoesNotExist:
            raise AuthenticationFailed("Invalid API key")

        return key_obj.merchant, key_obj

    def authenticate_header(self, request) -> str | None:
        return "SUPERPOOL"
