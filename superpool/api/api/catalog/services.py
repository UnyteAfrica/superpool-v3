from abc import ABC, abstractmethod

from api.catalog.exceptions import QuoteNotFoundError
from core.catalog.models import Policy, Product, Quote
from django.db import models
from django.db.models import QuerySet


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
    def get_quote(self, product, batch=False):
        """Retrieves an insurance quotation on a policy. if batch is selected returns a list of quotes from multiple insurers instead."""
        return NotImplementedError()

    # compute methods for traditional insurers
    def calculate_premium(self):
        """Calculates the premium based on the selected product, coverages, customer profile, and other relevant factors."""
        pass

    @staticmethod
    def generate_pdf():
        """Generates a PDF document of the quote."""
        pass

    def accept(self):
        """Converts the quote into a policy"""
        pass

    def decline(self, quote):
        """Sets the quote status to declined."""
        pass


class QuoteService(IQuote):
    def get_quote(self, product, batch=False):
        if batch:
            # TODO: Implement a logic for listing multiple quotes
            pass

        quote = Quote.objects.filter(product=product).distinct()
        if not quote:
            raise QuoteNotFoundError("No quote found for the given product.")
        return quote
