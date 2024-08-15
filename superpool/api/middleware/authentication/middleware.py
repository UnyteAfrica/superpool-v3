"""
This is module intercepts incoming request/response processing cycle
to perform additional functionalities not provided in the framework's
middleware

"""

import logging

from core.models import Application
from core.merchants.models import Merchant

logger = logging.getLogger(__name__)


class TenantAuthenticationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Get the information of the merchant from the request headers
        # if the merchant_id is not present in the request headers, it therefore
        # means, we have to check if the reqeust is coming from an internal user -
        # the admin or the customer support
        # otherwise invalidate the reqeust

        # NOTE: merchant_id is the unique identifier of the merchant
        merchant_id = request.headers.get("X-Tenant-ID")

        if merchant_id:
            try:
                merchant = Merchant.objects.get(tenant_id=merchant_id)

                if merchant:
                    tenant = merchant.user
                    request.user = tenant
                else:
                    # merchant information not found
                    logger.warning("Invalid merchant information")
                    request.tenant = None
            except (Merchant.DoesNotExist, Application.DoesNotExist) as err:
                # if no merchant or application is found in the database, fallback to normal
                logger.warning(f"Error fetching merchant or application: {err}")
                request.user = None
        else:
            # if the merchant_id or application_id is not found in the request headers
            # proceed to authenticate as normal authentication
            logger.warning("Merchant ID or Application ID not found in request headers")
            request.user = None

        response = self.get_response(request)

        return response
