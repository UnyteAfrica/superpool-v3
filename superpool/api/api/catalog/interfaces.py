"""
This module contains the abstract  and concrete implementation for quote providers.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Mapping, Union

from api.integrations.heirs.services import HeirsAssuranceService
from core.catalog.models import Quote
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

    async def _make_request(self, category: str, **params: dict) -> Mapping | dict:
        """
        Make a request to the external provider.
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

    def _parse_response(self, response: dict) -> Union[Mapping, list]:
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
        if response is not None:
            for quote_data in response.get("quotes", []):
                quotes.append(
                    {
                        "product_id": quote_data["product_id"],
                        "product_info": quote_data["product_info"],
                        "origin": self.provider,
                        "premium": quote_data["premium"],
                        "contribution": quote_data["contribution"],
                    }
                )
        return quotes

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

        for data in response_data:
            quote = Quote.objects.aupdate_or_create(
                product_id=data["product_id"],
                premium=data["premium"],
                contribution=data["contribution"],
                origin=data["origin"],
            )
