import logging
from datetime import timedelta

from asgiref.sync import async_to_sync
from django.core.exceptions import MultipleObjectsReturned
from django.db.models import DecimalField, F, Q, QuerySet, Value
from django.db.models.functions import Cast, Coalesce, NullIf
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
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.request import Request
from rest_framework.response import Response
from typing_extensions import deprecated

from api.catalog.exceptions import QuoteNotFoundError
from api.catalog.permissions import AdminOnlyInsurerFilterPermission
from api.catalog.serializers import PolicyPurchaseResponseSerializer
from core.catalog.models import Policy, Product, Quote
from core.models import Coverage

from .exceptions import ProductNotFoundError
from .openapi import (
    full_policy_renewal_example,
    insurance_policy_purchase_req_example,
    insurance_policy_purchase_res_example,
    limited_policy_renewal_example,
    policy_cancellation_request_example,
    policy_cancellation_request_example_2,
    products_response_example,
    quote_request_example,
)
from .quote_service import QuoteService
from .quote_service import QuoteService as QuoteServiceV2
from .serializers import (
    CoverageSerializer,
    FullCoverageSerializer,
    PolicyCancellationRequestSerializer,
    PolicyPurchaseSerializer,
    PolicyRenewalRequestSerializer,
    PolicyRenewalSerializer,
    PolicySerializer,
    PolicyUpdateSerializer,
    ProductSerializer,
    QuoteRequestSerializer,
    QuoteRequestSerializerV2,
    QuoteResponseSerializerV2,
    QuoteSerializer,
)
from .services import PolicyService, ProductService

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
    pagination_class = LimitOffsetPagination
    # authentication_classes = [APIKeyAuthentication]

    def get_queryset(self):
        return ProductService.list_products()

    def list(self, request: Request, *args: dict, **kwargs: dict) -> Response:
        queryset = self.get_queryset()

        # if we do not have any products, we will return a 404
        if not queryset:
            return Response(
                {"error": "No products are currently available"},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = self.get_serializer(queryset, many=True)
        page = self.paginate_queryset(queryset)
        if page is not None:
            return self.get_paginated_response(serializer.data)
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
    summary="Retrieve a product by ID",
    operation_id="retrieve_product",
    tags=["Products"],
    description="Retrieve a specific product by its ID",
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
class ProductRetrieveView(generics.GenericAPIView):
    """
    This endpoint lets you find a product by its ID or name

    e.g

        /api/v1/products/<uuid:pk>

        /api/v1/products/<str:product_name>
    """

    serializer_class = ProductSerializer
    queryset = ProductService.list_products()
    pagination_class = LimitOffsetPagination
    http_method_names = ["get"]

    # authentication_classes = [APIKeyAuthentication]

    def get(self, request, *args, **kwargs):
        # Priority is given to the product_id
        # if the product_id is provided, we will use it to retrieve the product
        # if the product_id is not provided, we will fallback to the product_name

        product_id = self.kwargs.get("pk")
        product_name = self.kwargs.get("product_name")

        if product_id:
            try:
                product = ProductService.get_product_by_id(product_id)
                serializer = self.get_serializer(product)
                return Response(serializer.data, status=status.HTTP_200_OK)
            except Product.DoesNotExist:
                return Response(
                    {"error": f"Product with ID '{product_id}' not found."},
                    status=status.HTTP_404_NOT_FOUND,
                )

        elif product_name:
            # multiple objects can be returned - although we only care for exact matches
            # if there are no exact matches, we will return a 404
            product_exact_matches = ProductService.get_product_by_name(product_name)
            logger.info(f"Products: {product_exact_matches}")

            if product_exact_matches.exists():
                print(
                    f"Product exact matches: {product_exact_matches.values_list('name', flat=True)}"
                )
                # single product returned, just return the product
                if product_exact_matches.count() == 1:
                    print("found just one match")
                    serializer = self.get_serializer(product_exact_matches.first())
                    return Response(serializer.data, status=status.HTTP_200_OK)

                # multple objects returned, return a paginated response
                print("found multiple matches")
                page = self.paginate_queryset(product_exact_matches)
                if page is not None:
                    serializer = self.get_serializer(page, many=True)
                    return self.get_paginated_response(serializer.data)

                # pagingation failed? return all the products
                serializer = self.get_serializer(product_exact_matches, many=True)
                return Response(serializer.data, status=status.HTTP_200_OK)

            # no products returned, 404
            return Response(
                {"error": f"Product with name '{product_name}' not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        # no product id or product name? client fucked up! return 404
        return Response(
            {"error": "Please provide a valid Product ID or Product Name"},
            status=status.HTTP_400_BAD_REQUEST,
        )


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
            return PolicyUpdateSerializer
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
        summary="View the details of a specific insurance policy by its ID",
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
        summary="Search and filter for policies",
        # description="Search for policies based on certain parameters",
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
            # OpenApiParameter(
            #     name="policy_number",
            #     description="policy reference number assigned by the insurer",
            # ),
        ],
        request=OpenApiRequest(request=PolicyUpdateSerializer),
        responses={
            200: OpenApiResponse(PolicySerializer, "Policy updated successfully"),
            400: {"error": "string", "detail": "string"},
        },
    )
    @action(detail=False, methods=["patch"], url_path="update")
    def update_policy(self, request):
        """
        Update an insurance policy using the policy ID
        """
        policy_id = request.data.get("policy_id")

        if not policy_id:
            return Response(
                {
                    "error": "Error! Provide a 'policy_id' to update the policy",
                    "detail": "You must provide the policy ID issued by us to update the policy.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            instance = Policy.objects.get(policy_id=policy_id)
        except Policy.DoesNotExist:
            return Response(
                {"error": "Policy not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        except MultipleObjectsReturned as data_integrity_err:
            logger.error(
                f"Multiple policies found for: {policy_id}. "
                f"ERROR: {str(data_integrity_err)}"
            )
            instance = Policy.objects.filter(policy_id=policy_id).first()

        serializer = self.get_serializer(instance, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            policy = Policy.objects.get(policy_id=policy_id)
            response_serializer = PolicySerializer(policy)
            return Response(response_serializer.data, status=status.HTTP_200_OK)
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
        from api.catalog.services import QuoteService

        return QuoteService()

    # permission_classes = [IsMerchant, IsMerchantOrSupport]

    @extend_schema(
        summary="Retrieve a specific quote by its reference code",
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
        Endpoint to retrieve a specific quote by its reference code
        """
        service = self.get_service()

        try:
            # quote = service.get_quote(quote_code=quote_code)
            quote = Quote.objects.get(quote_code=quote_code)

            # # should fix the assertion error on the serializer instance
            # if isinstance(quote, QuoteSerializer):
            #     quote = quote.data
            serializer = QuoteSerializer(quote)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Quote.DoesNotExist:
            logger.error(f"Quote not found: {quote_code}")
            return Response(
                {"error": "Quote not found"}, status=status.HTTP_404_NOT_FOUND
            )
        except MultipleObjectsReturned as data_integrity_err:
            logger.error(
                f"Multiple quotes found for: {quote_code}. "
                f"ERROR: {str(data_integrity_err)}"
            )
            quote = Quote.objects.filter(quote_code=quote_code).first()
            return Response(quote, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"An error occurred while fetching quotes: {str(e)}")
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class RequestQuoteView(views.APIView):
    """
    This endpoint allows users to request an insurance quote by either creating a new quote or retrieving
    an existing quote based on a provided quote code. Users can specify details such as the product type,
    product name, and insurance details including coverage type to get an accurate quote.

    You can provide either:
    - A `quote_code` to retrieve an existing quote.
    - A `product_id` and `insurance_details` to request a new quote.
    - `product_type` and `insurance_name` along with optional `insurance_details` to create a new quote.

    ## Request Parameters

    - **quote_code** (str, optional): The unique identifier of an existing quote. If provided, the endpoint
      will retrieve the quote associated with this code.
    - **product_type** (str, optional): The type of insurance product (e.g., LIFE, AUTO, HEALTH). Required if
      `quote_code` is not provided.
    - **insurance_name** (str, optional): The name of the insurance product. Used along with `product_type`
      to find the product if `quote_code` is not provided.
    - **insurance_details** (dict, optional): A dictionary containing additional details for the insurance quote,
      including `coverage_type` and other specifics.

    ## Request Body Examples

    Examples of valid request payloads:

    - Requesting a new quote for travel insurance:
      ```json
      {
        "product_type": "TRAVEL",
        "insurance_name": "Travel Insurance",
        "insurance_details": {
          "coverage_type": "Silver"
        }
      }

      OR

      {
        "product_id": "c0883345-7566-42e7-8bb1-a62871261163",
        "insurance_name": "Travel Insurance",
        "insurance_details": {
          "coverage_type": "Silver"
        }
      }
    """

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
            # examples=[
            #     travel_insurance_example,
            #     travel_insurance_with_product_id_example,
            #     health_insurance_example,
            #     health_insurance_with_product_id_example,
            #     home_insurance_example,
            #     home_insurance_with_product_id_example,
            #     gadget_insurance_example,
            #     gadget_insurance_with_product_id_example,
            #     auto_insurance_example,
            #     auto_insurance_with_product_id_example,
            # ],
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
        # examples=[
        #     travel_insurance_example,
        #     health_insurance_example,
        #     auto_insurance_example,
        # ],
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


class QuoteRequestView(views.APIView):
    """
    View to handle insurance quote requests and return aggregated quotes.

    This endpoint allows merchants to request insurance quotes for various insurance products.
    The system aggregates quotes from different insurance providers based on the provided
    product type, product name, and coverage preferences. The response includes a list of
    available quotes, along with detailed information such as coverage, premium, exclusions,
    and provider information.

    The request body requires customer metadata, insurance product details, and coverage preferences.

    Example Request Body: SEE API REQUEST EXAMPLE
    """

    # filterset_backend = [DjangoFilterBackend]
    # filterset_class = QuoteFilter

    @extend_schema(
        summary="Request a quote for an insurance policy or product",
        description="Submit a request to generate insurance quotes for a specified product type and customer details. Allows filtering by provider, coverage type, and sorting.",
        tags=["Quotes"],
        request=OpenApiRequest(
            request=QuoteRequestSerializerV2(many=True),
            examples=[quote_request_example],
        ),
        responses={
            200: OpenApiResponse(
                response=QuoteResponseSerializerV2(many=True),
                description="The response contains a list of available quotes from different providers.",
            )
        },
    )
    def post(self, request, *args, **kwargs):
        serializer = QuoteRequestSerializerV2(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        validated_data = serializer.validated_data
        service = QuoteServiceV2()

        try:
            quote_data = async_to_sync(service.request_quote)(validated_data)
            logger.info(f"Retrieved Quote Data: {quote_data}")
            print(f"Type of quote_data: {type(quote_data)}")
            paginator = LimitOffsetPagination()
            paginated_quotes = paginator.paginate_queryset(quote_data, request)

            if quote_data == []:
                return Response(
                    {
                        "error": "No quotes found for the provided criteria. Try query again"
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )

            if paginated_quotes is not None:
                response_serializer = QuoteResponseSerializerV2(
                    paginated_quotes, many=True
                )
                serializer_data = response_serializer.data
                return paginator.get_paginated_response(serializer_data)

            response_serializer = QuoteResponseSerializerV2(quote_data, many=True)
            serializer_data = response_serializer.data
            return Response(
                {
                    "message": "Quote successfully retrieved",
                    "data": serializer_data,
                },
                status=status.HTTP_200_OK,
            )
        except ValueError as exc:
            logger.error(f"Validation error: {exc}", exc_info=True)
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            logger.critical(f"Error occurred: {exc}", exc_info=True)
            return Response(
                {"error": "An error occurred while processing your request."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @deprecated("This method is no longer supported")
    def _apply_filters(self, request: Request, qs: QuerySet):
        """
        Uses QuoteFilter to apply filtering logic onto incoming request
        """
        filterset = self.filterset_class(request.query_params, queryset=qs)
        return filterset.qs

    @deprecated("This method is no longer supported")
    def _sort_queryset(self, request: Request, filtered_qs: QuerySet):
        """
        Apply sorting onto a filtered queryset and returns a filtered quotes
        """
        query_params = request.query_params

        # SORTING LOGIC
        #
        # SORT BY 'BEST_VALUE' OR 'CHEAPEST'
        sort_by = query_params.get("sort_by")

        if sort_by == "cheapest":
            filtered_qs = filtered_qs.order_by("premium__amount")
        elif sort_by == "best_coverage":
            # HERE WE ARE RETRIEVEING THE LIMIT OF THE QUOTE COVERAGE
            # FROM THE ADDITONAL_METADATA FIELD ON THE QUOTE OBJECT
            # WHICH IS A JSON FILED, WE WANT TO HOWEVER PASS DECIMAL
            # OBJECT INTO THE QUERYSET MANAGER
            COVERAGE_LIMIT = F("additional_metadata__coverage_limit")
            PREMIUM_AMOUNT = F("premium__amount")

            # import pdb
            #
            # pdb.set_trace()
            filtered_qs = filtered_qs.annotate(
                # See: https://devdocs.io/django~5.0/ref/models/database-functions#django.db.models.functions.Cast
                # Coalesce here, because initally its found that some of our coverage limit
                # values have null values been passed into this function hence breaking the feature
                # coverage_limit=Coalesce(
                #     Cast(COVERAGE_LIMIT, DecimalField()), Cast(Value(0), DecimalField())
                # ),
                # NullIf is used to treat "none" as NULL, and Coalesce ensures it defaults to 0 if NULL.
                coverage_limit=Coalesce(
                    Cast(NullIf(COVERAGE_LIMIT, Value("none")), DecimalField()),
                    Cast(Value(0), DecimalField()),
                ),
                value_ratio=(
                    F("coverage_limit") / Cast(PREMIUM_AMOUNT, DecimalField())
                ),
            ).order_by("-value_ratio")
            print(filtered_qs)
        return filtered_qs


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


@extend_schema(
    summary="View all coverages associated with an insurance product",
    tags=["Coverage"],
    responses={
        200: OpenApiResponse(
            response=CoverageSerializer,
            description="List of all coverages associated with an insurance product",
            examples=[
                OpenApiExample(
                    "Coverage List Example",
                    value=[
                        {
                            "coverage_id": "COV_uklZyZPPrN2M",
                            "coverage_name": "Travel Medical Emergency",
                            "coverage_limit": "10000.00",
                            "currency": "NGN",
                            "description": "Covers emergency medical expenses incurred while traveling.",
                            "coverage_period_end": "2024-12-31",
                            "benefits": "Covers hospitalization, medical evacuation, and repatriation.",
                            "exclusions": "Does not cover pre-existing conditions or routine medical visits.",
                        },
                        {
                            "coverage_id": "COV_kPvXWWVqGtoz",
                            "coverage_name": "Homeowners Insurance",
                            "coverage_limit": "50000.00",
                            "currency": "NGN",
                            "description": "Covers damage to the home and personal belongings due to various risks.",
                            "coverage_period_end": "2024-12-31",
                            "benefits": "Covers damage from fire, theft, and natural disasters.",
                            "exclusions": "Does not cover damage from intentional acts or wear and tear.",
                        },
                    ],
                ),
            ],
        ),
        404: OpenApiResponse(description="No coverages found for this product"),
        400: OpenApiResponse(description="Bad Request"),
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
class ProductCoverageListView(generics.ListAPIView):
    """
    Returns list of all coverages associated with a certain product
    """

    serializer_class = CoverageSerializer

    def get_queryset(self):
        product_id = self.kwargs["product_id"]
        try:
            product = Product.objects.get(pk=product_id)
        except Product.DoesNotExist:
            raise NotFound("Product Not Found")
        return product.coverages.all()


@extend_schema(
    summary="View the coverage information regarding an insurance product ",
    description="With this endpoint you can view the coverage information regaridng a certain insurance product to get insights on what is going on.",
    tags=["Coverage"],
    responses=OpenApiResponse(
        response=FullCoverageSerializer,
        description="Coverage Information",
        examples=[
            OpenApiExample(
                "Coverage",
                value={
                    "coverage_id": "COV_uklZyZPPrN2M",
                    "coverage_name": "Travel Medical Emergency",
                    "coverage_limit": "10000.00",
                    "currency": "NGN",
                    "description": "Covers emergency medical expenses incurred while traveling.",
                    "coverage_period_end": "2024-12-31",
                    "benefits": "Covers hospitalization, medical evacuation, and repatriation.",
                    "exclusions": "Does not cover pre-existing conditions or routine medical visits.",
                },
            )
        ],
    ),
)
class ProductCoverageRetrieveView(generics.RetrieveAPIView):
    """
    View the coverage information regarding an insurance product
    """

    queryset = Coverage.objects.all()
    serializer_class = FullCoverageSerializer

    def get_object(self) -> QuerySet:
        product_id = self.kwargs["product_id"]
        coverage_id = self.kwargs["coverage_id"]

        try:
            product = Product.objects.get(pk=product_id)
            coverage = product.coverages.get(coverage_id=coverage_id)
        except Product.DoesNotExist:
            logger.error(f"Product with ID: {product_id} does not exist")
            raise NotFound("Product not found!")
        except Coverage.DoesNotExist:
            logger.error(f"Coverage with ID: {coverage_id} does not exist")
            raise NotFound("Coverage not found")
        except MultipleObjectsReturned as exc:
            logger.error(f"Multiple object returned by product id: {product_id}")
            raise Exception(
                {"error": f"Multiple Objects returned by product id: {product_id}"},
            ) from exc
        except Exception as e:
            raise e

        return coverage


@extend_schema(
    summary="Search for insurance coverages",
    description=(
        "This API allows users to search for insurance coverages using various filters. "
        "Admin users (staff - customer-support) have additional access to search using the insurer name and insurer ID. "
        "Non-admin users can only search by coverage name, coverage ID, and product ID."
    ),
    tags=["Coverage"],
    parameters=[
        OpenApiParameter(
            "coverage_name",
            description="Case-insensiteive name of the coverage you are trying to search. We allow partial and exact matches of your query",
        ),
        OpenApiParameter(
            "coverage_id",
            type=OpenApiTypes.STR,
            description="Unique string-generated ID of the coverage",
            examples=[OpenApiExample("example coverage id", value="COV_uklZyZPPrN2M")],
        ),
        OpenApiParameter(
            "product_id",
            type=OpenApiTypes.UUID,
            description="Unique resource identifier of the product",
        ),
        OpenApiParameter(
            "insurer_name",
            description=(
                "Admin-only filter. Case-insensitive search by insurer name. "
                "This filter is accessible only to customer support users."
            ),
            required=False,
            type=OpenApiTypes.STR,
            examples=[
                OpenApiExample("Partial match", value="Health Plus"),
                OpenApiExample("Exact match", value="Global Insurers Ltd."),
            ],
        ),
        OpenApiParameter(
            "insurer_id",
            type=OpenApiTypes.UUID,
            description="Admin-only filter. Search by unique insurer ID (UUID). Accessible only to admin users.",
            required=False,
        ),
    ],
    responses=OpenApiResponse(
        response=CoverageSerializer,
        description="Coverage Search Results",
        examples=[
            OpenApiExample(
                "Coverage Search Results",
                value=[
                    {
                        "coverage_id": "COV_uklZyZPPrN2M",
                        "coverage_name": "Travel Medical Emergency",
                        "coverage_limit": "10000.00",
                        "currency": "NGN",
                        "description": "Covers emergency medical expenses incurred while traveling.",
                        "coverage_period_end": "2024-12-31",
                        "benefits": "Covers hospitalization, medical evacuation, and repatriation.",
                        "exclusions": "Does not cover pre-existing conditions or routine medical visits.",
                    },
                    {
                        "coverage_id": "COV_kPvXWWVqGtoz",
                        "coverage_name": "Homeowners Insurance",
                        "coverage_limit": "50000.00",
                        "currency": "NGN",
                        "description": "Covers damage to the home and personal belongings due to various risks.",
                        "coverage_period_end": "2024-12-31",
                        "benefits": "Covers damage from fire, theft, and natural disasters.",
                        "exclusions": "Does not cover damage from intentional acts or wear and tear.",
                    },
                ],
            )
        ],
    ),
)
class ProductCoverageSearchView(generics.ListAPIView):
    """
    Search for an insurance coverage on the platform using specific paramaters
    """

    serializer_class = CoverageSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, AdminOnlyInsurerFilterPermission]

    def get_queryset(self) -> QuerySet:
        # we want to allow both partial and exact case insentive matches
        # since the likely application of this one is on a dashboard
        query_params = self.request.query_params
        q = Q()

        coverage_name = query_params.get("coverage_name")
        coverage_id = query_params.get("coverage_id")
        product_id = query_params.get("product_id")
        insurer_name = query_params.get("insurer_name")
        insurer_id = query_params.get("insurer_id")

        if coverage_name:
            q &= Q(coverage_name__icontains=coverage_name)
            logger.debug(f"Filtering by coverage_name: {coverage_name}")

        if coverage_id:
            q &= Q(coverage_id__icontains=coverage_id)
            logger.debug(f"Filtering by coverage_id: {coverage_id}")

        if product_id:
            q &= Q(product__id=product_id)

        # filter by insurer naeme (this, is an indirect filteration process)
        #
        # We have to reverse-filter through Product -> Provider relationship
        if insurer_name:
            q &= Q(product__provider__name__icontains=insurer_name)

        if insurer_id:
            q &= Q(product__provider__id=insurer_id)

        try:
            queryset = Coverage.objects.filter(q)
            logger.debug(f"Queryset retrieved: {queryset}")
            return queryset
        except Exception as e:
            logger.error(f"Error during queryset retrieval: {str(e)}")
            raise e
