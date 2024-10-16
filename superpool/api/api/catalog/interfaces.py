"""
This module contains the abstract  and concrete implementation for quote providers.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any, Mapping, Optional, Union

from asgiref.sync import sync_to_async
from django.db import transaction
from typing_extensions import deprecated

from api.catalog.serializers import ProductDetailsSerializer
from api.integrations.heirs.services import HeirsAssuranceService
from core.catalog.models import Price, Product, Quote
from core.providers.integrations.heirs.registry import Quote as QuoteType
from core.providers.models import Provider

logger = logging.getLogger(__name__)


class BaseQuoteProvider(ABC):
    """
    Abstract class for quote providers.
    """

    @abstractmethod
    async def fetch_and_save_quotes(self, validated_data: dict[str, Any]) -> None:
        """
        Retrieve quotes from the provider based on incoming validated request data and save them to the database.
        """
        pass


@dataclass
class QuoteData:
    """
    Defines the structure for a quote data object from Heirs
    """

    product_id: str
    product_name: str
    product_info: str
    premium: Decimal
    origin: str
    contribution: Optional[Decimal] = Decimal(0)


@deprecated("This class is deprecated. Use HeirsQuoteProvider instead")
class ExternalQuoteProvider(BaseQuoteProvider):
    """
    Handles the retrieval of quotes from external providers.
    """

    def __init__(self, provider: str):
        self.provider = provider
        self.service = HeirsAssuranceService()

    async def process_request(self, validated_data: dict) -> Union[Mapping, list]:
        """
        Handle the request and return quotes.
        """
        product_type = validated_data["insurance_details"].get("product_type")
        category = validated_data["insurance_details"]["product_type"].lower()

        product_details_serializer = ProductDetailsSerializer(data=validated_data)
        product_details_serializer.is_valid(raise_exception=True)

        matching_serializer_class = product_details_serializer.get_matching_serializer(
            product_type
        )
        if not matching_serializer_class:
            raise ValueError("No matching serializer found for the product type.")

        additional_info_serializer = matching_serializer_class(
            data=validated_data.get("additional_information")
        )
        additional_info_serializer.is_valid(raise_exception=True)

        request_params = {
            **additional_info_serializer.validated_data,
        }

        params = self._extract_params(validated_data)

        try:
            response = await self._make_request(category, **params)
            parsed_quotes = self._parse_response(response)
            await self._create_quotes(parsed_quotes)
            return parsed_quotes
        except Exception as e:
            logger.error(f"Error retrieving quotes from {self.provider}: {e}")
            return []

    async def _make_request(self, category: str, **params: dict) -> list[tuple]:
        """
        Make a request to the external provider to fetch products
        """
        # if self.provider in ("Heirs", "Leadway"):
        # establish connection  to the provider
        # using the service client integrated onto the platform
        #
        # first, fetch the sub-product ids for the product category
        # essentially, should call - HeirsAssuranceService.fetch_insurance_products()
        #
        # then fetch the product information for each sub-product id
        # should call - HeirsAssuranceService.get_product_info()
        sub_products = await self.service.fetch_insurance_products(category)

        product_info_tasks = [
            self.service.fetch_product_info(product["productId"])
            for product in sub_products
        ]
        product_info_responses = await asyncio.gather(*product_info_tasks)
        # now we return the product along with its corresponding product info
        return list(zip(sub_products, product_info_responses))

    def _parse_response(self, response: list[tuple]) -> list[dict]:
        """
        Parse the response from the external provider.
        """
        # responsee from quotes contain only the premium to be paid for that product id
        #  and a 'contribution' field which is the amount the policy holder is expected to pay
        #  for the policy

        # Instead we want to create a consistent response format for all providers
        # where we would include the product id, the product info,
        # the origin (the provider name), the premium and the contribution
        quotes = []
        for product, product_info in response:
            # For now, we would just go with the Hiers flow
            # this should change when integrating other platform
            quotes.append(
                {
                    "product_id": product["productId"],
                    "product_name": product_info["productName"],
                    "product_info": product_info["info"],
                    "premium": product_info["premium"],
                    "contribution": product_info["contribution"],
                    "origin": self.provider,
                }
            )
        return quotes

    def _extract_params(self, validated_data: dict) -> dict:
        """
        Extract parameters from the validated request data.
        """
        params = {}
        product_type = validated_data["insurance_details"]["product_type"]

        # VALID PARAMETTERS BASED ON PRODUCT TYPES
        if product_type == "motor":
            params = {
                "motor_value": validated_data.get("motor_value"),
                "motor_class": validated_data.get("motor_class"),
                "motor_type": validated_data.get("motor_type"),
            }
        elif product_type == "travel":
            params = {
                "user_age": validated_data.get("user_age"),
                "start_date": validated_data.get("start_date"),
                "end_date": validated_data.get("end_date"),
            }
        elif product_type == "biker":
            params = {
                "motor_value": validated_data.get("motor_value"),
                "motor_class": validated_data.get("motor_class"),
            }

        return params

    async def _create_quotes(self, response_data: list) -> None:
        """
        Retrieve quotes from the provider based on incoming validated request data.

        Eseentially, this method creates the quote objects from the external provider's response
        and saves them to the database.
        """
        provider_name = self.provider.lower()
        provider = Provider.objects.filter(name__icontains=provider_name).first()

        if not provider:
            logger.error(f"Could not find provider with name: {provider_name}")
            raise ValueError(f"Provider with name {provider_name} not found")

        for data in response_data:
            # create corresponding product object for that insurer
            product, _ = await Product.objects.aupdate_or_create(
                provider=provider,
                name=data["product_name"],
                defaults={
                    "description": data["description"],
                    "product_type": "Auto",  # NOTE: WE NEED TO DYNAMICALLY SET THIS
                    "is_live": True,
                },
            )

            # create corresponding price (premium) object
            premium = Price.objects.create(
                amount=data["premium"],
                currency="NGN",
            )

            await Quote.objects.aupdate_or_create(
                product=product,
                premium=premium,
                base_price=data.get("base_price", 0),
                origin="External",
                provider=provider.name,
                additional_metadata=data.get("additional_metadata", {}),
                policy_terms=data.get("policy_terms", {}),
            )


class HeirsQuoteProvider(BaseQuoteProvider):
    def __init__(self):
        self.client = HeirsAssuranceService()

    async def fetch_and_save_quotes(self, validated_data: dict[str, Any]) -> None:
        """
        Fetch quotes from Heirs Assurance.
        """
        product_type = validated_data["insurance_details"]["product_type"]
        category = self._map_product_type_to_category(product_type)
        params = self._extract_params(validated_data)

        # Fetch product details and insurance info
        sub_products = self.client.fetch_insurance_products(category)

        tasks = []
        for product in sub_products:
            product_id = product["productId"]
            tasks.append(
                self._fetch_product_info_and_save_quote(product_id, category, params)
            )
        await asyncio.gather(*tasks)

    async def _fetch_product_info_and_save_quote(
        self, product_id: int, product_class: str, params: dict[str, Any]
    ) -> Union[dict[str, Any], None]:
        """
        Fetch product info and quote for a specific product
        """
        quotes = self.client.get_quotes(product_class, params)
        print(f"Quote Data: {quotes}")

        if isinstance(quotes, dict) and "error" in quotes:
            logger.warning(f"Error fetching quotes for product id: {product_id}")
            logger.error(f'Error fetching quotes: {quotes["error"]["detail"]}')
            return None

        assert isinstance(quotes, list), ValueError("Invalid response from Heirs API")
        updated_quotes: list[QuoteType] = [
            {**quote, "origin": "Heirs"} for quote in quotes
        ]
        await sync_to_async(self._save_quote)(updated_quotes, product_class)

    @transaction.atomic
    def _save_quote(self, quote_data: list[QuoteType], product_class: str) -> None:
        """
        Save the product, price, quote to the database
        """
        provider_name_alias = "Heirs Insurance Group"
        provider, created = Provider.objects.get_or_create(name=provider_name_alias)

        if created:
            logger.info(f"Created provider: {provider_name_alias}")
        else:
            logger.info(f"Using existing provider: {provider_name_alias}")

        product_type = self._map_category_to_product_type(product_class)
        logger.info(f"Product Type: {product_type}")

        for quote in quote_data:
            # Update or create Product
            product, product_created = Product.objects.update_or_create(
                name=quote["product_name"],
                provider=provider,
                defaults={
                    "description": quote.get("product_info", ""),
                    "product_type": product_type,
                    "is_live": True,
                },
            )
            if product_created:
                logger.info(f"Created product: {product.name}")
            else:
                logger.info(f"Updated existing product: {product.name}")

            # unique description for identiying the Price which belongs to a product
            description = f"{quote['product_name']} - Premium"
            price, price_created = Price.objects.update_or_create(
                amount=quote["premium"],
                description=description,
                currency="NGN",
                defaults={},
            )
            if price_created:
                logger.info(f"Created price: {price.amount} NGN")
            else:
                logger.info(f"Updated existing price: {price.amount} NGN")

            # Update or create quote record for the product
            quote_obj, quote_created = Quote.objects.update_or_create(
                product=product,
                origin="External",
                provider=provider.name,
                defaults={
                    "premium": price,
                    "base_price": quote["premium"],
                    "additional_metadata": {
                        "contribution": quote.get("contribution", 0),
                        "policy_terms": quote.get("policy_terms", {}),
                    },
                },
            )
            if quote_created:
                logger.info(
                    f"Created new quote: {quote_obj.quote_code} for product: {product.name}"
                )
            else:
                logger.info(
                    f"Updated existing quote: {quote_obj.quote_code} for product: {product.name}"
                )

    def _map_product_type_to_category(self, product_type: str) -> str:
        mapping = {
            "Auto": "Motor",
            "Home": "HomeProtect",
            "Personal_Accident": "Personal Accident",
            "Gadget": "Device",
            "Travel": "Travel",
            "Cargo": "Marine Cargo",
        }
        # return the original product type if no mapping is found
        return mapping.get(product_type, product_type)

    def _map_category_to_product_type(self, category: str) -> str:
        reverse_mapping = {
            "Motor": "Auto",
            "HomeProtect": "Home",
            "Personal Accident": "Personal_Accident",
            "Device": "Gadget",
            "Travel": "Travel",
            "Marine Cargo": "Cargo",
        }
        # return the category if no mapping is found
        return reverse_mapping.get(category, category)

    def _process_vehicle_params(self, validated_data: dict) -> dict:
        """
        Extract vehicle parameters from validated request data.
        """

        # extract and convert decimal to its str value
        additional_info = validated_data["insurance_details"].get(
            "additional_information"
        )
        vehicle_type = additional_info.get("vehicle_type")
        vehicle_value = str(additional_info.get("vehicle_value"))

        car_vehicle_params = {
            "motor_value": vehicle_value,
            "motor_class": additional_info.get("vehicle_usage"),
            "motor_type": additional_info.get("vehicle_category"),
        }
        bike_vehicle_params = {
            "motor_value": vehicle_value,
            "motor_class": additional_info.get("vehicle_usage"),
        }
        vehicle_params = {}

        if vehicle_type == "Car":
            vehicle_params = {**car_vehicle_params, "vehicle_type": vehicle_type}
        elif vehicle_type == "Bike":
            vehicle_params = {**bike_vehicle_params, "vehicle_type": vehicle_type}
        else:
            raise ValueError(f"Invalid vehicle type: {vehicle_type}")

        logger.info(f"Extracted Vehicle Params: {vehicle_params}")
        return vehicle_params

    def _extract_params(self, validated_data: dict) -> dict:
        """
        Extract required parameters from validated request data.
        """
        additional_info = validated_data["insurance_details"].get(
            "additional_information"
        )
        customer_info = validated_data.get("customer_metadata", {})
        category_name = additional_info.get("insurance_options")

        product_type = validated_data["insurance_details"]["product_type"]

        date_of_birth = customer_info.get("date_of_birth")
        if date_of_birth:
            today = datetime.today().date()
            user_age = (
                today.year
                - date_of_birth.year
                - ((today.month, today.day) < (date_of_birth.month, date_of_birth.day))
            )
        else:
            user_age = None

        # process params based on product type
        #
        # vehicle params are only required for Auto insurance
        if product_type == "Auto":
            _vehicle_params = self._process_vehicle_params(validated_data)
            logger.info(f'Finished processing vehicle params for "{product_type}"')
            return {
                **_vehicle_params,
                "category_name": category_name,
                "product_id": additional_info.get("product_id"),
                **customer_info,
                "product_type": product_type,
            }
        extracted = {
            **additional_info,
            "user_age": user_age,
            "category_name": category_name,
        }
        logger.info(f"Computed user age: {user_age}")
        logger.info(f"Extraacted Additional Info: {extracted}")
        return extracted


# @warnings.warn("This class has not been implemented yet")
class LeadwayQuoteProvider(BaseQuoteProvider):
    """
    TO BE USED WHEN WE WANT TO INTEGRATE LEADWAY INSURANCE
    """

    pass


# @warnings.warn("This class has not been implemented yet")
class AXAQuoteProvider(BaseQuoteProvider):
    """
    TO BE USED WHEN WE WANT TO INTEGRATE AXA INSURANCE
    """

    pass
