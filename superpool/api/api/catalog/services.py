import asyncio
import logging
import traceback
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, Union

from django.core.exceptions import ObjectDoesNotExist
from django.db import DatabaseError, models, transaction
from django.db.models import Q, QuerySet
from django.utils import timezone
from rest_framework.generics import get_object_or_404
from rest_framework.serializers import ValidationError

from api.catalog.exceptions import ProductNotFoundError, QuoteNotFoundError
from api.catalog.interfaces import QuoteProviderFactory
from api.catalog.serializers import QuoteSerializer
from core.catalog.models import Policy, Price, Product, ProductTier, Quote
from core.merchants.models import Merchant
from core.models import Coverage
from core.providers.models import Provider as InsurancePartner
from core.user.models import Customer

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
    def get_product_by_id(product_id: Any) -> Product:
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
            else:
                raise ValidationError(
                    "Either policy id or the policy number must be provided."
                )

            # check if the policy is already active and within its valid effective period
            # today = timezone.now().date()
            # if policy.effective_from <= today <= policy.effective_through:
            #     raise ValidationError(
            #         "Policy is currently active and within its valid effective period. Renewal is not needed."
            #     )

            # check that the preferred policy start date is after the current policy's effective end date
            if policy_start_date:
                if (
                    policy.effective_through
                    and policy_start_date <= policy.effective_through
                ):
                    raise ValidationError(
                        "Preferred start date must be after the current policy's effective end date."
                    )
                if policy.effective_from and policy_start_date <= policy.effective_from:
                    raise ValidationError(
                        "Preferred start date must be after the current policy's effective start date."
                    )

            # set the new policy status and dates
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
        from django.db import transaction

        from api.notifications.services import PolicyNotificationService

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
            with transaction.atomic():
                # retrieve quote information and process it
                quote_code = validated_data["quote_code"]

                # quote here, is actually a serializer and not the actual data
                # from serializr, LoL.
                quote_serializer = quote_service._get_quote_by_code(quote_code)
                if not quote_serializer:
                    raise ValidationError(
                        f"Quote with code {quote_code} does not exist"
                    )

                # extract information about the product and the applicable premium from the quote
                quote_data = (
                    quote_serializer.data
                )  # shoudl be a dict with serialized data
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

                # import pdb
                #
                # pdb.set_trace()

                # extract information about the insurer using the provider id
                # otherwise, fallback to a fail-safe of using the insurer name
                # in the output of the serializer

                provider_info = product_data.get("provider", {})
                insurer_id = provider_info.get("provider_id")
                insurer_name = provider_info.get("provider_name")

                try:
                    if insurer_id:
                        insurer = get_object_or_404(InsurancePartner, id=insurer_id)
                    else:
                        # we want to use case-insensitive exact match
                        insurer = InsurancePartner.objects.get(
                            Q(provider_name__iexact=insurer_name)
                        )
                except InsurancePartner.DoesNotExist:
                    raise ValidationError(
                        f"Insurer with name '{insurer_name}' does not exist"
                    )

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
                customer_context = {
                    "first_name": customer_metadata.get("first_name", ""),
                    "last_name": customer_metadata.get("last_name", ""),
                    "customer_email": customer_metadata.get("customer_email"),
                }
                try:
                    PolicyNotificationService.notify_merchant(
                        "purchase_policy",
                        policy,
                        customer=customer_context,
                        transaction_date=transaction_date,
                    )
                except TypeError as exc:
                    raise Exception(f"Error sending notification: \n{str(exc)}")
                except Exception as exc:
                    raise Exception(
                        f"An error occured while attempting to send notification for policy purchase: \n{str(exc)}",
                    )

                return policy
        except (
            ObjectDoesNotExist,
            KeyError,
            ValidationError,
            Quote.DoesNotExist,
        ) as exc:
            logger.error(f"Exception occurred: {str(exc)}")
            raise ValidationError(f"Error: {str(exc)}")
        except DatabaseError as exc:
            logger.error(
                f"DatabaseError occurred: {str(exc)}\n{traceback.format_exc()}"
            )
            raise Exception(f"DatabaseError: {str(exc)}")
        except Exception as exc:
            logger.error(
                f"Unexpected error occurred: {str(exc)}\n{traceback.format_exc()}"
            )
            raise Exception(f"An unexpected error occurred: {str(exc)}")

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
    """
    A service that handles the logic of retrieving and aggregating insurance quotes
    from various providers (integrated providers and internal providers)
    """

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
        Creates a new insurance quote based on the specified product and coverage details.

        This endpoint allows you to generate an insurance quote by specifying either a product ID,
        product type, and optional product name. The quote is determined by either providing a coverage ID
        or coverage type. If a coverage type is provided, the base price is retrieved from predefined flat fees.

        Arguments:
            product_id (str, optional): The unique identifier of the product. If provided, overrides
                other product type and name parameters.
            product_type (str, optional): The type of insurance product (e.g., LIFE, AUTO, HEALTH).
                If `product_id` is not provided, this parameter is required.
            product_name (str, optional): The name of the insurance product. If `product_id` is not provided,
                this parameter is used along with `product_type` to identify the product.
            insurance_details (dict): A dictionary containing details related to the insurance quote.
                This can include 'coverage_id' and 'coverage_type'.
            **kwargs: Additional keyword arguments. Can include 'coverage_id', 'coverage_type', and 'premium_amount'.

        Returns:
            Quote: An instance of the `Quote` model representing the created insurance quote.

        Raises:
            ValueError: If the provided `product_id` does not exist, if no product is found with the given
                `product_type` and `product_name`, if neither `coverage_id` nor `coverage_type` is provided,
                or if an invalid coverage type is specified.

        Examples:
            - To create a quote using a product ID:
              ```
              _create_quote(product_id="12345")
              ```

            - To create a quote using product type and name:
              ```
              _create_quote(product_type="AUTO", product_name="Basic Car Insurance", insurance_details={"coverage_type": "Standard"})
              ```

            - To create a quote using coverage ID:
              ```
              _create_quote(product_type="HEALTH", insurance_details={"coverage_id": "7890"})
              ```

        Notes:
            - The `coverage_id` and `coverage_type` cannot both be provided. Only one should be used to determine the base price.
            - The `premium_amount` can be specified to adjust the premium details of the quote.
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
            coverage_type = insurance_details.get("coverage_type") or kwargs.get(
                "coverage_type"
            )

            if coverage_id:
                try:
                    coverage = Coverage.objects.get(pk=coverage_id)
                    base_price = coverage.coverage_limit
                except Coverage.DoesNotExist:
                    raise ValueError(f"Coverage with ID '{coverage_id}' not found.")

            elif coverage_type:
                # coverage_id not provided? then we need to get the coverage type
                # and determine the base price based on the flat fees

                # retrieve te coverage types for the product type
                COVERAGE_TYPES = self._get_coverage_types_for_product_type(product_type)

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
            else:
                raise ValueError(
                    "Either coverage_id or coverage_type must be provided."
                )

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

    def _calculate_premium(self, tier, **kwargs):
        """
        Calculate the base price and premium for the quote based on the tier and coverage amount.
        """
        base_price = tier.base_preimum
        risk_adjustments = kwargs.get("risk_adjustments", [])

        # perform risk adjustments to the base price (if any)

        # for coverage in tier.coverages.all():
        #     coverage_limit = coverage.coverage_limit
        #     if coverage_limit:
        #         total_premium = base_price

        total_premium = base_price

        premium = Price.objects.create(
            amount=total_premium,
            description=f"Premium for {tier.tier_name}",
        )

        return base_price, premium

    @transaction.atomic
    def create_quote(
        self,
        product_id=None,
        product_type=None,
        product_name=None,
        insurance_details=None,
        coverage_type=None,
        coverage_amount=None,
        **kwargs,
    ):
        """
        Create a new insurance quote based on product and coverage information.

        Arguments:
            - product_id: The unique identifier of the product.
            - product_type: The type of insurance product (e.g., 'Auto', 'Health').
            - product_name: Optional name of the insurance product.
            - insurance_details: A dictionary of additional details (coverage, etc.).
            - coverage_type: Type of coverage requested (e.g., 'Comprehensive', 'Basic').
            - coverage_amount: Desired coverage amount.
        """
        if product_id:
            product = get_object_or_404(Product, id=id)
        elif product_type and product_name:
            product = Product.objects.get(
                product_type=product_type, product_name=product_name
            )
        else:
            raise ValueError(
                "Either product_id or (product_type and product_name) must be provided."
            )

        tier = self._get_tier_by_coverage_type(product, coverage_type)
        base_price, premium = self._calculate_premium(tier, **kwargs)

        quote = Quote.objects.create(
            base_price=base_price,
            premium=premium,
            product=product,
            additional_metadata=insurance_details,
        )
        return quote

    def _retrieve_external_quotes(self, validated_data: Dict[str, Any]) -> QuerySet:
        """
        Retrieve quotes from external providers asynchronously.
        """
        provider_names = ["Heirs"]
        quotes = []

        async def gather_quotes():
            tasks = []
            for provider_name in provider_names:
                provider = QuoteProviderFactory.get_provider(provider_name)
                tasks.append(provider.get_quotes(validated_data))
            results = await asyncio.gather(*tasks)
            return results

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            provider_quotes = loop.run_until_complete(gather_quotes())
        finally:
            loop.close()

        # Flatten the list of lists
        external_quotes_data = [
            quote for sublist in provider_quotes for quote in sublist
        ]

        # Process and store the quotes
        quotes = self._create_quotes_from_external_data(external_quotes_data)
        return Quote.objects.filter(pk__in=quotes)

    def request_quote(self, validated_data: dict) -> QuerySet:
        """
        Retrieve quotes based on validated data from the `QuoteRequestSerializerV2`

        This function follows a four-step process:

        1. Request Comes In:
           - Extract product details from the incoming request using the validated data.
           - The key product information includes the `product_type`, along with coverage preferences.

        2. Asynchronous External Provider Requests:
           - Based on the product type, we check if it matches specific product categories (e.g., Auto, Home, Personal Accident, Travel).
           - For valid product types, we initiate concurrent external API requests to our insurance providers using the `ProviderNameService`.
           - This involves:
               a. Fetching all insurance products under a specific product type.
               b. For each product, fetching the product description based on `productId`.
               c. Fetching the premium and contribution details for the selected product.

        3. Internal Quotes:
           - Simultaneously, we retrieve internal quotes from our database using the product information.
           - Providers are fetched based on the `product_type`, and quotes are generated for each matching product.

        4. Aggregation & Filtering:
           - Once the external provider data is gathered, it is aggregated into a unified schema.
           - We use the retrieved data to filter quotes from the internal `Quote` model.
           - Finally, we return the list of quotes that match the coverage and product preferences back to the merchant.

        """

        product_type = validated_data["insurance_details"]["product_type"]
        product_name = validated_data["insurance_details"].get("product_name")
        coverage_preferences = validated_data.get("coverage_preferences", {})

        providers = self._get_providers_for_product_type(product_type)

        # NOTE: WE SHOULD MAKE AN API CALL TO THE EXTERNAL PROVIDERS
        #
        # however, we should only make external API calls for specific product types
        #
        # (Device, Motor, Home, Travel, Personal Accident)

        external_quotes = []
        external_product_class = self._is_external_provider_product(product_type)
        if external_product_class:
            external_quotes = self._retrieve_external_quotes(validated_data)
        # external_quotes_task = (
        #     self._retrieve_external_quotes(validated_data)
        #     if external_product_class
        #     else None
        # )

        internal_quotes = self._retrieve_quotes_from_internal_providers(
            product_type, coverage_preferences
        )

        # # Gather external quotes
        # tasks = [internal_quotes_task]
        #
        # if external_quotes_task:
        #     tasks.append(external_quotes_task)
        #
        # results = asyncio.run(asyncio.gather(*tasks))

        # internal_quotes = results[0]
        # logger.info(f"Internal quotes: {internal_quotes}")
        # external_quotes = results[1] if external_quotes_task else []
        # logger.info(f"External quotes: {external_quotes}")

        all_quotes = internal_quotes.union(external_quotes)
        return all_quotes

    def _get_tier_by_coverage_type(self, product, coverage_type):
        """
        Retrieve the appropriate product tier based on coverage type and product.
        """
        try:
            tier = ProductTier.objects.filter(
                product=product, coverages__coverage_type=coverage_type
            ).first()
            if not tier:
                raise ValueError(
                    f"Tier with coverage type '{coverage_type}' not found for product '{product.name}'."
                )
            return tier
        except ProductTier.DoesNotExist:
            raise ValueError(
                f"Tier with coverage type '{coverage_type}' not found for product '{product.name}'."
            )

    def _get_providers_for_product_type(self, product_type: str) -> QuerySet:
        """
        Fetch all insurance providers with the who offers some product
        for this product type
        """
        return InsurancePartner.objects.filter(
            product__product_type=product_type
        ).distinct()

    def _is_external_provider_product(self, product_type: str) -> bool:
        """
        Map internal product type to external product class for API calls
        Determine if the product type requires external API calls

        This approach is because of Heirs right now
        """
        VALID_EXTERNAL_PRODUCT_TYPES = {
            "Motor",
            "TenantProtect",
            "HomeProtect",
            "BusinessProtect",
            "Personal Accident",
            "Marine Cargo",
            "Device",
            "Travel",
        }
        mapping = {
            "Auto": "Motor",
            "Home": "HomeProtect",
            "Personal_Accident": "Personal Accident",
            "Gadget": "Device",
            "Travel": "Travel",
        }
        return product_type in VALID_EXTERNAL_PRODUCT_TYPES

    def _create_quotes_from_external_data(
        self, external_quotes_data: list[Dict[str, Any]]
    ):
        """
        Create Quote instances from pulled external provider data.
        """
        quotes = []
        for data in external_quotes_data:
            provider_name = data["origin"]
            provider, _ = Provider.objects.get_or_create(name=provider_name)

            product, _ = Product.objects.get_or_create(
                provider=provider,
                name=data["product_name"],
                defaults={
                    "description": data["product_info"],
                    "product_type": data["product_type"],
                    "is_live": True,
                },
            )

            # Create or get Price instance
            premium, _ = Price.objects.get_or_create(
                amount=data["premium"],
                currency="NGN",
            )

            quote, created = Quote.objects.update_or_create(
                quote_code=data["product_id"],
                defaults={
                    "product": product,
                    "premium": premium,
                    "base_price": data.get("base_price", data["premium"]),
                    "origin": "External",
                    "provider": provider.name,
                    "additional_metadata": {
                        "contribution": data.get("contribution"),
                        "policy_terms": data.get("policy_terms", {}),
                    },
                },
            )
            quotes.append(quote.pk)
        return quotes

    def _retrieve_quotes_from_internal_providers(
        self, providers: QuerySet, validated_data: dict
    ) -> QuerySet:
        """
        Fetches quotes from traditional internal insurance providers based on stored data

        Arguments:
            providers (QuerySet): List of insurance providers that offer the requested product.
            validated_data (dict): Validated data from the incoming request.

        Returns:
            List of internal quotes
        """
        # IN FUTURE WE ARE GOING TO BE DOING SOME DYNAMIC CALCULATION IN HERE
        #
        # FOR NOW WE ARE JUST GOING TO RETURN THE BASE PREMIUMS BACK TO THE MERCHANT
        # AS THE AMOUNT TO BE PAID
        quotes = []
        providers_list = [provider.name for provider in providers]

        product_type = validated_data["insurance_details"]["product_type"]
        product_name = validated_data["insurance_details"].get("product_name")

        # Prefetch related product tiers and coverages in a single query
        #
        # fetch all products matching the product information (name, type, tier or something)
        products = (
            Product.objects.filter(
                provider__name__in=providers_list,
                product_type=product_type,
            )
            # .select_related("provider")
            .prefetch_related("tiers", "tiers__coverages")
        )

        logger.info(f"Found products: {products}")

        # if product name is present in the incoming request, include search by name
        if product_name:
            products = products.filter(name__icontains=product_name)
            logger.info(f"Filtered products: {products}")

        # When a quote is being generated based on the product coverage,
        # and provider, we are doing something interesting here,
        # we would create a Quote object for each provider and tier.
        #
        # Such that when we pulling the pricing and currency values, we won't
        # be hard-coding it, we wuld be pulling it from the Quote model
        try:
            for product in products:
                # fetch all the tier nnmes for this product
                all_tier_names = [tier.tier_name for tier in product.tiers.all()]
                for tier in product.tiers.all():
                    logger.info(
                        f"Processing product: {product.name}, Tier: {tier.tier_name}"
                    )
                    print(f"Product: {product.name}")
                    print(f"Tier: {tier.tier_name}")

                    with transaction.atomic():
                        premium = Price.objects.create(
                            amount=tier.base_premium,
                            description=f"{product.name} - {tier.tier_name} Premium",
                        )

                        logger.info(
                            f"Created pricing object: {premium} for {product} in tier: {tier.tier_name}"
                        )

                        # pdb.set_trace()

                        quote = Quote.objects.create(
                            product=product,
                            premium=premium,
                            base_price=tier.base_premium,
                            additional_metadata={
                                "tier_name": tier.tier_name,
                                "coverage_details": [
                                    {
                                        "coverage_name": coverage.coverage_name,
                                        "coverage_description": coverage.description,
                                        "coverage_type": coverage.coverage_name,
                                        "coverage_limit": str(coverage.coverage_limit),
                                    }
                                    for coverage in tier.coverages.all()
                                ],
                                "exclusions": tier.exclusions or "",
                                "benefits": tier.benefits or "",
                                "product_type": product.product_type,
                                "available_tiers": all_tier_names,  # All addons available for this product
                            },
                        )
                        logger.info(
                            f"Created quote: {quote.quote_code} for {product.name} - {tier.tier_name}"
                        )
                        quotes.append(quote.pk)
            return Quote.objects.filter(pk__in=quotes)
        except Exception as exc:
            logger.error(f"Error while processing product tiers: {exc}")
            raise exc
