from abc import ABC, abstractmethod
from typing import Union

from api.catalog.exceptions import ProductNotFoundError, QuoteNotFoundError
from core.catalog.models import Policy, Product, Quote
from django.db import models
from django.db.models import QuerySet
from rest_framework.serializers import ValidationError

from .serializers import QuoteSerializer


class ProductService:
    """
    Service class for the Product model
    """

    @staticmethod
    def list_products() -> QuerySet:
        """
        Returns a queryset of all products
        """
        return Product.objects.all()

    @staticmethod
    def get_product(name: str) -> Product:
        """
        Returns a product by name
        """
        return Product.objects.get(models.Q(name=name)).select_related("provider_id")

    @staticmethod
    def get_product_by_id(product_id: int) -> Product:
        """
        Returns a product by id
        """
        return Product.objects.get(models.Q(id=product_id)).select_related(
            "provider_id"
        )


class PolicyService:
    """
    Service class for the Policy model
    """

    @staticmethod
    def list_policies() -> QuerySet:
        """
        Returns a queryset of all policies
        """
        return Policy.objects.all()

    @staticmethod
    def list_policies_by_product_type() -> QuerySet:
        """
        Returns a queryset of all policies by product type
        """
        return Policy.objects.filter(
            models.Q(product__product_type=models.F("product_type"))
        ).select_related("product", "provider_id")


class IQuote(ABC):
    @abstractmethod
    def get_quote(self, product, quote_code=None, batch=False):
        """Retrieves an insurance quotation on a policy. if batch is selected returns a list of quotes from multiple insurers instead."""
        raise NotImplementedError()

    # compute methods for traditional insurers
    def calculate_premium(self):
        """Calculates the premium based on the selected product, coverages, customer profile, and other relevant factors."""
        pass

    @staticmethod
    def generate_pdf():
        """Generates a PDF document of the quote."""
        pass

    def accept_quote(self, quote):
        """Converts the quote into a policy"""
        pass

    def decline_quote(self, quote):
        """Sets the quote status to declined."""
        pass


class QuoteService(IQuote):
    def _get_all_quotes_for_product(self, product_code):
        try:
            product = Product.objects.get(code=product_code)
            quotes = Quote.objects.filter(product=product)
            if not quotes:
                raise QuoteNotFoundError("No quotes found for the given product.")
            serializer = QuoteSerializer(quotes, many=True)
            return serializer.data
        except Product.DoesNotExist:
            raise ProductNotFoundError("Product not found.")

    def _get_quote_by_code(self, quote_code):
        try:
            quote = Quote.objects.get(quote_code=quote_code)
            serializer = QuoteSerializer(quote)
            return serializer.data
        except Quote.DoesNotExist:
            raise QuoteNotFoundError("Quote not found.")

    def get_quote(
        self,
        product: Union[str, None] = None,
        quote_code: Union[str, None] = None,
        batch=False,
    ):
        """
        Retrieves insurance quotes for an insurance policy
        """
        if batch and product is not None:
            return self._get_all_quotes_for_product(product_code=product)
        return self._get_quote_by_code(quote_code=quote_code)

    def update_quote(self, quote_code, data):
        """
        Updates the information and metadata of an existing quote
        """
        try:
            # get the quote from the database and update it with new
            # information
            quote = Quote.objects.get(quote_code=quote_code)
            serializer = QuoteSerializer(quote, data=data, partial=True)
            if serializer.is_valid(raise_exception=True):
                serializer.save()
                return serializer.data
        except Quote.DoesNotExist:
            raise QuoteNotFoundError("Quote not found.")

    def accept_quote(self, quote):
        if quote:
            customer_metadata = getattr(quote, "customer_metadata", {})
            # Create a corresponding Policy object with the information on the quote
            policy_payload = {
                "product": quote.product,
                "customer": customer_metadata,
                "provider_name": quote.provider.name,
                "provider_id": quote.provider.name,
                "premium": quote.premium,
            }
            policy_id, policy = Policy.objects.create(**policy_payload)
            return policy_id, policy
