"""
This module contains the abstract  and concrete implementation for quote providers.
"""

from abc import ABC, abstractmethod
from typing import Mapping, Optional, Union

from django.db.models import QuerySet


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

    async def _make_request(self, url: str, data: dict) -> dict:
        """
        Make a request to the external provider.
        """
        if self.provider in ("Heirs", "Leadway"):
            # establish connection  to the provider
            # using the service client integrated onto the platform
            #
            # first, fetch the sub-product ids for the product category
            # essentially, should call - HeirsAssuranceService.fetch_insurance_products()
            #
            # then fetch the product information for each sub-product id
            # should call - HeirsAssuranceService.get_product_info()
            return NotImplemented
        return NotImplemented

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
        return NotImplemented

    async def _create_quotes(self, response_data: Mapping | dict) -> Optional[QuerySet]:
        """
        Retrieve quotes from the provider based on incoming validated request data.

        Eseentially, this method creates the quote objects from the external provider's response
        and saves them to the database.
        """
        return NotImplemented
