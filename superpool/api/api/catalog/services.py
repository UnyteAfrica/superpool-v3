from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Any, Dict, NewType, Union

from rest_framework.generics import get_object_or_404

from api.catalog.exceptions import ProductNotFoundError, QuoteNotFoundError
from core.catalog.models import Policy, Product, Quote
from core.merchants.models import Merchant
from core.user.models import Customer
from django.core.mail import send_mail
from django.db import models
from django.db.models import Q, QuerySet
from rest_framework.serializers import ValidationError
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.exceptions import APIException

import logging

logger = logging.getLogger(__name__)


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
    def get_product(product_name: str) -> Product:
        """
        Returns a product by name
        """
        return get_object_or_404(Product, name=product_name)

    @staticmethod
    def get_product_by_id(product_id: int) -> Product:
        """
        Returns a product by id
        """
        return get_object_or_404(Product, id=product_id)


############################################################################################################
#
# POLICY SERVICE
#
############################################################################################################
class PolicyService:
    """
    Service class for the Policy model
    """

    @staticmethod
    def validate_policy(policy_id: str | None = None, policy_number: str | None = None):
        """
        Validates a policy using either the policy ID or policy number
        """

        if not policy_id and not policy_number:
            raise ValidationError(
                "Policy identifier is required. Either policy id or policy number must be provided"
            )

        # check if the policy exists and is active
        if (
            policy_id
            and not Policy.objects.filter(policy_id=policy_id, status="active").exists()
        ):
            raise ValidationError("Policy not found or already cancelled")
        elif (
            policy_number
            and not Policy.objects.filter(
                policy_number=policy_number, status="active"
            ).exists()
        ):
            return ValidationError("Policy not found or already cancelled")

        # policy is active and exist, so we return an identifier
        return policy_id or policy_number

    @staticmethod
    def renew_policy(policy: Policy, expiry_date: datetime) -> Policy:
        """
        Renews a policy using the given policy data
        """
        from api.notifications.services import PolicyNotificationService

        # In production, We want to update the status of a policy in our db, consequently sending an api call to the insurer
        # with the provided information, and return it back to the merchant
        policy.effective_through = expiry_date
        policy.save()

        # send notification emails to stakeholders - in this case, our merchant  and their customer
        PolicyNotificationService.notify_merchant("renew_policy", policy)
        PolicyNotificationService.notify_customer("renew_policy", policy)

        # Trigger background task to renew policy with the insurer and set the policy status to renewed
        # Once policy is renewed, notify the merchant of a status update and notify the merchant of the renewal

        return policy

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
        from api.notifications.services import PolicyNotificationService

        # In production, We want to update the status of a policy in our db, consequently sending an api call to the insurer
        # with the provided information, and return it back to the merchant
        try:
            policy = Policy.objects.get(policy_id=policy_identifier)

            policy.status = "cancelled"
            policy.cancellation_reason = reason
            policy.cancellation_date = datetime.now()
            policy.save()

            # send notification emails to stakeholders - in this case, our merchant  and their customer
            PolicyNotificationService.notify_merchant("cancel_policy", policy)
            PolicyNotificationService.notify_customer("cancel_policy", policy)

            return {
                "message": "Policy cancelled successfully.",
                "status": policy.status,
                "policy_id": policy.policy_id,
                "cancellation_reason": policy.cancellation_reason,
                "cancellation_date": policy.cancellation_date,
            }
        except Policy.DoesNotExist:
            raise Exception("Policy not found")
        except Exception as exc:
            raise Exception(f"An error occured during policy cancellation: {str(exc)}")

    @staticmethod
    def purchase_policy(validated_data: dict) -> Policy:
        """
        Purchase a policy using the given policy data

        Returns:

            Policy created policy object
        """
        from api.notifications.services import PolicyNotificationService

        quote_service = QuoteService()
        quote_code = validated_data["quote_code"]

        try:
            # retrieve quote information and process it
            quote_code = validated_data["quote_code"]
            quote_data = quote_service._get_quote_by_code(quote_code)
            if not quote_data:
                raise ValidationError(f"Quote with code {quote_code} does not exist")

            # extract information about the product and the applicable premium from the quote
            product = quote_data.data.get("product")
            premium = quote_data.data.get("price", {}).get("amount")

            # validate incoming data where neccessary
            customer_metadata = validated_data["customer_metadata"]
            product_metadata = validated_data["product_metadata"]
            payment_information = validated_data["payment_metadata"]
            activation_details = validated_data["activation_metadata"]

            # handle payment validation
            PolicyService._validate_payment(payment_information, premium)

            # are we renewing the policy?
            renewal_date = (
                activation_details.get("policy_expiry_date") + timedelta(days=1)
                if activation_details.get("renew")
                else None
            )
            # next, we want to process merhant and customer information
            customer = PolicyService._create_or_retrieve_customer(customer_metadata)
            merchant = PolicyService._get_merchant(validated_data["merchant_code"])

            # process policy purchase
            policy = PolicyService._create_policy(
                customer,
                product,
                premium,
                merchant,
                quote_data["provider"],
                activation_details,
                renewal_date=renewal_date,
            )

            # notify the merchant and customer
            PolicyNotificationService.notify_merchant("purchase_policy", policy)
            PolicyNotificationService.notify_customer(
                "purchase_policy", policy, customer_metadata["customer_email"]
            )

            return policy
        except ObjectDoesNotExist:
            logger.error("Policy not found")
            raise ValidationError("Policy not found")

        except Exception as exc:
            logger.error(
                f"Unexpected error occurred in PolicyService while purhcasing the policy: {str(exc)}"
            )
            raise APIException(
                "An unexpected error occurred while processing the policy purchase."
            )

    @staticmethod
    def _create_policy(
        customer,
        product,
        policy_price,
        merchant,
        policy_provider,
        activation_details,
        **kwargs,
    ):
        """
        Handles the actual creation of a policy

        Arguments:
            customer: The customer object
            product: The product object
            policy_price: The price of the policy
            merchant: The merchant object
            policy_provider: The insurance provider of the policy
            activation_details: The polcy activation details
            kwargs: Additional keyword arguments

        Returns:
            The created policy object
        """

        renewal_date = kwargs.get("renewal_date", None)
        return Policy.objects.create(
            policy_holder=customer,
            product=product,
            premium=policy_price,
            merchant=merchant,
            provider_id=policy_provider,
            renewable=activation_details.get("renew"),
            renewal_date=renewal_date,
            effective_from=datetime.now().date(),
            effective_through=activation_details.get("policy_expiry_date"),
        )

    @staticmethod
    def _get_merchant(merchant_code):
        """
        Retrieves a merchant by their unique code
        """

        try:
            merchant = Merchant.objects.get(short_code=merchant_code, status="active")
        except Merchant.DoesNotExist:
            raise ValidationError(
                f'Merchant with the provided short code "{merchant_code}" not found'
            )
        return merchant

    @staticmethod
    def _create_or_retrieve_customer(customer_data):
        """
        Creates a new policy holder or retrieves an existing one
        """
        return Customer.objects.get_or_create(
            email=customer_data["customer_email"],
            defaults={
                "first_name": customer_data["first_name"],
                "last_name": customer_data["last_name"],
                "phone_number": customer_data["customer_phone"],
                "address": customer_data["customer_address"],
                "dob": customer_data["customer_date_of_birth"],
                "gender": customer_data["customer_gender"],
            },
        )[0]

    @staticmethod
    def _validate_payment(payment_information, policy_price):
        """
        Validates the payment information of a given policy
        """
        # Check if payment status is sucessful
        if payment_information["payment_status"] != "completed":
            raise ValidationError("Payment status must be completed to proceed")

        # Check if the amount paid matches the policy price
        if premium_amount := payment_information.get("premium_amount"):
            if premium_amount != policy_price.amount:
                raise ValidationError("Amount paid does not match the policy price")
        return payment_information


############################################################################################################
#
# QUOTE SERVICE
#
############################################################################################################
class IQuote(ABC):
    @abstractmethod
    def get_quote(
        self,
        product,
        product_name,
        quote_code=None,
        insurance_details=None,
        batch=False,
        **kwargs,
    ):
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
    def _get_all_quotes_for_product(
        self, product_type, product_name=None, insurance_details: Dict[str, Any] = None
    ):
        """
        Retrieves all quotes for a given product type and optional product name.

        Arguments:

            product_type: The type of insurance product.
            product_name: The specific name of the insurance product.
            insurance_details: Additional details specific to the insurance type.

        Returns:
            A list of quotes.
        """
        from api.catalog.serializers import QuoteSerializer

        try:
            if product_name:
                products = Product.objects.filter(
                    Q(product_type=product_type) & Q(name=product_name)
                )
            else:
                products = Product.objects.filter(product_type=product_type)

            if not products.exists():
                logger.error(
                    f"No products found for type {product_type} and name {product_name}"
                )
                raise ProductNotFoundError("Product not found.")

            quotes = Quote.objects.filter(product_in=products)
            if not quotes.exists():
                logger.error(f"No quotes found for the given product: {product_name}")
                raise QuoteNotFoundError("No quotes found for the given product.")

            serializer = QuoteSerializer(quotes, many=True)
            return serializer.data
        except Product.DoesNotExist:
            logger.error(
                f"Product does not exist for type {product_type} and name {product_name}"
            )
            raise ProductNotFoundError("Product not found.")

    def _get_quote_by_code(self, quote_code):
        from api.catalog.serializers import QuoteSerializer

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
        insurance_details: Dict[str, Any] = None,
        batch: bool = False,
        **kwargs,
    ):
        """
        Retrieves insurance quotes for an insurance policy

        Arguments:

            product: The type of insurance product.
            product_name: The specific name of the insurance product.
            quote_code: A unique code for the insurance quote.
            insurance_details: Additional details specific to the insurance type.
            batch: Flag to indicate if multiple quotes should be retrieved.
            kwargs: Additional arguments for future extensions.

        Returns:
            A quote or list of quotes.
        """
        insurance_details = insurance_details or {}

        if quote_code:
            return self._get_quote_by_code(quote_code=quote_code)
        elif product:
            return self._get_all_quotes_for_product(
                product_type=product,
                product_name=product_name,
                insurance_details=insurance_details,
            )
        else:
            raise ValueError("Either product, or quote_code must be provided.")

    def update_quote(self, quote_code, data):
        """
        Updates the information and metadata of an existing quote
        """
        from api.catalog.serializers import QuoteSerializer

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
