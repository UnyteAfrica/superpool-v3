from core.catalog.models import Product
from django.db.models import QuerySet
from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import Serializer

from .serializers import PolicySerializer, ProductSerializer
from .services import PolicyService, ProductService


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
