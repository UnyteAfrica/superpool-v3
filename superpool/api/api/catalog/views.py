import logging
from uuid import uuid4
import uuid

from api.app_auth.authentication import APIKeyAuthentication
from api.catalog.exceptions import QuoteNotFoundError
from api.catalog.filters import QSearchFilter
from api.catalog.serializers import PolicyPurchaseResponseSerializer
from core.catalog.models import Policy, Product, Quote
from core.user.models import Customer
from django.db.models import QuerySet
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    OpenApiRequest,
    OpenApiResponse,
    extend_schema,
)
from rest_framework import generics, mixins, status, views, viewsets
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from django.db.models import Q

from .exceptions import ProductNotFoundError
from .serializers import (
    PolicyCancellationRequestSerializer,
    PolicyCancellationResponseSerializer,
    PolicyCancellationSerializer,
    PolicyPurchaseSerializer,
    PolicyRenewalSerializer,
    PolicySerializer,
    ProductSerializer,
    QuoteRequestSerializer,
    QuoteSerializer,
    PolicyRenewalRequestSerializer,
)
from .services import PolicyService, ProductService, QuoteService

logger = logging.getLogger(__name__)


class PolicyListView(generics.ListAPIView):
    """
    List all policies
    """

    serializer_class = PolicySerializer

    def get_queryset(self):
        return PolicyService.list_policies()

    @extend_schema(
        summary="List all policies",
        operation_id="list_policies",
        description="List all policies available in the system",
        responses={
            200: PolicySerializer(many=True),
            404: {"error": "There are no policies available at the moment"},
        },
    )
    def list(self, request: Request, *args: dict, **kwargs: dict) -> Response:
        queryset = self.get_queryset()

        if not queryset.exists():
            return Response(
                {"error": "There are no policies available at the moment"},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ProductListView(generics.ListAPIView):
    """
    List all products
    """

    serializer_class = ProductSerializer

    def get_queryset(self):
        return ProductService.list_products()

    @extend_schema(
        summary="List all products",
        operation_id="list_products",
        description="List all products available in the system",
        responses={
            200: ProductSerializer(many=True),
            404: {"error": "No products are currently available"},
        },
    )
    def list(self, request: Request, *args: dict, **kwargs: dict) -> Response:
        queryset = self.get_queryset()

        # if we do not have any products, we will return a 404
        if not queryset.exists():
            return Response(
                {"error": "No products are currently available"},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class PolicyByProductTypeView(generics.ListAPIView):
    serializer_class = PolicySerializer

    def get_queryset(self) -> QuerySet:
        return PolicyService.list_policies_by_product_type()

    @extend_schema(
        summary="List policies by product type",
        description="List all policies available for a specific product type",
        responses={
            200: PolicySerializer(many=True),
            404: {"error": "No policies found for this product category"},
        },
    )
    def list(self, request: Request, *args: dict, **kwargs: dict) -> Response:
        queryset = self.get_queryset()

        if not queryset.exists():
            return Response(
                {"error": "No policies found for this product category"},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ProductView(generics.RetrieveAPIView):
    """
    This endpoint lets you find one from the products list by the product's id.
    """

    serializer_class = ProductSerializer

    def get_queryset(self, **kwargs: dict):
        return ProductService.get_product_by_id(kwargs.get("product_id"))

    @extend_schema(
        summary="Retrieve a product by ID",
        description="Retrieve a product by ID",
        responses={
            200: ProductSerializer,
            404: {"error": "Product not found"},
            500: {"error": "Internal server error"},
        },
    )
    def retrieve(self, request: Request, *args: dict, **kwargs: dict) -> Response:
        params = request.query_params.dict()
        product_id = params.get("product_id")

        try:
            queryset = self.get_queryset(product_id=product_id)
            serializer = self.get_serializer(queryset)
        except Product.DoesNotExist:
            return Response(
                {"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND
            )
        except Product.MultipleObjectsReturned:
            return Response(
                {"error": "Multiple products found"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        except Exception:
            return Response(
                {"error": "Internal server error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        return Response(serializer.data, status=status.HTTP_200_OK)


class PolicyAPIViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    queryset = PolicyService.list_policies()

    def get_serializer_class(self):
        if self.action == "create":
            return PolicyPurchaseSerializer
        return PolicySerializer

    def get_service(self):
        return PolicyService()

    @extend_schema(
        summary="Renew a policy",
        request=PolicyRenewalRequestSerializer,
        responses={
            200: OpenApiResponse(
                description="Insurance Policy Renewal successful",
                examples=[
                    "application/json": {
                        "renewal_status": "success",  # 'success' or 'failed
                        "message": "Policy Renewal successful",
                        "data": {
                            "policy_number": "POL-2021-01-0001",
                            "policy_duration": 365,
                            "policy_metadata": {
                                "product_name": "Basic Health Coverage",
                                "product_type": "Health",
                                "insurer": "Reliance Health",
                                "customer_name": "Janet Joestar",
                                "customer_email": "janet.joe@email.com",
                                "customer_phone": "+234 123 456 7890",
                                "customer_address": "123, Main Street, Lagos, Nigeria",
                                "policy_status": "active",
                                "policy_id": "e2f7ca44-905a-4e22-b31f-2d1f23fb1c07",
                                "renewable": "True",
                            },
                            "renewal_date": "2024-11-01",
                        },
                    },
                ],
            ),
            400: OpenApiResponse(
                description='Bad request',
                examples={
                    'application/json': {
                        "renewal_status": "error",
                        "error": 'An error occured, please provide the Policy Refrence Number or the Policy unique\'s iD'
                    }
                }
            ),
            404: OpenApiResponse(
                description='Policy not found',
                examples={
                    'application/json': {
                        "renewal_status": "error",
                        "error": "Policy not found"
                    }
                }
            ),
            500: OpenApiResponse(
                description='Server error',
                examples={
                    'application/json': {
                        "renewal_status": "error",
                        "error": "Internal server error message"
                    }
                }
            )
        },
    )
    @action(detail=False, methods=["post"])
    def renew(self, request, *args, **kwargs):
        """
        This action allows you as a merchant to submit a renewal
        request for your customer
        """
        policy_id = request.data.get("policy_id")
        policy_number = request.data.get("policy_number")

        if not policy_number or not policy_id:
            return Response(
                {
                    "error": "An error occured, please provide the Policy Refrence Number or the Policy unique's iD"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = PolicyRenewalRequestSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            policy_identifier = data.get("policy_identifier")

            try:
                policy = Policy.objects.get(
                    Q(policy_id=policy_identifier) | Q(policy_number=policy_identifier)
                )
                renewed_policy = PolicyService.renew_policy(
                    policy, data.get("policy_end_date")
                )
                response_serializer = PolicyRenewalSerializer(renewed_policy)
                response_data = {
                    "renewal_status": "success",
                    "message": "Policy Renewal successful",
                    "data": response_serializer.data,
                }
                return Response(response_data, status=status.HTTP_200_OK)
            except Policy.DoesNotExist:
                response_data = {
                    "renewal_status": "failed",
                    "error": "Policy not found",
                }
                return Response(response_data, status=status.HTTP_404_NOT_FOUND)
            except Exception as exc:
                response_data = {
                    "renewal_status": "failed",
                    "error": str(exc),
                }
                return Response(
                    response_data, status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        response_data = {
            "renewal_status": "failed",
            "error": serializer.errors,
        }
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        operation_id="retrieve-policy-by-id",
        description="Retrieve a specific policy by its ID",
        responses={200: PolicySerializer},
    )
    def retrieve(self, request, pk=None):
        """
        Retrieve a specific policy by its ID
        """
        try:
            policy = Policy.objects.get(pk=pk)
        except Policy.DoesNotExist:
            return Response(
                {"error": "Policy not found"}, status=status.HTTP_404_NOT_FOUND
            )
        serializer = self.get_serializer(policy)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="product_type",
                description="Type of the insurance product (e.g., Life, Health, Auto, Gadget)",
                required=False,
                type=OpenApiTypes.STR,
            ),
            OpenApiParameter(
                name="policy_name",
                description="Name of the insurance policy",
                required=False,
                type=OpenApiTypes.STR,
            ),
        ],
        responses={200: PolicySerializer(many=True)},
    )
    @action(detail=False, methods=["get"])
    def search(self, request, **extra_kwargs):
        """
        Action that allows you to search or filter for a policy based on
        certain parameters.

        Params are not limited to, customer details, status of the policy,
        policy category
        """
        product_type = request.query_params.get("product_type")
        policy_name = request.query_params.get("policy_name")

        qs = self.get_queryset()

        if product_type:
            qs = qs.filter(product__product_type__iexact=product_type)

        if policy_name:
            qs = qs.filter(product__name__icontains=policy_name)

        # we want to return a paginated results
        # at every filteration
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Update an existing policy data",
        parameters=[
            OpenApiParameter(
                name="policy_id",
            ),
            OpenApiParameter(
                name="policy_number",
                description="policy reference number assigned by the insurer",
            ),
        ],
        request=PolicySerializer,
        responses={200: PolicySerializer, 400: {"error": "string", "detail": "string"}},
    )
    @action(detail=False, methods=["patch"], url_path="update")
    def update_policy(self, request):
        """
        Update an insurance policy using the policy ID or the policy number
        """
        policy_id = request.data.get("policy_id")
        policy_number = request.data.get("policy_number")

        if not policy_number or not policy_id:
            return Response(
                {
                    "error": "Error! Provide a policy_id or policy_number to update policy",
                    "detail": "You must provide either policy ID issued by us or the policy reference number issued by the insurer.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if policy_id:
            try:
                instance = Policy.objects.get(policy_id=policy_id)
            except Policy.DoesNotExist:
                return Response(
                    {"error": "Policy not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )
        elif policy_number:
            try:
                instance = Policy.objects.get(policy_number=policy_number)
            except Policy.DoesNotExist:
                return Response(
                    {"error": "Policy not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )
        else:
            return Response(
                {"error": "You must provide either policy_id or policy_number."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.get_serializer(instance, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProductAPIViewSet(viewsets.GenericViewSet):
    # endpoint to search and filter for product based on query parameters

    # endpoint to get a product belonging to a specific insurer
    pass


class QuoteListView(generics.ListAPIView):
    def get_service(self):
        return QuoteService()

    def get(self, request, product_name):
        """
        Retrieve list of quotes for an insurance policy
        """
        service = self.get_service()

        try:
            quotes = service.get_quote(product=product_name, batch=True)
            return Response(quotes, status=status.HTTP_200_OK)
        except (QuoteNotFoundError, ProductNotFoundError) as api_err:
            return Response({"error": str(api_err)}, status=status.HTTP_404_NOT_FOUND)


class QuoteDetailView(views.APIView):
    def get_service(self):
        return QuoteService()

    def get(self, request, quote_code):
        """
        Endpoint to retrieve a specific quote by its ID
        """
        service = self.get_service()

        try:
            quote = service.get_quote(quote_code=quote_code)
            return Response(quote, status=status.HTTP_200_OK)
        except QuoteNotFoundError as api_err:
            return Response({"error": str(api_err)}, status=status.HTTP_404_NOT_FOUND)


class QuoteAPIViewSet(viewsets.ViewSet):
    def get_permissions(self):
        if self.action in ("create", "update"):
            self.permission_classes = [IsAdminUser]
        elif self.action == "accept":
            self.permission_classes = [IsAuthenticated]
        return super().get_permissions()

    def get_service(self):
        return QuoteService()

    @extend_schema(
        summary="Request a policy quote",
        responses={
            200: QuoteSerializer,
        },
    )
    @action(detail=False, methods=["post"])
    def request_quote(self, request):
        service = self.get_service()
        quote_data = request.data

        # we need the metadata to determine if the merchant is requesting for
        # a list of quotes for a group of customers or for a single customer
        customer_metadata = quote_data.get("customer_metadata", "INDIVIDUAL")

        quote = service.get_quote(
            product=quote_data.get("product_type"),
            quote_code=quote_data.get("quote_code"),
            batch=(customer_metadata == "BATCH"),
        )
        return Response(quote, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["post"], url_name="request")
    def accept_quote(self, request):
        service = self.get_service()
        quote_code = request.data.get("quote_code")

        if not quote_code:
            return Response(
                {"error": "Quote code is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # first we want to get the quote by the quote id from the database
            # then we want to convert to a suitable policy, that is just generating a policy
            quote = Quote.objects.get(quote_code=quote_code)

            # this is where actual conversion to policy takes place
            #
            # The idea here is that we take a previously retrieved quote, and create a corresponding
            # policy
            policy_id = service.accept_quote(quote)
            return Response({"policy_id": policy_id}, status=status.HTTP_200_OK)
        except Quote.DoesNotExist:
            return Response(
                {"error": "Quote not found"}, status=status.HTTP_404_NOT_FOUND
            )


class RequestQuoteView(views.APIView):
    def get_service(self):
        return QuoteService()

    @extend_schema(
        summary="Request a policy quote",
        request=QuoteRequestSerializer,
        responses={
            200: QuoteSerializer,
        },
    )
    def post(self, request):
        mode = request.META.get("x-quote-mode", "testnet")

        # validate incoming data conforms to some predefined values
        req_serializer = QuoteRequestSerializer(data=request.data)
        if req_serializer.is_valid(raise_exception=True):
            request_data = req_serializer.validated_data

            if mode == "mainnet":
                # make call to the API service
                pass
            # it means we in dev mode
            quote_service = self.get_service()
            # retrieve the quote based on the parameters provided
            quote = quote_service.get_quote(
                product=request_data.get(
                    "insurance_type"
                ),  # an insurance type have to be provided e.g Auto, Travel, Health
                product_name=request_data.get(
                    "insurance_name"
                ),  # as an addition, a policy name (Smart Health Insurance) can be provided
                quote_code=request_data.get("quote_code"),
            )
            if quote:
                return Response(quote.data, status=status.HTTP_200_OK)
            return Response(quote.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response(req_serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PolicyPurchaseView(generics.CreateAPIView):
    """
    This view allows you to generate a new policy for your
    customer
    """

    serializer_class = PolicyPurchaseSerializer

    @extend_schema(
        summary="Purchase a policy",
        description="Purchase a new policy for your customer",
        request=PolicyPurchaseSerializer,
        responses={201: PolicyPurchaseResponseSerializer},
    )
    def create(self, request, *args, **kwargs):
        """
        Issue a new policy for a customer
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        policy = serializer.save()
        response_serializer = PolicyPurchaseResponseSerializer(policy)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class PolicyCancellationView(generics.GenericAPIView):
    """
    This view allows you to initiate the termination of insurance policy
    """

    serializer_class = PolicyCancellationRequestSerializer

    def get_service(self):
        return PolicyService()

    @extend_schema(
        summary="Cancel an active policy subscription",
        parameters=[
            OpenApiParameter(
                name="policy_id",
                description="Unique ID of the policy",
            ),
            OpenApiParameter(
                name="policy_number",
                description="policy reference number assigned by the insurer",
            ),
        ],
        description="Cancel an active policy subscription using the policy id or the policy number provided by the insurer",
        request=PolicyCancellationRequestSerializer,
        responses={200: PolicyCancellationResponseSerializer, 400: {"error": "string"}},
    )
    def post(self, request):
        """
        Cancel a policy subscription using the policy ID or the policy number
        """
        service = self.get_service()
        policy_number = request.data.get("policy_number")
        policy_id = request.data.get("policy_id")

        if not policy_id or not policy_number:
            return Response(
                {
                    "error": "Either policy number or policy number must be provided",
                    "detail": "Please provide a valid policy reference number or policy id to perform this action",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            try:
                response = service.cancel_policy(
                    policy_identifier=serializer.validated_data["policy_id"],
                    reason=serializer.validated_data["cancellation_reason"],
                )
                response_serializer = PolicyCancellationResponseSerializer(response)
                return Response(response_serializer.data, status=status.HTTP_200_OK)
            except Exception as exc:
                return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
