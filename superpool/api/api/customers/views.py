from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from core.permissions import IsAdminUser as IsAdmin, IsCustomerSupport, IsMerchant
from rest_framework.pagination import LimitOffsetPagination

from core.user.models import Customer

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

    permission_classes = [IsMerchant]
    pagination_class = LimitOffsetPagination
