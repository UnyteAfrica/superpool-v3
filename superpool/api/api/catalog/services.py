from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, NewType, Union

from api.catalog.exceptions import ProductNotFoundError, QuoteNotFoundError
from core.catalog.models import Policy, Product, Quote
from django.core.mail import send_mail
from django.db import models
from django.db.models import Q, QuerySet
from rest_framework.serializers import ValidationError

from .serializers import PolicyCancellationResponseSerializer, QuoteSerializer

CustomerT = NewType("CustomerT", str)
""" Denotes a Customer Type"""
MerchantT = NewType("MerchantT", str)
""" Denotes a Merchant Type"""


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

    @staticmethod
    def notify(
        who: MerchantT | CustomerT, action: str | dict, policy: Policy
    ) -> dict[str, Any]:
        """
        Notify a stakeholder about an action that took place on this policy

        Arguments:
            action: context to include in the mail to be sent to this stakeholder
            who: the stakeholder, who is of string type Customer or string type Merchant
        """
        return {}

    @staticmethod
    def _notify_merchant(action, policy) -> None | Exception:
        """Send a notification to the merchant about the action that took place on the policy"""

        from django.conf import settings

        ACTION_TITLE_TEMPLATE = {
            "purchase_policy": "Policy Purchase Notification - A new policy has been purchased.",
            "accept_policy": "Policy Confirmation - A new policy has been accepted.",
            "cancel_policy": "Policy Cancellation Notification",
            "status_update": "Policy Status Update - A policy status has been updated.",
        }

        try:
            send_mail(
                f"{ACTION_TITLE_TEMPLATE[action]}",
                f"The policy {policy.policy_number} sold by you has been {ACTION_TITLE_TEMPLATE[action]}. Please take note.",
                f"{settings.DEFAULT_FROM_EMAIL}",
                [policy.merchant_id.email],
            )
        except Exception as exc:
            raise Exception(
                f"An error occured during merchant notification: {str(exc)}"
            )

    @staticmethod
    def _notify_customer(action, policy, channel) -> None | Exception:
        """Notify the customer about the action that took place on their policy"""

        from django.conf import settings

        ACTION_TITLE_TEMPLATE = {
            "purchase_policy": "Policy Purchase Successful - We've got your back!. Your policy has been purchased.",
            "accept_policy": "Your policy has been accepted.",
            "cancel_policy": "Policy Cancellation Confirmation - Your policy has been cancelled.",
            "status_update": "Policy Status Update - Your policy status has been updated.",
        }
        try:
            send_mail(
                f"{ACTION_TITLE_TEMPLATE[action]}",
                f"Your policy {policy.policy_number} has been cancelled.",
                f"{settings.DEFAULT_FROM_EMAIL}",
                [policy.policy_holder.email],
            )
        except Exception as exc:
            raise Exception(
                f"An error occured during merchant notification: {str(exc)}"
            )

    @staticmethod
    def cancel_policy(policy_identifier: str, reason: str) -> dict | Exception:
        """
        Initiate a cancellation request using the given policy data

        Policy cancellation can be initiated either using the policy reference number or the assigned
        policy ID.

        Returns:

            PolicyCancellationResponseSerializer (dict) a formatted response object in form of a python dictionary

            OR

            Exception an error message indicating failure of opertion
        """
        from api.notifications.services import NotificationService

        # In production, We want to update the status of a policy in our db, consequently sending an api call to the insurer
        # with the provided information, and return it back to the merchant
        try:
            policy = Policy.objects.get(policy_id=policy_identifier)

            policy.status = "cancelled"
            policy.cancellation_reason = reason
            policy.cancellation_date = datetime.now()
            policy.save()

            # send notification emails to stakeholders - in this case, our merchant  and their customer
            NotificationService.notify("merchant", "cancel_policy", policy)
            NotificationService.notify("customer", "cancel_policy", policy)

            return {
                "status": policy.status,
                "message": "Policy cancelled successfully.",
                "policy_id": policy.policy_id,
                "cancellation_reason": policy.cancellation_reason,
                "cancellation_date": policy.cancellation_date,
            }
        except Policy.DoesNotExist:
            raise Exception("Policy not found")
        except Exception as exc:
            raise Exception(f"An error occured during policy cancellation: {str(exc)}")


class IQuote(ABC):
    @abstractmethod
    def get_quote(self, product, product_name, quote_code=None, batch=False):
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
    def _get_all_quotes_for_product(self, product_type, product_name=None):
        try:
            if product_name:
                product = Product.objects.filter(
                    Q(product_type=product_type) | Q(product_name=product_name)
                )
            product = Product.objects.get(product_type=product_type)
            quotes = Quote.objects.filter(product=product)
            if not quotes:
                raise QuoteNotFoundError("No quotes found for the given product.")
            serializer = QuoteSerializer(quotes, many=True)
            return serializer
        except Product.DoesNotExist:
            raise ProductNotFoundError("Product not found.")

    def _get_quote_by_code(self, quote_code):
        try:
            quote = Quote.objects.get(quote_code=quote_code)
            serializer = QuoteSerializer(quote)
            return serializer
        except Quote.DoesNotExist:
            raise QuoteNotFoundError("Quote not found.")

    def get_quote(
        self,
        product: Union[str, None] = None,
        product_name: Union[str, None] = None,
        quote_code: Union[str, None] = None,
        batch=False,
    ):
        """
        Retrieves insurance quotes for an insurance policy
        """
        if product and product_name:
            return self._get_all_quotes_for_product(
                product_type=product, product_name=product_name
            )
        elif product:
            return self._get_all_quotes_for_product(product_type=product)
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
