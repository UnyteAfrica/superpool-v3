from rest_framework import authentication
from rest_framework import exceptions
from django.conf import settings
from django.contrib.auth.models import AnonymousUser

class DashboardAuthentication(authentication.BaseAuthentication):
    header_name = 'HTTP_X_BACKEND_API_KEY'

    def authenticate(self, request):
        api_key = request.META.get(self.header_name, None)
        if not api_key:
            return None

        if api_key != settings.BACKEND_API_KEY:
            raise exceptions.AuthenticationFailed('API Key is invalid.')

        return AnonymousUser(), None