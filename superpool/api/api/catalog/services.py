from abc import ABC, abstractmethod
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, NewType, Union
from api.notifications.base import NotificationService
from core.models import Coverage
from core.providers.models import Provider as InsurancePartner
from django.db import transaction

from rest_framework.generics import get_object_or_404

from api.catalog.exceptions import ProductNotFoundError, QuoteNotFoundError
from core.catalog.models import Policy, Price, Product, Quote
from core.merchants.models import Merchant
from core.user.models import Customer
from django.core.mail import send_mail
from django.utils import timezone
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
    def get_product_by_name(product_name: str) -> QuerySet:
        """
        Returns a list of products by name.
        If multiple products with the same name exist, they will all be returned.
        """
        return Product.objects.filter(name__iexact=product_name)

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
    @transaction.atomic
    def renew_policy(
        policy_id: str | None = None,
        policy_number: str | None = None,
        policy_start_date=None,
        policy_expiry_date=None,
        include_additional_coverage=False,
        modify_exisitng_coverage=False,
        coverage_details: dict | None = None,
        auto_renew=False,
    ):
        """
        Renews a policy using the given policy data
        """
        from api.notifications.services import PolicyNotificationService

        try:
            if policy_id:
                policy = Policy.objects.get(policy_id=policy_id)
            elif policy_number:
                policy = Policy.objects.get(policy_number=policy_number)

            if policy.status != "active":
                policy.status = "active"

            # check if the policy is already active and within its valid effective period
            today = timezone.now().date()
            if policy.effective_from <= today <= policy.effective_through:
                raise ValidationError(
                    "Policy is currently active and within its valid effective period. Renewal is not needed."
                )

            if policy_start_date:
                policy.effective_from = policy_start_date
            if policy_expiry_date:
                policy.effective_through = policy_expiry_date
            policy.renewal_date = policy_expiry_date + timedelta(days=1)

            if include_additional_coverage:
                # TODO: Implement this later
                raise NotImplementedError(
                    "Additional coverage implementation is not yet available."
                )
            if modify_exisitng_coverage:
                # TODO: implement this later
                raise NotImplementedError(
                    "Modification of existing coverage is not yet available."
                )

            update_fields = [
                "status",
                "effective_from",
                "effective_through",
                "renewal_date",
            ]
            policy.save(update_fields=update_fields)

            transaction_date = policy.created_at.strftime("%Y-%m-%d %H:%M:%S")
            customer = {
                "first_name": policy.policy_holder.first_name,
                "last_name": policy.policy_holder.last_name,
                "customer_email": policy.policy_holder.email,
            }
            try:
                PolicyNotificationService.notify_merchant(
                    "renew_policy",
                    policy,
                    customer=customer,
                    transaction_date=transaction_date,
                )
            except Exception as exc:
                raise RuntimeError(
                    f"An error occured while attempting to send notification for policy renewal: {str(exc)}"
                )

        except Policy.DoesNotExist:
            raise ValueError("Policy not found")
        except Exception as exc:
            raise RuntimeError(f"An error occured: {str(exc)}")

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
    def get_policy(policy_id=None, policy_number=None):
        try:
            if policy_id:
                return Policy.objects.get(policy_id=policy_id)
            elif policy_number:
                return Policy.objects.get(policy_number=policy_number)
            else:
                raise ValueError("Either policy_id or policy_number must be provided.")
        except ObjectDoesNotExist:
            raise ValueError("Policy not found.")

    @staticmethod
    @transaction.atomic
    def cancel_policy(
        policy_id: str | None = None,
        policy_number: str | None = None,
        reason: str | None = None,
        cancellation_date=None,
    ):
        """
        Initiate a cancellation request using the given policy data

        Policy cancellation can be initiated either using the policy reference number or the assigned
        policy ID.
        """
        from api.notifications.services import PolicyNotificationService
        from django.db import transaction

        policy = Policy.objects.get(policy_id=policy_id)

        if policy_id:
            policy = Policy.objects.get(policy_id=policy_id)
        elif policy_number:
            policy = Policy.objects.get(policy_number=policy_number)
        else:
            raise ValueError("Either policy_id or policy_number must be provided.")

        with transaction.atomic():
            policy.status = policy.CANCELLED
            policy.cancellation_reason = reason
            policy.cancellation_date = cancellation_date or timezone.now()

            # set the cancellation initiator to the merchant
            policy.cancellation_initiator = policy.merchant.name

            policy.save(
                update_fields=["status", "cancellation_reason", "cancellation_date"]
            )

            transaction_date = timezone.now().strftime("%Y-%m-%d %H:%M:%S")
            customer = {
                "first_name": policy.policy_holder.first_name,
                "last_name": policy.policy_holder.last_name,
                "customer_email": policy.policy_holder.email,
            }
            # send notification emails to stakeholders - in this case, our merchant  and their customer
            try:
                PolicyNotificationService.notify_merchant(
                    "cancel_policy", policy, customer, transaction_date
                )
            except Exception as mail_exc:
                raise Exception(
                    "An error occured while initiating notification to merchant"
                ) from mail_exc

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

            # quote here, is actually a serializer and not the actual data
            # from serializr, LoL.
            quote_serializer = quote_service._get_quote_by_code(quote_code)
            if not quote_serializer:
                raise ValidationError(f"Quote with code {quote_code} does not exist")

            # extract information about the product and the applicable premium from the quote
            quote_data = quote_serializer.data  # shoudl be a dict with serialized data
            product_data = quote_data.get("product")
            # print(f"Product data: {product_data}")

            price_data = quote_data.get("price", {})
            premium = price_data.get("amount")

            # we want to ensure to handle adequate type conversion for the premium amount
            # django often stores Decimal values as strings in the database
            #
            # convert the premium amount to a Decimal if it is a string
            if isinstance(premium, str):
                try:
                    premium = Decimal(premium)  # Convert to Decimal
                except ValueError:
                    raise ValidationError("Invalid premium amount format")

            # extract product information from the product data
            product_id = product_data.get("id")
            product = get_object_or_404(Product, id=product_id)

            # validate incoming data where neccessary
            customer_metadata = validated_data["customer_metadata"]
            product_metadata = validated_data["product_metadata"]
            payment_information = validated_data["payment_metadata"]
            activation_details = validated_data["activation_metadata"]

            # handle payment validation
            PolicyService._validate_payment(payment_information, price_data)

            # are we renewing the policy?
            renewal_date = (
                activation_details.get("policy_expiry_date") + timedelta(days=1)
                if activation_details.get("renew")
                else None
            )
            # next, we want to process merhant and customer information
            customer = PolicyService._create_or_retrieve_customer(customer_metadata)
            merchant = PolicyService._get_merchant(validated_data["merchant_code"])

            insurer_id = quote_data["product"]["provider"]
            insurer = get_object_or_404(InsurancePartner, id=insurer_id)

            # process policy purchase
            policy = PolicyService._create_policy(
                customer,
                product,
                premium,
                merchant,
                insurer,
                activation_details,
                renewal_date=renewal_date,
            )
            policy_created_at = policy.created_at

            transaction_date = policy_created_at.strftime("%Y-%m-%d %H:%M:%S")
            print(f"Policy created at: {transaction_date}")
            print(f"customer: {customer_metadata}")
            print("transaction date: ", transaction_date)
            # notify the merchant and customer
            try:
                PolicyNotificationService.notify_merchant(
                    "purchase_policy",
                    policy,
                    customer=customer_metadata,
                    transaction_date=transaction_date,
                )
                # PolicyNotificationService.notify_customer(
                #     "purchase_policy", policy, customer_metadata["customer_email"]
                # )
            except TypeError as exc:
                raise Exception(f"Error sending notification: \n{str(exc)}")
            except Exception as exc:
                raise Exception(
                    f"An error occured while attempting to send notification for policy purchase: \n{str(exc)}",
                )

            return policy
        except ObjectDoesNotExist as exc:
            logger.error(f"ObjectDoesNotExist: {str(exc)}")
            raise ValidationError("Required object does not exist")

        except KeyError as exc:
            logger.error(f"KeyError: {str(exc)}")
            raise ValidationError(f"Missing required data: {str(exc)}")

        except Quote.DoesNotExist as exc:
            logger.error(f"Quote does not exist: {str(exc)}")
            raise ValidationError("Quote does not exist for the provided quote code")

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

        # if product and isinstance(product, uuid):
        #     product = get_object_or_404(Product, id=product)

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
            merchant = Merchant.objects.get(short_code=merchant_code)
            logger.info(f"Merchant found: {merchant}")
        except Merchant.DoesNotExist:
            logger.error(
                f"Merchant with the provided short code {merchant_code} not found"
            )
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
    def _validate_payment(payment_information: dict, policy_price: dict):
        """
        Validates the payment information of a given policy
        """
        try:
            paid_amount = Decimal(payment_information.get("premium_amount", 0))
            policy_price_amount = Decimal(policy_price.get("amount", 0))

            # Check if payment status is sucessful
            if payment_information["payment_status"] != "completed":
                raise ValidationError("Payment status must be completed to proceed")

            # Check if the amount paid matches the policy price
            # if paid_amount != policy_price_amount:
            # raise ValidationError("Amount paid does not match the policy price")
        except ValueError as exc:
            raise ValidationError(f"Invalid amount information: {str(exc)}")


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
    FLAT_FEES = {
        # Product Type -> (Coverage Type -> Flat Fee)
        "Smart Generations Protection": {
            "Bronze": Decimal("2500.00"),
            "Silver": Decimal("3500.00"),
            "Gold": Decimal("5000.00"),
        },
        Product.ProductType.LIFE: {
            "Basic": Decimal("5000.00"),
            "Comprehensive": Decimal("10000.00"),
        },
        Product.ProductType.AUTO: {
            "Basic": Decimal("2000.00"),
            "Standard": Decimal("3500.00"),
            "Premium": Decimal("5500.00"),
            "Autobase": Decimal("30000.00"),
            "Third-Party": Decimal("15000.00"),
        },
        Product.ProductType.HEALTH: {
            "Standard": Decimal("3000.00"),
            "Premium": Decimal("5000.00"),
        },
        Product.ProductType.TRAVEL: {
            "Bronze": Decimal("2000.00"),
            "Silver": Decimal("3000.00"),
            "Gold": Decimal("1500.00"),
        },
        Product.ProductType.GADGET: {
            "Basic": Decimal("2000.00"),
            "Advanced": Decimal("3500.00"),
        },
        Product.ProductType.HOME: {
            "Bronze": Decimal("1500.00"),
            "Silver": Decimal("2500.00"),
            "Gold": Decimal("3500.00"),
            "Platinum": Decimal("5000.00"),
        },
        Product.ProductType.PERSONAL_ACCIDENT: {
            "Basic": Decimal("1250.00"),
            "Silver": Decimal("2450.00"),
        },
        Product.ProductType.STUDENT_PROTECTION: {
            "Annually": Decimal("12000.00"),
            "Monthly": Decimal("1000.00"),
        },
    }

    def _get_coverage_types_for_product_type(self, product_type):
        """
        Retrieves available coverage types for a given product type.

        Arguments:
            product_type: The type of insurance product.

        Returns:
            A list of coverage types available for the given product type.
        """
        # product_type = product_type

        if product_type not in self.FLAT_FEES:
            raise ValueError(
                f"Invalid product type. Expected one of {list(self.FLAT_FEES.keys())}."
            )

        return list(self.FLAT_FEES[product_type].keys())

    def _get_all_quotes_for_product(
        self,
        product_id=None,
        product_type=None,
        product_name=None,
        insurance_details: Dict[str, Any] = None,
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
            if product_id:
                try:
                    product = Product.objects.get(id=product_id)
                    product_type = product.product_type
                    product_name = product.name
                except Product.DoesNotExist:
                    logger.error(f"Product with ID {product_id} does not exist.")
                    raise ProductNotFoundError("Product not found.")
            elif product_type and product_name:
                products = Product.objects.filter(
                    Q(product_type=product_type) & Q(name=product_name)
                )
            elif product_type:
                products = Product.objects.filter(product_type=product_type)
            else:
                raise ValueError("Either product ID or product type must be provided.")

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

    def _create_quote(
        self,
        product_id=None,
        product_type: str | None = None,
        product_name: str | None = None,
        insurance_details: dict = {},
        **kwargs,
    ):
        """
        Creates a new insurance quote for a given product type and optional product name.

        """
        PRODUCT_TYPES = list(self.FLAT_FEES.keys())

        if product_id:
            try:
                product = Product.objects.get(id=product_id)
                product_type = product.product_type
                product_name = product.name
            except Product.DoesNotExist:
                raise ValueError(f"Product with ID '{product_id}' not found.")
        else:
            product_type = product_type or kwargs.get("product_type")
            product_name = product_name or kwargs.get("insurance_name")

            # if product_type not in PRODUCT_TYPES:
            #     raise ValueError(
            #         f"Invalid product type. Expected one of {PRODUCT_TYPES}."
            #     )
            product = Product.objects.filter(
                product_type=product_type, name__iexact=product_name
            ).first()

            if not product:
                raise ValueError(
                    f"Product with type '{product_type}' and name '{product_name}' not found."
                )

            # determine the base price for the quote based on coverage ID or the flat fees
            coverage_id = insurance_details.get("coverage_id") or kwargs.get(
                "coverage_id"
            )
            if coverage_id:
                try:
                    coverage = Coverage.objects.get(id=coverage_id)
                    base_price = coverage.coverage_limit
                except Coverage.DoesNotExist:
                    raise ValueError(f"Coverage with ID '{coverage_id}' not found.")
            else:
                # coverage_id not provided? then we need to get the coverage type
                # and determine the base price based on the flat fees

                # retrieve te coverage types for the product type
                COVERAGE_TYPES = self._get_coverage_types_for_product_type(product_type)
                coverage_type = insurance_details.get("coverage_type") or kwargs.get(
                    "coverage_type"
                )

                if coverage_type not in COVERAGE_TYPES:
                    raise ValueError(
                        f"Invalid coverage type. Expected one of {COVERAGE_TYPES}."
                    )
                try:
                    base_price = self.FLAT_FEES[product_type][coverage_type]
                except KeyError:
                    raise ValueError(
                        f"Flat fee for product type '{product_type}' and coverage type '{coverage_type}' not found."
                    )

                raise ValueError("Coverage ID must be provided.")

            # create the premium amount
            premium_amount = Decimal(kwargs.get("premium_amount", "0.0"))
            premium_description = kwargs.get("insurance_name", product_name)
            premium = Price.objects.create(
                amount=premium_amount,
                description=premium_description,
            )

            with transaction.atomic():
                quote = Quote.objects.create(
                    product=product,
                    base_price=base_price,
                    premium=premium,
                    additional_metadata=insurance_details,
                )
            return quote

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
        PRODUCT_TYPES = ["Health", "Gadget", "Travel", "Life", "Home"]

        if quote_code:
            return self._get_quote_by_code(quote_code=quote_code)
        elif product in PRODUCT_TYPES:
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
