"""
This module contains the abstract  and concrete implementation for quote providers.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Mapping, Union

from api.integrations.heirs.services import HeirsAssuranceService
from core.catalog.models import Product, Quote
from core.providers.models import Provider

logger = logging.getLogger(__name__)


class BaseQuoteProvider(ABC):
    """
    Abstract class for quote providers.
    """

    @abstractmethod
    def get_quotes(self, validated_data: Mapping | dict) -> Union[Mapping, list]:
        """
        Retrieve quotes from the provider based on incoming validated request data.
        """
        return NotImplemented


class ExternalQuoteProvider(BaseQuoteProvider):
    """
    Handles the retrieval of quotes from external providers.
    """

    def __init__(self, provider: str):
        self.provider = provider
        self.service = HeirsAssuranceService()

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
            self.service.get_product_info(product["productId"])
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

    async def get_quotes(self, validated_data: Mapping) -> Union[Mapping, list]:
        """
        Retrieve quotes from the provider based on incoming validated request data.
        """
        category = validated_data["insurance_details"]["product_type"].lower()
        params = self._extract_params(validated_data)

        try:
            response = await self._make_request(category, **params)
            parsed_quotes = self._parse_response(response)
            return await self._create_quotes(parsed_quotes)
        except Exception as e:
            logger.error(f"Error retrieving quotes from {self.provider}: {e}")
            return []

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

            await Quote.objects.aupdate_or_create(
                product=product,
                premium=premium,
                base_price=data.get("base_price", 0),
                origin="External",
                provider=provider.name,
                additional_metadata=data.get("additional_metadata", {}),
                policy_terms=data.get("policy_terms", {}),
            )
