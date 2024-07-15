import logging
import uuid

from api.app_auth.authentication import APIKeyAuthentication
from core.catalog.models import Policy, Product, Quote
from django.db import transaction
from django.db.models import QuerySet
from drf_spectacular.utils import extend_schema
from rest_framework import generics, mixins, status, views, viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import Serializer

from .serializers import PolicyPurchaseSerializer, PolicySerializer, ProductSerializer
from .services import PolicyService, ProductService

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
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    queryset = PolicyService.list_policies()
    authentication_classes = [APIKeyAuthentication]

    def get_serializer_class(self):
        if self.action == "create":
            return PolicyPurchaseSerializer
        return PolicySerializer

    @action(detail=False, methods=["post"])
    def purchase(self, request, *args, **kwargs):
        """
        This action allows you to generate a new policy for your
        customer
        """
        # generate a new policy for the customer
        # Construct a new policy object, and return both the policy number and the policy ID

        # emit a policy purchased signal that fires up a background task to notify the admins
        # of the platform

        # fires off a background process that post (actually register the customer info) and
        # the policy information to the insurer endpoint
        # (we should just call a function in a service that would integrate the Insurer APIs)

        # returrn the policy ID, Policy Number, and the status of the policy to the merchant

        pass

    @action(detail=False, methods=["post"])
    def renew(self, request, *args, **kwargs):
        """
        This action allows you as a merchant to submit a renewal
        request for your customer
        """
        # This should grab the policy instance from the database

        # It should should check if update a policy  is renewable
        # if it is, it should update the details of a policy with
        # new set of information: specifically, the effective_from
        # and the effective to

        # Return the updated policy from the database to the user

        # NOTE: ALTHOUGH WE HAVE A FIELD, renewable in our django models for Policy,
        # WE SHOULD PROBABLY ADD RENEWED or IS_RENEWED TO CHECK IF A POLICY HAS BEEN
        # RENEWED AND TO DIFFERENTIATE IT FROM NON-RENEWED POLICIES

        pass

    def retrieve(self, request, pk=None):
        """
        Retrieve a specific policy by its ID
        """
        pass

    @action(details=False, methods=["post"])
    def search(self, request, **extra_kwargs):
        """
        Action that allows you to search or filter for a policy based on
        certain parameters.

        Params are not limited to, customer details, status of the policy,
        policy category
        """
        # We want to do a pattern match here, depending on query params
        pass


class ProductAPIViewSet(viewsets.GenericViewSet):
    # endpoint to search and filter for product based on query parameters

    # endpoint to get a product belonging to a specific insurer
    pass


class QuoteView(generics.RetrieveAPIView):
    # endpoint to get a quote on a Policy from the database or cache,
    # if it exists it retrieves it, otherwise it call the Insurer's API
    # to retrieve new quotes and save it to the database

    # update endpoint that updates our local database at the end of every day with
    # realtime prices from the insurers a quote should be associated with a policy, under
    # a product and an associated insurer
    # NOTE: UPDATE: THIS SHOULD NOT BE AN ENDPOINT IT SHOULD BE A CELERY TASK OR SOMETHING
    # THIS COULD INFACT BE DESIGNED IN SOLID_PRINCIPLES, EACH INSURER WOULD HAVE THEIR OWN
    # QUOTE UPDATER THAT WOULD UPDATE THE DATABASE, HENCE EASIER FOR DEBUGGING AND TROBULESHOOTING

    pass
