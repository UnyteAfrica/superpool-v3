import logging
from uuid import uuid4
import uuid
from .openapi import products_response_example
from datetime import datetime, timedelta
from core.permissions import (
    IsAdminUser,
    IsMerchant,
    IsCustomerSupport,
    IsMerchantOrSupport,
)
from rest_framework.permissions import IsAuthenticated

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
from rest_framework.exceptions import APIException, ValidationError
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from django.db.models import Q
from rest_framework import filters
from .openapi import (
    travel_insurance_example,
    travel_insurance_with_product_id_example,
    health_insurance_example,
    health_insurance_with_product_id_example,
    home_insurance_example,
    home_insurance_with_product_id_example,
    gadget_insurance_example,
    gadget_insurance_with_product_id_example,
    auto_insurance_example,
    auto_insurance_with_product_id_example,
    insurance_policy_purchase_req_example,
    insurance_policy_purchase_res_example,
    limited_policy_renewal_example,
    full_policy_renewal_example,
    policy_cancellation_request_example,
    policy_cancellation_request_example_2,
)

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


@extend_schema(
    summary="List all policies",
    operation_id="list-policies",
    description="List all policies available in the system",
    tags=["Policies"],
    responses={
        200: OpenApiResponse(
            PolicySerializer(many=True),
            "Policies",
        ),
        404: {"error": "There are no policies available at the moment"},
    },
)
class PolicyListView(generics.ListAPIView):
    """
    List all policies
    """

    serializer_class = PolicySerializer
    # authentication_classes = [APIKeyAuthentication]
    # permission_classes = [IsMerchant, IsCustomerSupport, IsAuthenticated]

    def get_queryset(self):
        return PolicyService.list_policies()

    def list(self, request: Request, *args: dict, **kwargs: dict) -> Response:
        queryset = self.get_queryset()

        if not queryset.exists():
            return Response(
                {"error": "There are no policies available at the moment"},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema(
    summary="List all products",
    operation_id="list-products",
    tags=["Products"],
    description="List all products available in the system",
    responses={
        200: OpenApiResponse(
            response=ProductSerializer(many=True),
            examples=[products_response_example],
        ),
        404: OpenApiResponse(
            response={"error": "No products found"},
            description="No products found",
            examples=[
                OpenApiExample(
                    "No Products Found Example",
                    value={"error": "No products found"},
                )
            ],
        ),
    },
)
class ProductListView(generics.ListAPIView):
    """
    List all products
    """

    serializer_class = ProductSerializer
    # authentication_classes = [APIKeyAuthentication]

    def get_queryset(self):
        return ProductService.list_products()

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
        operation_id="list-policies-by-product-type",
        tags=["Policies"],
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


@extend_schema(
    summary="Retrieve a product by ID or name",
    operation_id="retrieve_product",
    tags=["Products"],
    description="Retrieve a specific product by its ID or name",
    request=OpenApiRequest(
        request=ProductSerializer,
        examples=[
            OpenApiExample(
                name="Product ID Example",
                value={
                    "product_id": "b097d1b7-70f8-42a7-a411-6f22727b5c7d",
                },
            ),
            OpenApiExample(
                name="Product Name Example",
                value={
                    "product_name": "Health Insurance",
                },
            ),
        ],
    ),
    responses={
        200: OpenApiResponse(
            description="Product details",
            response=ProductSerializer,
            examples=[
                OpenApiExample(
                    "Product Response Example",
                    value={
                        "id": 1,
                        "name": "Health Insurance",
                        "product_type": "Health",
                        "insurer": "Reliance Health",
                        "description": "This is a health insurance policy",
                        "price": 1000.0,
                        "currency": "USD",
                        "created_at": "2021-11-01T00:00:00Z",
                        "updated_at": "2021-11-01T00:00:00Z",
                    },
                )
            ],
        )
    },
)
class ProductRetrieveView(generics.RetrieveAPIView):
    """
    This endpoint lets you find a product by its ID or name

    e.g

        /api/v1/products/1

        /api/v1/products/health-insurance
        /api/v1/products/health-insurance?product_id=1
    """

    serializer_class = ProductSerializer
    queryset = ProductService.list_products()
    # authentication_classes = [APIKeyAuthentication]

    def get_object(self):
        # Priority is given to the product_id
        # if the product_id is provided, we will use it to retrieve the product
        # if the product_id is not provided, we will fallback to the product_name

        product_id = self.kwargs.get("pk")
        product_name = self.kwargs.get("product_name")

        if product_id:
            return ProductService.get_product_by_id(product_id)
        return ProductService.get_product(product_name)


class PolicyAPIViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    queryset = PolicyService.list_policies()
    # permission_classes = [IsMerchant, IsAuthenticated, IsCustomerSupport]

    def get_serializer_class(self):
        if self.action == "renew":
            return PolicyRenewalRequestSerializer
        elif self.action == "update_policy":
            return PolicySerializer
        elif self.action == "search":
            return PolicySerializer
        return PolicySerializer

    def get_service(self):
        return PolicyService()

    @extend_schema(
        summary="Renew a policy",
        operation_id="renew-policy",
        tags=["Policies"],
        request=OpenApiRequest(
            request=PolicyRenewalRequestSerializer,
            examples=[
                limited_policy_renewal_example,
                full_policy_renewal_example,
            ],
        ),
        responses={
            200: OpenApiResponse(
                description="Insurance Policy Renewal successful",
                response=PolicyRenewalSerializer,
                examples=[
                    OpenApiExample(
                        "Successful Renewal Example",
                        value={
                            "renewal_status": "success",
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
                                    "renewable": True,
                                },
                                "renewal_date": "2024-11-01",
                            },
                        },
                    )
                ],
            ),
            400: OpenApiResponse(
                description="Bad request",
                examples=[
                    OpenApiExample(
                        "Bad Request Example",
                        value={
                            "renewal_status": "failed",
                            "error": "An error occurred, please provide the Policy Reference Number or the Policy unique ID",
                        },
                    )
                ],
            ),
            404: OpenApiResponse(
                description="Policy not found",
                examples=[
                    OpenApiExample(
                        "Not Found Example",
                        value={"renewal_status": "failed", "error": "Policy not found"},
                    )
                ],
            ),
            500: OpenApiResponse(
                description="Server error",
                examples=[
                    OpenApiExample(
                        "Server Error Example",
                        value={
                            "renewal_status": "failed",
                            "error": "Internal server error message",
                        },
                    )
                ],
            ),
        },
    )
    @action(detail=False, methods=["post"])
    def renew(self, request, *args, **kwargs):
        """
        This action allows you as a merchant to submit a renewal
        request for your customer
        """
        policy_service = self.get_service()
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            try:
                validated_data = serializer.validated_data
                policy_service.renew_policy(
                    policy_id=validated_data.get("policy_id"),
                    policy_number=validated_data.get("policy_number"),
                    policy_start_date=validated_data.get("preferred_policy_start_date"),
                    policy_expiry_date=validated_data.get("preferred_policy_start_date")
                    + timedelta(days=validated_data.get("policy_duration", 0)),
                    include_additional_coverage=validated_data.get(
                        "include_additional_coverage"
                    ),
                    modify_exisitng_coverage=validated_data.get(
                        "modify_exisitng_coverage"
                    ),
                    coverage_details=validated_data.get("coverage_details"),
                    auto_renew=validated_data.get("auto_renew"),
                )
                response_data = {
                    "renewal_status": "success",
                    "message": "Policy successfully renewed!",
                }
                return Response(response_data, status=status.HTTP_200_OK)
            except ValueError as e:
                return Response(
                    {"renewal_status": "failed", "error": str(e)},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            except NotImplementedError as e:
                ERR_CODE = "ERR_NOT_IMPLEMENTED"
                ERR_MESSAGE = (
                    "We are aware of this error, and are actively working on this feature. Please check back later."
                    "If you have any questions, please contact us at tech@unyte.com"
                    "As an alternative, we have provided a workaround for you to use."
                    "Please review the examples and try sending the payload in the other format."
                    "Thank you for your understanding."
                )
                return Response(
                    {
                        "renewal_status": "failed",
                        "err_code": ERR_CODE,
                        "error_detail": ERR_MESSAGE,
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )
            except RuntimeError as e:
                return Response(
                    {"renewal_status": "failed", "error": str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        operation_id="retrieve-policy-by-id",
        description="Retrieve a specific policy by its ID",
        tags=["Policies"],
        responses={
            200: OpenApiResponse(
                description="Policy details", response=PolicySerializer
            ),
            404: OpenApiResponse(description="Policy not found"),
        },
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
        operation_id="search-policies",
        description="Search for policies based on certain parameters",
        tags=["Policies"],
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
        operation_id="update-policy",
        tags=["Policies"],
        parameters=[
            OpenApiParameter(
                name="policy_id",
            ),
            OpenApiParameter(
                name="policy_number",
                description="policy reference number assigned by the insurer",
            ),
        ],
        request=OpenApiRequest(request=PolicySerializer),
        responses={
            200: OpenApiResponse(PolicySerializer, "Policy updated successfully"),
            400: {"error": "string", "detail": "string"},
        },
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


class QuoteListView(generics.ListAPIView):
    # permission_classes = [IsMerchant, IsCustomerSupport, IsAuthenticated]
    # authentication_classes = [APIKeyAuthentication]

    def get_service(self):
        return QuoteService()

    @extend_schema(
        summary="Retrieve list of quotes for an insurance policy",
        operation_id="list-quotes",
        tags=["Quotes"],
        responses={
            200: OpenApiResponse(
                description="Quotes",
                response=QuoteSerializer,
                examples=[],
            )
        },
    )
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

    # permission_classes = [IsMerchant, IsMerchantOrSupport]

    @extend_schema(
        summary="Retrieve a specific quote by its ID",
        operation_id="retrieve-quote",
        tags=["Quotes"],
        responses={
            200: OpenApiResponse(
                description="Quote details",
                response=QuoteSerializer,
                examples=[
                    OpenApiExample(
                        "Health Insurance Quote Example",
                        value={
                            "quote_code": "QTE-2021-01-0001",
                            "base_price": 1000.0,
                            "product": {
                                "id": "3b0630d1-1a90-4413-a46f-501fc5e783d9",
                                "created_at": "2021-11-01T00:00:00Z",
                                "updated_at": "2021-11-01T00:00:00Z",
                                "is_trashed": "false",
                                "trashed_at": "null",
                                "restored_at": "null",
                                "name": "Health Insurance",
                                "description": "This is a health insurance policy",
                                "product_type": "Health",
                                "provider": "1fecef4b-76c4-4b0f-a01c-282c45b645db",
                                "coverage_details": "null",
                                "insurer": "Reliance Health",
                                "price": {
                                    "amount": 1000.0,
                                    "description": "Health insurance premium",
                                    "currency": "USD",
                                    "discount_amount": 0.0,
                                    "surcharges": 0.0,
                                    "commission": 0.0,
                                },
                            },
                        },
                    ),
                ],
            ),
            404: OpenApiResponse(
                description="Not Found",
                examples=[
                    OpenApiExample(
                        "Quote Not Found Example", value={"error": "Quote Not Found"}
                    )
                ],
            ),
            500: OpenApiResponse(
                description="Internal Server Error",
                examples=[
                    OpenApiExample(
                        "Internal Server Error Example",
                        value={"error": "Internal Server Error"},
                    )
                ],
            ),
        },  # noqa,
    )
    def get(self, request, quote_code):
        """
        Endpoint to retrieve a specific quote by its ID
        """
        service = self.get_service()

        try:
            quote = service.get_quote(quote_code=quote_code)

            # should fix the assertion error on the serializer instance
            if isinstance(quote, QuoteSerializer):
                quote = quote.data
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
            201: OpenApiResponse(QuoteSerializer, "Quote information"),
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
    # permission_classes = [
    #     IsMerchant,
    # ]
    #
    def get_service(self):
        return QuoteService()

    @extend_schema(
        summary="Request a policy quote",
        operation_id="request-quote",
        tags=["Quotes"],
        request=OpenApiRequest(
            QuoteRequestSerializer,
            examples=[
                travel_insurance_example,
                travel_insurance_with_product_id_example,
                health_insurance_example,
                health_insurance_with_product_id_example,
                home_insurance_example,
                home_insurance_with_product_id_example,
                gadget_insurance_example,
                gadget_insurance_with_product_id_example,
                auto_insurance_example,
                auto_insurance_with_product_id_example,
            ],
        ),
        responses={
            200: OpenApiResponse(
                description="Quotes",
                response=QuoteSerializer,
                examples=[
                    OpenApiExample(
                        "Travel Insurance Quote",
                        value={
                            "quote_code": "QTE-2021-01-0001",
                            "base_price": 1000.0,
                            "product": {
                                "id": "3b0630d1-1a90-4413-a46f-501fc5e783d9",
                                "created_at": "2021-11-01T00:00:00Z",
                                "updated_at": "2021-11-01T00:00:00Z",
                                "is_trashed": "false",
                                "trashed_at": "null",
                                "restored_at": "null",
                                "name": "Travel Insurance",
                                "description": "This is a travel insurance policy",
                                "product_type": "Travel",
                                "provider": "1fecef4b-76c4-4b0f-a01c-282c45b645db",
                                "coverage_details": "null",
                                "insurer": "Virgina Travel",
                                "price": {
                                    "amount": 1000.0,
                                    "description": "Travel insurance premium",
                                    "currency": "USD",
                                    "discount_amount": 0.0,
                                    "surcharges": 0.0,
                                    "commission": 0.0,
                                },
                            },
                        },
                    ),
                ],
            ),
            400: OpenApiResponse(
                description="Bad Request",
                examples=[
                    OpenApiExample(
                        "Bad Request Example",
                        value={
                            "error": "Bad Request",
                            "detail": "Invalid request data",
                        },
                    )
                ],
            ),
            500: OpenApiResponse(
                description="Internal Server Error",
                examples=[
                    OpenApiExample(
                        "Internal Server Error Example",
                        value={"error": "Internal Server Error"},
                    )
                ],
            ),
        },
        examples=[
            travel_insurance_example,
            health_insurance_example,
            auto_insurance_example,
        ],
    )
    def post(self, request):
        # validate incoming data conforms to some predefined values
        req_serializer = QuoteRequestSerializer(data=request.data)

        if req_serializer.is_valid(raise_exception=True):
            request_data = req_serializer.validated_data
            insurance_details = request.data.pop("insurance_details", {})

            # retrieve the quote based on the parameters provided
            quote_service = self.get_service()
            quote_code = request_data.get("quote_code")
            product_type = request_data.get("product_type")
            insurance_name = request_data.get("insurance_name")
            try:
                if quote_code:
                    # Retrieve existing quote by code
                    quote_data = quote_service.get_quote(quote_code=quote_code)
                else:
                    # Create a new quote
                    coverage_type = insurance_details.get("coverage_type")
                    quote_data = quote_service._create_quote(
                        product_type=product_type,
                        product_name=insurance_name,
                        insurance_details=insurance_details,
                    )
                # quote_data = quote_service.get_quote(
                #     product=request_data.get(
                #         "product_type"
                #     ),  # an insurance type have to be provided e.g Auto, Travel, Health
                #     product_name=request_data.get(
                #         "insurance_name"
                #     ),  # as an addition, a policy name (Smart Health Insurance) can be provided
                #     quote_code=request_data.get("quote_code"),
                #     insurance_details=insurance_details,
                # )

                # # this should fix the error that am passing serializer instance rather than .data or .errors
                # if isinstance(quote_data, QuoteSerializer):
                #     quote_data = quote_data.data
                #     return Response(quote_data, status=status.HTTP_200_OK)
                # else:
                #     quote_serializer = QuoteSerializer(quote_data)
                #     return Response(quote_serializer.data, status=status.HTTP_200_OK)

                # If the result is a Quote object, serialize it
                if isinstance(quote_data, Quote):
                    quote_serializer = QuoteSerializer(quote_data)
                    return Response(quote_serializer.data, status=status.HTTP_200_OK)

                # If the result is already serialized data, return it directly
                if isinstance(quote_data, dict):
                    return Response(quote_data, status=status.HTTP_200_OK)

                # Handle unexpected types
                raise ValueError("Unexpected type returned from quote service.")
            except (ProductNotFoundError, QuoteNotFoundError) as api_err:
                logger.error(
                    f'An error occurred while fetching quotes: "{str(api_err)}"'
                )
                return Response(
                    {"error": str(api_err)}, status=status.HTTP_404_NOT_FOUND
                )
            except ValueError as exc:
                logger.error(f'ValueError: "{str(exc)}"')
                return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        logger.error(f"Request data is invalid: {req_serializer.errors}")
        return Response(req_serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PolicyPurchaseView(generics.GenericAPIView):
    """
    This view allows you to generate a new policy for your
    customer
    """

    serializer_class = PolicyPurchaseSerializer
    # permission_classes = [IsMerchant, IsMerchantOrSupport]

    @extend_schema(
        summary="Purchase a policy",
        operation_id="purchase-policy",
        tags=["Policies"],
        description="Purchase a new policy for your customer",
        request=OpenApiRequest(
            request=PolicyPurchaseSerializer,
            examples=[insurance_policy_purchase_req_example],
        ),
        responses={
            201: OpenApiResponse(
                description="Policy purchase successful",
                response=PolicyPurchaseResponseSerializer,
                examples=[insurance_policy_purchase_res_example],
            ),
            400: OpenApiResponse(
                description="Bad Request",
                examples=[
                    OpenApiExample(
                        "Bad Request Example",
                        value={
                            "error": "Bad Request",
                            "detail": "Invalid request data",
                        },
                    )
                ],
            ),
            500: OpenApiResponse(
                description="Internal Server Error",
                examples=[
                    OpenApiExample(
                        "Internal Server Error Example",
                        value={"error": "Internal Server Error"},
                    )
                ],
            ),
        },
    )
    def post(self, request, *args, **kwargs):
        """
        Issue a new policy for your customer

        Handles the purchase of an insurance policy
        """
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            logger.info(f"Validated data: {serializer.validated_data}")
            service = PolicyService()

            try:
                policy = service.purchase_policy(serializer.validated_data)
                if policy:
                    response_serializer = PolicyPurchaseResponseSerializer(policy)
                    return Response(
                        response_serializer.data, status=status.HTTP_201_CREATED
                    )
            except (ValidationError, Quote.DoesNotExist) as api_err:
                logger.error(f"An error occurred: {str(api_err)}")
                return Response(
                    {"error": str(api_err)}, status=status.HTTP_400_BAD_REQUEST
                )
            except Exception as exc:
                logger.error(f"An error occurred: {str(exc)}")
                return Response(
                    {"error": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PolicyCancellationView(generics.GenericAPIView):
    """
    This view allows you to initiate the termination of insurance policy
    """

    # permission_classes = [IsMerchant, IsMerchantOrSupport]
    # authentication_classes = [APIKeyAuthentication]

    serializer_class = PolicyCancellationRequestSerializer

    def get_service(self):
        return PolicyService()

    @extend_schema(
        summary="Cancel an active policy subscription",
        operation_id="cancel-policy",
        tags=["Policies"],
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
        request=OpenApiRequest(
            request=PolicyCancellationRequestSerializer,
            examples=[
                policy_cancellation_request_example,
                policy_cancellation_request_example_2,
            ],
        ),
        responses={
            200: OpenApiResponse(
                description="Policy cancellation successful",
                response={
                    "cancellaton_status": "string",
                    "message": "string",
                },
                examples=[
                    OpenApiExample(
                        "Policy Cancellation Success Example",
                        value={
                            "cancellaton_status": "success",
                            "message": "Policy has been successfully cancelled",
                        },
                    )
                ],
            ),
            400: OpenApiResponse(
                description="Bad Request",
                examples=[
                    OpenApiExample(
                        "Bad Request Example",
                        value={
                            "error": "Bad Request",
                            "detail": "Invalid request data",
                        },
                    )
                ],
            ),
        },
    )
    def post(self, request):
        """
        Cancel a policy subscription using the policy ID or the policy number
        """
        service = self.get_service()
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            validated_data = serializer.validated_data

            policy_id = validated_data.get("policy_id")
            policy_number = validated_data.get("policy_number")
            cancellation_reason = validated_data.get("cancellation_reason")

            try:
                service.cancel_policy(
                    policy_id=policy_id,
                    policy_number=policy_number,
                    reason=cancellation_reason,
                )

                response_data = {
                    "cancellaton_status": "success",
                    "message": "Policy has been successfully cancelled",
                }
                return Response(response_data, status=status.HTTP_200_OK)
            except Exception as exc:
                logger.error(f"An unkown error occured: {str(exc)}")
                return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
