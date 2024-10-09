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

    async def _retrieve_external_quotes(
        self, validated_data: Dict[str, Any]
    ) -> QuerySet:
        """
        Retrieve quotes from external providers asynchronously.

        External providers are responsible for fetching and saving quotes to the database
        This method simply triggers the quote fetching process.
        """
        provider_names = ["Heirs"]
        tasks = [
            self._fetch_and_save_provider_quotes(provider, validated_data)
            for provider in provider_names
        ]
        await asyncio.gather(*tasks)

        # after fetching, we should retrive the quotes from the database
        external_quotes_data = await self._retrieve_quotes_from_db(
            validated_data, origin="External"
        )
        return external_quotes_data

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
        external_product_class = self._map_product_type_to_external_class(product_type)
        tasks = []

        if external_product_class:
            tasks.append(self._retrieve_external_quotes(validated_data))
        else:
            external_quotes = Quote.objects.none()

        tasks.append(self._retrieve_internal_quotes(validated_data))

        try:
            if external_product_class:
                # Run both tasks concurrently
                external_quotes, internal_quotes = await asyncio.gather(*tasks)
            else:
                # Only run internal_quotes task
                (internal_quotes,) = await asyncio.gather(*tasks)

            if external_product_class:
                # Combine the external and internal QuerySets
                all_quotes = external_quotes | internal_quotes
            else:
                all_quotes = internal_quotes

        except Exception as e:
            logger.error(f"Failed to retrieve quotes: {e}", exc_info=True)
            raise

        # results = await asyncio.gather(*tasks, return_exceptions=True)
        # external_quotes = results[0] if external_product_class else Quote.objects.none()
        # internal_quotes = results[1]
        # print(f"External quotes: {external_quotes}")
        # print(f"Internal quotes: {internal_quotes}")
        return all_quotes

    def _get_providers_for_product_type(self, product_type: str) -> QuerySet:
        """
        Fetch all insurance providers with the who offers some product
        for this product type
        """
        providers = InsurancePartner.objects.filter(
            product__product_type=product_type
        ).distinct()
        logger.info(f'Found providers for product type "{product_type}": {providers}')
        return providers

    def _map_product_type_to_external_class(self, product_type: str) -> Optional[str]:
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
        mapping = self.PRODUCT_TYPE_MAPPING.get(product_type)
        logger.info(f"External product class for {product_type}: {mapping}")
        return mapping if mapping in VALID_EXTERNAL_PRODUCT_TYPES else None

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
            premium, _ = Price.objects.get_or_create(
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
                provider=product.provider.name,
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

        Returns a list of quote IDs (or quote_codes).
        """
        quote_ids = []
        for tier in product.tiers.all():
            logger.info(f"Processing product: {product.name}, Tier: {tier.tier_name}")
            quote_id = await sync_to_async(self._create_quote)(product, tier)
            if quote_id:
                quote_ids.append(quote_id)
                logger.info(
                    f"Processed quote of tier: {tier.tier_name} for product: {product.name}"
                )
        return quote_ids

    async def _retrieve_internal_quotes(
        self,
        validated_data: dict[str, Any],
    ) -> QuerySet:
        """
        Fetches quotes from traditional internal insurance providers based on stored data
        """
        product_type = validated_data["insurance_details"]["product_type"]
        product_name = validated_data["insurance_details"].get("product_name")
        providers = self._get_providers_for_product_type(product_type)

        if not providers:
            logger.info(f"No internal providers found for product type: {product_type}")
            return Quote.objects.none()

        query = Q(product_type=product_type, provider__name__in=providers)
        if product_name:
            query &= Q(product__name__icontains=product_name)

        # products = Product.objects.filter(query).prefetch_related(
        #     "tiers", "tiers__coverages"
        # )
        products = await self._fetch_products(query)
        if not products:
            logger.info("No products found for the given criteria.")
            return Quote.objects.none()

        # quote_ids: list[str] = []
        quote_ids = await asyncio.gather(
            *(self._create_quote_for_internal_product(product) for product in products)
        )
        # for product in products:
        #     quote_ids.extend(await self._create_quote_for_internal_product(product))

        flattened_ids = [quote_id for sublist in quote_ids for quote_id in sublist]
        print(f"Quote IDs: {flattened_ids}")

        internal_quotes = Quote.objects.filter(quote_code__in=flattened_ids)
        logger.info(f"Retrieved {internal_quotes.count()} internal quotes")
        return internal_quotes

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
