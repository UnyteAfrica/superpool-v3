"""
This is module intercepts incoming request/response processing cycle
to perform additional functionalities not provided in the framework's
middleware

"""

import logging

from core.models import Application
from django.http import JsonResponse
from rest_framework import status

# from rest_framework.response import Response

logger = logging.getLogger(__name__)


class APIKeyMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        x_app_id = request.headers.get("X-APP-ID")

        if not x_app_id:
            return JsonResponse(
                {"error": "Request object must contain X-APP-ID"},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        try:
            app = Application.objects.get(application_id=x_app_id)

            request.application = app
            request.merchant = app.merchant
        except Application.DoesNotExist:
            logger.error(f"Invalid X-APP-ID: {x_app_id}")
            return JsonResponse(
                {"error": "Invalid X-APP-ID"}, status=status.HTTP_403_FORBIDDEN
            )

        response = self.get_response(request)

        return response