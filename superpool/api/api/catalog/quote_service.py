import asyncio
import logging
from typing import Any, Dict, Optional

from asgiref.sync import sync_to_async
from django.db import transaction
from django.db.models import Q, QuerySet

from core.catalog.models import Price, Product, ProductTier, Quote
from core.providers.models import Provider as InsurancePartner

from .providers import QuoteProviderFactory

logger = logging.getLogger(__name__)


class QuoteService:
    PRODUCT_TYPE_MAPPING = {
        "Auto": "Motor",
        "Home": "HomeProtect",
        "Personal_Accident": "Personal Accident",
        "Gadget": "Device",
        "Travel": "Travel",
    }

    async def _fetch_and_save_provider_quotes(
        self, provider_name: str, validated_data: dict
    ):
        """
        Fetch and save quotes using the specified provider.

        Each provider's `fetch_and_save_quotes` method is responsible for fetching
        quotes and saving them to the database.
        """
        try:
            provider = QuoteProviderFactory.get_provider(provider_name)
            await provider.fetch_and_save_quotes(validated_data)
            logger.info(f"Successfully fetched and saved quotes from {provider_name}")
        except Exception as e:
            logger.error(
                f"Failed to fetch quotes from {provider_name}: {e}", exc_info=True
            )

    def _retrieve_external_quotes(self, validated_data: Dict[str, Any]) -> QuerySet:
        """
        Retrieve quotes from external providers asynchronously.

        External providers are responsible for fetching and saving quotes to the database
        This method simply triggers the quote fetching process.
        """
        provider_names = ["Heirs"]
        quotes = []
        tasks = [
            self._fetch_and_save_provider_quotes(provider_names, validated_data)
            for provider in provider_names
        ]

        async def gather_quotes():
            for provider_name in provider_names:
                provider = QuoteProviderFactory.get_provider(provider_name)
                tasks.append(provider.fetch_and_save_quotes(validated_data))
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
        # NOTE WE DON'T NEED THE BELOW! - WE ARE ALREADY SAVING THE QUOTES IN THE PROVIDER
        # ALSO WE DON'T NEED TO RETURN THE QUOTES HERE BECAUSE A SEPERATE FUNCTION WOULD BE
        # CALLED TO RETRIEVE THE QUOTES FROM THE DATABASE
        quotes = self._create_quotes_from_external_data(external_quotes_data)
        return Quote.objects.filter(pk__in=quotes)

    async def request_quote(self, validated_data: dict) -> QuerySet:
        """
        Orchestrates the quote retrieval process for both internal and external providers.

        Quotes are based on validated data from the `QuoteRequestSerializerV2`
        """

        product_type = validated_data["insurance_details"]["product_type"]
        product_name = validated_data["insurance_details"].get("product_name")
        coverage_preferences = validated_data.get("coverage_preferences", {})

        if not product_type:
            logger.error("Product type is missing in the request.")
            raise ValueError("Product type is required. It cannot be empty.")

        providers = self._get_providers_for_product_type(product_type)
        # determine if the product type requires external API calls, if it does match
        # we should make the API call to the external provider

        external_product_class = self._is_external_provider_product(product_type)
        if external_product_class:
            external_quotes = self._retrieve_external_quotes(validated_data)

        internal_quotes = self._retrieve_internal_quotes(
            product_type, coverage_preferences
        )

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
        """ The list of supported product class in Heirs API - we should be doing internal mapping """
        return product_type in self.PRODUCT_TYPE_MAPPING

    async def _fetch_products(self, query: Q) -> list[Product]:
        """
        Fetch products matching the query asynchronously.
        """
        products = await sync_to_async(list)(
            Product.objects.filter(query).prefetch_related("tiers", "tiers__coverages")
        )
        logger.info(f"Fetched products: {[product.name for product in products]}")
        return products

    def _create_quote(self, product: Product, tier: ProductTier) -> Optional[str]:
        """
        Create a single Quote object for the given product and tier.

        Returns the quote ID if creation is successful, else None.
        """
        all_tier_names = [tier.tier_name for tier in product.tiers.all()]
        with transaction.atomic():
            premium = Price.objects.create(
                amount=tier.base_premium,
                description=f"{product.name} - {tier.tier_name} Premium",
            )

            logger.info(
                f"Created pricing object: {premium} for {product} in tier: {tier.tier_name}"
            )

            quote, created = Quote.objects.update_or_create(
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
                origin="Internal",
                provider=product.provider,
            )
            if created:
                logger.info(
                    f"Created new quote: {quote.quote_code} for {product.name} - {tier.tier_name}"
                )
            else:
                logger.info(
                    f"Updated existing quote: {quote.quote_code} for {product.name} - {tier.tier_name}"
                )
            return quote.quote_code

    async def _create_quote_for_internal_product(self, product: Product) -> list[str]:
        """
        Create Quote objects for each tier of a given product
        """
        quote_ids: list[str] = []
        for tier in product.tiers.all():
            logger.info(f"Processing product: {product.name}, Tier: {tier.tier_name}")

            quote_id = await sync_to_async(self._create_quote)(product, tier)

            if quote_id:
                quote_ids.append(quote_id)
        return quote_ids

    async def _retrieve_internal_quotes(
        self,
        product_type: str,
        product_name: Optional[str],
        providers_list: list[str],
        validated_data: dict[str, Any],
    ) -> list[str]:
        """
        Fetches quotes from traditional internal insurance providers based on stored data
        """
        if not providers_list:
            logger.info(f"No internal providers found for product type: {product_type}")
            return []

        query = Q(product_type=product_type, provider__name__in=providers_list)

        # if product name is present in the incoming request, include search by name
        if product_name:
            query &= Q(name__icontains=product_name)

        products = Product.objects.filter(query).prefetch_related(
            "tiers", "tiers__coverages"
        )
        logger.info(f"Found products: {products}")
        if not products:
            logger.info("No products found for the given criteria.")
            return []

        quote_ids: list[str] = []

        # When a quote is being generated based on the product coverage,
        # and provider, we are doing something interesting here,
        # we would create a Quote object for each provider and tier.
        #
        # Such that when we pulling the pricing and currency values, we won't
        # be hard-coding it, we wuld be pulling it from the Quote model
        for product in products:
            quote_ids.extend(await self._create_quote_for_internal_product(product))

        logger.info(f"Retrieved {len(quote_ids)} internal quotes")
        return quote_ids

    async def _retrieve_quotes_from_db(
        self, validated_data: dict[str, Any], origin: Optional[str] = None
    ) -> QuerySet:
        """
        Retrieve quotes from the database based on the validated data
        """
        product_type = validated_data["insurance_details"]["product_type"]
        product_name = validated_data["insurance_details"].get("product_name")

        query = Q(product__product_type=product_type)
        if product_name:
            query &= Q(product__name__icontains=product_name)

        # # if coverage preferences are provided, filter quotes accordingly
        if coverages_preferences := validated_data.get("coverage_preferences"):
            # TODO: filter quotes based on the coverage preferences
            pass

        # we never know
        if origin:
            query &= Q(origin=origin)

        # fetch all quotes for the products matching the product information
        quotes = await sync_to_async(lambda: Quote.objects.filter(query).distinct())()
        logger.info(
            f"Retrieved {quotes.count()} {'external' if origin == 'External' else 'internal'} quotes from DB"
        )
        return quotes
