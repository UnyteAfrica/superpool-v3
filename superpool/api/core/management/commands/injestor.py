import json
from decimal import Decimal
from pathlib import Path
from typing import Any

import requests
from django.core.management import BaseCommand
from django.core.management.base import CommandError, CommandParser
from django.db import transaction

from core.catalog.models import Product, ProductTier


class Command(BaseCommand):
    help = ""

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
        parser.add_argument(
            "--dir",
            type=Path,
            help="Directory path containing the json files to be injested",
        )

    def _read_from_file_path(self, file_path: Path):
        """
        Read JSON file from file path
        """
        with open(file_path, encoding="utf-8") as filebuf:
            return json.load(filebuf)

    def _read_from_network_io(self, url) -> dict | CommandError:
        """
        Fetch the JSON data from a URL.
        """
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()  # raise exception is we have errors
            return response.json()
        except requests.RequestException as netioerr:
            return CommandError(f"Failed to fetch data from {url}: {netioerr}")

    def process_argument(self, *args: Any, **options: Any):
        """
        Process the arguments passed to the command
        """
        if options.get("path"):
            return self._read_from_file_path(options["path"])
        elif options.get("url"):
            return self._read_from_network_io(options["url"])
        elif options.get("dir"):
            dir_path = options["dir"]
            if not dir_path.is_dir():
                raise CommandError("Please provide a valid directory path")

            data = []
            for file in dir_path.iterdir():
                if file.suffix == ".json":
                    data.append(self._read_from_file_path(file))
            return data
        else:
            raise CommandError("Please provide a valid file path or URL")

    def handle(self, *args: Any, **options: Any) -> str | None:
        provider_data = self.process_argument(*args, **options)

        with transaction.atomic():
            self.stdout.write(self.style.NOTICE("Starting data injestion"))
            self.stdout.write(self.style.NOTICE("Processing data..."))
            self.parse_data(provider_data)

        self.stdout.write(self.style.SUCCESS("Data injestion successful"))

    def _map_product_type(self, product_category: str) -> Product.ProductType:
        """
        Map the product category to the ProductType enum
        """
        PRODUCT_CATEGORY = data.get("Product_Category")

        if not PRODUCT_CATEGORY:
            raise CommandError("Product Category is required")

        # Key:
        #
        # PRODUCT CATEGORY  (we have to do, case-insenstive match):
        # Auto, Automobile, Auto Insurance == AUTO
        # Travel == TRAVEL
        # Education == Student_Protection
        # Health == HEALTH
        # Home == HOME

        if PRODUCT_CATEGORY.lower() in ["auto", "automobile", "auto insurance"]:
            product_type = Product.ProductType.AUTO
        elif PRODUCT_CATEGORY.lower() == "travel":
            product_type = Product.ProductType.TRAVEL
        elif PRODUCT_CATEGORY.lower() == "education":
            product_type = Product.ProductType.STUDENT_PROTECTION
        elif PRODUCT_CATEGORY.lower() == "health":
            product_type = Product.ProductType.HEALTH
        elif PRODUCT_CATEGORY.lower() == "home":
            product_type = Product.ProductType.HOME
        elif PRODUCT_CATEGORY.lower() == "life":
            product_type = Product.ProductType.LIFE
        elif PRODUCT_CATEGORY.lower() in ["personal accident", "accident"]:
            product_type = Product.ProductType.PERSONAL_ACCIDENT
        else:
            product_type = Product.ProductType.OTHER

        return product_type

    def _map_tier_type(self, tier: str) -> ProductTier.TierType:
        """
        Map the tier type to the TierType enum
        """
        if tier not in ProductTier.TierType.values:
            tier_type = ProductTier.TierType.OTHER
        else:
            tier_type = tier
        return tier_type

    def _validate_provider(self, provider: str) -> str:
        """
        Validate the provider name
        """
        if provider in ("AXA", "AXA Mansard", "AXA Mansard Insurance Plc"):
            return "AXA Mansard"
        elif provider in ("NEM", "NEM Insurance Plc."):
            return "NEM Insurance Plc."
        else:
            return provider

    def parse_data(self, data: Any) -> dict:
        """
        Parse the data and return the processed data

        Parses the incoming data of the format:

        [
        {
            "Product": "SMART STUDENT PROTECTION PLAN",
            "Insurer": "NEM Insurance Plc.",
            "Commission(%)": "",
            "Product_Category": "Education",
            "Premiums": [
                {
                    "Product Type": "SILVER",
                    "Premium (cost per unit) (N)": "1,500",
                    "Premium Payment Frequency": "",
                    "Flat Fee": ""
                },
                {
                    "Product Type": "GOLD",
                    "Premium (cost per unit) (N)": "2,500",
                    "Premium Payment Frequency": "",
                    "Flat Fee": ""
                },
                {
                    "Product Type": "PLATINUM",
                    "Premium (cost per unit) (N)": "3,500",
                    "Premium Payment Frequency": "",
                    "Flat Fee": ""
                },
                {
                    "Product Type": "DIAMOND",
                    "Premium (cost per unit) (N)": "5,500",
                    "Premium Payment Frequency": "",
                    "Flat Fee": ""
                }
            ]
        }
        ]

        """

        provider = data.get("Insurer")
        provider_name = self._validate_provider(provider)

        product_name = data.get("Product")
        product_type = self._map_product_type(data.get("Product_Category"))

        # Now we would create a product object
        product, _ = Product.objects.get_or_create(
            provider=provider_name, name=product_name, product_type=product_type
        )

        premiums = data.get("Premiums")

        if not premiums:
            raise CommandError("Premiums data is required")

        for premium in premiums:
            # Here now we would map each object in the premium
            # to a tier?
            tier = premium.get("Product Type")
            tier_type = self._map_tier_type(tier)
            premium_cost = premium.get("Premium (cost per unit) (N)")

            # Now we would create a tier object for the product
            tier_obj, _ = ProductTier.objects.get_or_create(
                name=tier,
                product=product,
                base_premium=Decimal(premium_cost.replace(",", "")),
                tier_type=tier_type,
            )
            product.tiers.add(tier_obj)
