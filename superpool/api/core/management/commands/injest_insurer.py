"""
Property of Unyte Africa Limited

Created: 2024-09-17 10:00:00

Maintainer: Eri A. (@50-Course)
"""

import json
import sys
from decimal import Decimal
from pathlib import Path
from textwrap import dedent
from typing import Any

import requests
from django.core.management import BaseCommand
from django.core.management.base import CommandError, CommandParser
from django.db import transaction

from core.catalog.models import Product, ProductTier
from core.models import Coverage
from core.providers.models import Provider


class Command(BaseCommand):
    """
    Injest and onboard insurers and their product into the superpool platform

    Requires a JSON file path to be provided. containing the metadata of the
    insurer and their products.

    For more information,
    see: https://github.com/UnyteAfrica/insurer-policies-quotes?tab=readme-ov-file#superpool
    """

    help = dedent(
        """
        Onboard insurers and their products onto the platform from either a JSON file or a URL.

        Usage:

        1. To ingest data from a local file:

            python manage.py ingest_insurer --path=/path/to/your/file/on/your/system.json

        2. To ingest data from a URL:

            python manage.py ingest_insurer --url=https://example.com/insurer_data.json

        Ensure that only one of --path or --url is provided at a time.
        """
    )

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--path",
            type=Path,
            help="File path (in json) containing the insurers information to be injested",
        )
        parser.add_argument(
            "--url",
            type=str,
            help="URL Path containing the json file with the insurers information",
        )

    def _map_product_type(self, product_name: str):
        """
        Map a product name to the appropriate ProductType.
        """
        if "Life" in product_name:
            return Product.ProductType.LIFE
        elif "Health" in product_name:
            return Product.ProductType.HEALTH
        elif "Auto" in product_name:
            return Product.ProductType.AUTO
        elif "Travel" in product_name:
            return Product.ProductType.TRAVEL
        elif "Gadget" in product_name:
            return Product.ProductType.GADGET
        elif "Home" in product_name:
            return Product.ProductType.HOME
        elif "Personal Accident" in product_name:
            return Product.ProductType.PERSONAL_ACCIDENT
        elif "Student Protection" in product_name:
            return Product.ProductType.STUDENT_PROTECTION
        else:
            return Product.ProductType.OTHER

    def _map_tier_type(self, tier_name: str):
        """
        Map a tier type to the appropriate TierType.
        """
        if "Basic" in tier_name:
            return ProductTier.TierType.BASIC
        elif "Standard" in tier_name:
            return ProductTier.TierType.STANDARD
        elif "Premium" in tier_name:
            return ProductTier.TierType.PREMIUM
        elif "Bronze" in tier_name:
            return ProductTier.TierType.BRONZE
        elif "Silver" in tier_name:
            return ProductTier.TierType.SILVER
        else:
            return ProductTier.TierType.OTHER

    def _read_from_file_path(self, file_path: Path):
        """
        Read JSON file from file path
        """
        with open(file_path, encoding="utf-8") as filebuf:
            return json.load(filebuf)

    def _read_from_network_io(self, url):
        """
        Fetch the JSON data from a URL.
        """
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()  # raise exception is we have errors
            return response.json()
        except requests.RequestException as netioerr:
            return CommandError(f"Failed to fetch data from {url}: {netioerr}")

    def handle(self, *args: Any, **options: Any) -> str | None:
        json_file_path = options.get("path")
        json_url = options.get("url")

        if not json_file_path and not json_url:
            raise CommandError(
                "Please provide either --path or --url for the JSON input."
            )

        # does our file exists?
        if json_file_path:
            if not json_file_path.exists():
                raise CommandError(f"The file path {json_file_path} does not exist.")
            insurer_data = self._read_from_file_path(json_file_path)
        elif json_url:
            insurer_data = self._read_from_network_io(json_url)

        # extract out the insurer information
        insurer_name = insurer_data["insurer"]["name"]
        insurer_email = insurer_data["insurer"]["contact_info"]["email"]
        insurer_phone = insurer_data["insurer"]["contact_info"]["phone"]

        if not insurer_name or not insurer_email:
            raise CommandError(
                "Cannot parse file information. error: INVALID_INSURER_INFO"
            )

        provider, created = Provider.objects.get_or_create(name=insurer_name)

        if not created:
            if provider.support_email != insurer_email:
                self.stdout.write(
                    self.style.WARNING(
                        f"The provided insurer's email differ from what we have on our records."
                        f"Found, {provider.support_email} instead of the newly provided {insurer_email}."
                        "Would you like to update it with the provided one? "
                    )
                )

                email_prompt = input(
                    "Would you like to update it with the provided one? "
                )

                match email_prompt:
                    case "y" | "Y":
                        provider.support_email = insurer_email
                        provider.save()
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"Updated email for {insurer_name} to {insurer_email}"
                            )
                        )
                    case "n" | "N":
                        sys.stdout.write(
                            self.style.NOTICE("Understood! Skipping to next process...")
                        )
                    case _:
                        pass

        else:
            provider.support_email = insurer_email
            provider.support_phone = insurer_phone
            provider.save()
            self.stdout.write(
                f"Created new insurer: {insurer_name} with email {insurer_email}."
            )

        self.stdout.write(f"Detected provider: {provider.name}")

        with transaction.atomic():
            # Process each product and product tiers
            for product_data in insurer_data["products"]:
                self._process_product(provider, product_data)

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully ingested insurer data from {json_file_path}."
            )
        )

    def _process_product(self, provider, product_data):
        """
        Create or update a product for the given provider.
        """

        product_name = product_data["name"]
        product_description = product_data.get("description", "")

        product_type = self._map_product_type(product_name)

        # handle product creation
        product, product_created = Product.objects.get_or_create(
            provider=provider,
            name=product_name,
            defaults={
                "description": product_description,
                "product_type": product_type,
            },
        )

        if product_created:
            self.stdout.write(
                self.style.SUCCESS(f"Created new product: {product_name}")
            )
        else:
            self.stdout.write(
                self.style.NOTICE(f"Product {product_name} already exists")
            )

        for tier_data in product_data["tiers"]:
            self._process_tier(product, tier_data)

    def _process_tier(self, product, tier_data):
        """
        Create or update a product tier for the given product.
        """
        tier_name = tier_data["tier_name"]
        tier_pricing = tier_data["pricing"]
        base_premium = Decimal(tier_pricing["base_premium"])
        _tier_type = tier_data.get("tier_type", "Other")

        tier_type = self._map_tier_type(_tier_type)

        tier, tier_created = ProductTier.objects.get_or_create(
            product=product,
            tier_name=tier_name,
            defaults={
                "base_premium": base_premium,
                "description": tier_data.get("description", ""),
                "tier_type": tier_type,
            },
        )

        if tier_created:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Created tier '{tier_name}' for product '{product.name}'."
                )
            )
        else:
            self.stdout.write(
                self.style.NOTICE(
                    f"Tier '{tier_name}' already exists for product '{product.name}'."
                )
            )

        tier_modified = False

        for coverage_data in tier_data["coverage"]:
            coverage_type_input = coverage_data.get("coverage_type")
            _coverage_type = coverage_type_input
            coverage_type = (
                coverage_type_input
                if coverage_type_input in Coverage.CoverageType.values
                else Coverage.CoverageType.OTHER
            )

            coverage_name = coverage_data.get("coverage_name", _coverage_type)
            coverage_limit = Decimal(coverage_data["coverage_limit"])

            coverage, coverage_created = Coverage.objects.get_or_create(
                coverage_name=coverage_name,
                defaults={
                    "coverage_limit": coverage_limit,
                    "currency": coverage_data["currency"],
                    "coverage_type": coverage_type,
                    "description": coverage_data.get("description", ""),
                },
            )

            if coverage_created:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Created new coverage: {coverage_name} with type: {coverage_type} for tier: {tier_name}"
                    )
                )
                tier_modified = True
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f"Coverage {coverage_name} already exists with type: {coverage.coverage_type} for tier: {tier_name}"
                    )
                )

            if coverage not in tier.coverages.all():
                tier.coverages.add(coverage)
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Added coverage '{coverage_name}' to tier '{tier_name}'."
                    )
                )
                tier_modified = True

        # Update exclusions and benefits only if they have changed
        exclusions_list = tier_data.get("exclusions", [])
        benefits_list = tier_data.get("benefits", [])

        if tier.exclusions != "\n".join(exclusions_list) or tier.benefits != "\n".join(
            benefits_list
        ):
            tier.exclusions = "\n".join(exclusions_list)
            tier.benefits = "\n".join(benefits_list)
            tier_modified = True

        # Save tier only if modified
        if tier_modified:
            tier.save()
