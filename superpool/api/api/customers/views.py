from rest_framework import status, viewsets
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from core.permissions import IsAdminUser as IsAdmin, IsCustomerSupport, IsMerchant
from core.merchants.models import Merchant
from rest_framework.pagination import LimitOffsetPagination
from .services import CustomerService

from core.user.models import Customer

from drf_spectacular.utils import OpenApiRequest, OpenApiResponse
from drf_spectacular.utils import extend_schema
from .serializers import CustomerInformationSerializer, CustomerSummarySerializer


class CustomerViewSet(viewsets.ModelViewSet):
    """
    Viewset for Admin and Customer Support to manage customers
    """

    permission_classes = [IsAdmin, IsCustomerSupport]


class MerchantCustomerViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Handles all merchant-related customer data.

    Merchants can retrieve information about their customers, including policy details, claims, transactions, and more.
    Each endpoint is a GET request and includes pagination and filtering options to handle large datasets effectively.
    """

    # permission_classes = [IsMerchant]
    pagination_class = LimitOffsetPagination
    # http_method_names = ["get"]

    def get_queryset(self):
        merchant_id = self.kwargs.get("tenant_id")
        return Customer.objects.filter(merchant=merchant_id)

    def get_service(self):
        """
        Return the instance of our customers endpoint service
        """
        return CustomerService()

    @extend_schema(
        summary="Retrieve all customers for a merchant",
        description=(
            "This endpoint returns a list of all customers associated with the authenticated merchant."
            " Merchants can filter customers by various attributes such as active policies or claims. "
            " Pagination is supported to handle large datasets."
        ),
        tags=["Customers"],
        responses={200: CustomerInformationSerializer(many=True)},
    )
    def list(self, request, tenant_id, *args, **kwargs):
        """
        Retrieve all customers for the authenticated merchant.
        The list can be filtered by the status of their policies, claims, or other criteria.

        Returns:
            - A list of customers, with optional filters to retrieve only those with active policies, claims, etc.
            - Supports pagination to handle large datasets.

        Usage:
            GET /merchants/{tenantId}/customers/
        """
        customer_service = self.get_service()
        merchant = get_object_or_404(Merchant, tenant_id=tenant_id)
        queryset = customer_service.list_customers_by_merchant(merchant=merchant)
        serializer = CustomerSummarySerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Retrieve a specific customer's details",
        description=(
            "This endpoint returns detailed information for a specific customer, including their contact "
            "information, policies, claims, and transactions."
        ),
        tags=["Customers"],
        responses={200: CustomerInformationSerializer},
    )
    def retrieve(self, request, *args, **kwargs):
        """
        Retrieve detailed information for a specific customer by ID.

        The information includes the customer's contact details, active and inactive policies, any claims they have made, and their transaction history.

        Returns:
            - The full details of a customer, including their associated policies, claims, and transactions.

        Usage:
            GET /merchants/{merchantId}/customers/{customerId}/
        """
        customer = self.get_object()
        serializer = CustomerInformationSerializer(customer)
        return Response(serializer.data, status=status.HTTP_200_OK)
