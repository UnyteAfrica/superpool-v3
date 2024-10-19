from drf_spectacular.extensions import OpenApiAuthenticationExtension
from drf_spectacular.utils import OpenApiParameter

from .authentication import APIKeyAuthentication


class APIKeyAuthExtension(OpenApiAuthenticationExtension):
    target_class = APIKeyAuthentication

    def get_security_requirements(self, auto_schema):
        return [{"APIKey": []}]

    def get_security_definition(self, auto_schema):
        return {
            "type": "apiKey",
            "name": "API-KEY",
            "in": "header",
        }

    def get_request_parameters(self, manual_parameters: list, *args, **kwargs):
        return [
            OpenApiParameter(
                name="API-KEY",
                location=OpenApiParameter.HEADER,
                description="API Key for authentication",
                required=True,
            )
        ]
