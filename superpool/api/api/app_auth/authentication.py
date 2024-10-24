import logging

from django.conf import settings
from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.request import Request

# from rest_framework_api_key.models import APIKey
from api.app_auth.services import KeyAuthService
from core.models import APIKey as APIKeyModel

User = settings.AUTH_USER_MODEL

logger = logging.getLogger(__name__)


class APIKeyAuthentication(BaseAuthentication):
    """
    Custom authentication class that uses API Key from request headers.
    """

    KEYWORD = "SUPERPOOL "

    def authenticate(self, request):
        auth_header = get_authorization_header(request).decode("utf-8")
        print(auth_header)

        if not auth_header:
            return None

        # header has to start with the keyword!
        if not auth_header.startswith(self.KEYWORD):
            return None

        api_key = auth_header[len(self.KEYWORD) :].strip()

        if not api_key:
            raise AuthenticationFailed(
                "Invalid API key header. No credentials provided."
            )

        return self.authenticate_credentials(api_key)

    def authenticate_credentials(self, key):
        try:
            hashed = APIKeyModel().hash_key(key)
            key_obj = APIKeyModel.objects.get(key_hash=hashed)
        except APIKeyModel.DoesNotExist:
            raise AuthenticationFailed("Invalid API key")

        user = key_obj.merchant.user
        return user, key_obj

    def authenticate_header(self, request) -> str | None:
        return self.KEYWORD


class ClientKeyAuthenticationBackend(BaseAuthentication):
    """
    Authentication Scheme for API Key V2

    This backend is used to authenticate the incoming request using API Key provided
    in the request headers. The key is validated against the APIKeyV2 model and the
    corresponding user is returned.
    """

    def __init__(self):
        self.auth_service = KeyAuthService()

    def authenticate(self, request: Request):
        auth_key = request.headers.get("Authorization") or request.headers.get(
            "X-API-Key"
        )

        if not auth_key:
            # proceed to the next authentication class
            return None

        try:
            key_obj = self.auth_service.validate(auth_key)
        except ValueError as e:
            logger.exception("API key validation failed")
            raise AuthenticationFailed("Invalid API Key")

        user = self.get_user(key_obj)
        return user, key_obj

    def get_user(self, key_obj):
        """
        Retrieve the user from the key object
        """
        # validate the api key type
        # if the key type is internal (that is, the key for Web-Facing Backend), then
        # uhm... what hhould we  do?
        # otherwise, if the key type is 'merchant' (it means, the key can be used for
        # integration purpose,we should return the user object associated with the  merchant)
