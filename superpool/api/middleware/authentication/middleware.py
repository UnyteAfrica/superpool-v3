"""
This is module intercepts incoming request/response processing cycle
to perform additional functionalities not provided in the framework's
middleware

"""

import logging

from core.models import Application
from core.merchants.models import Merchant
from django.http import JsonResponse
from rest_framework import status

# from rest_framework.response import Response

logger = logging.getLogger(__name__)


class APIKeyMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Get the information of the merchant from the request headers
        # if the merchant_id is not present in the request headers, it therefore
        # means, we have to check if the reqeust is coming from an internal user -
        # the admin or the customer support
        # otherwise invalidate the reqeust

        # NOTE: merchant_id is the unique identifier of the merchant
        merchant_id = request.headers.get("X-Merchant-ID")
        # APP ID is the identifier of the application, this is used to identify the
        # application that is making the request
        # for merchannts, they would have to create an application and use the
        # application id to make requests to the API
        x_app_id = request.headers.get("X-APP-ID")

        if merchant_id and x_app_id:
            try:
                merchant = Merchant.objects.get(id=merchant_id)
                application = Application.objects.get(id=x_app_id)

                if merchant and application:
                    request.tenant = merchant
            except (Merchant.DoesNotExist, Application.DoesNotExist):
                request.tenant = None
        else:
            request.tenant = None

        response = self.get_response(request)

        return response
