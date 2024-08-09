from django.core.management import BaseCommand
from django.core.exceptions import ValidationError
from django.utils.dateparse import parse_date
import sys
from decimal import Decimal

from core.catalog.models import Quote, Policy
from core.merchants.models import Merchant
from api.catalog.services import PolicyService


class Command(BaseCommand):
    """
    This command is used to create a purchase insurance policy for a given quote
    """

    help = "Purchase a policy by providing necessary details"

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "quote_code", type=str, help="Quote code to purchase policy for"
        )
        parser.add_argument(
            "--first_name", type=str, help="First name of the policy holder"
        )
        parser.add_argument(
            "--last_name", type=str, help="Last name of the policy holder"
        )
        parser.add_argument("customer_email", type=str, help="Email of the customer")
        parser.add_argument(
            "--customer_phone", type=str, help="Phone number of the customer"
        )
        parser.add_argument(
            "--customer_date_of_birth",
            type=str,
            help="Date of birth of the policy holder",
        )
        parser.add_argument(
            "--customer_gender",
            choices=["M", "F"],
            type=str,
            help="Sexual orientation of the policy holder",
        )
        parser.add_argument(
            "policy_name",
            type=str,
            help="Name of the insurance policy (or product) to purchase",
        )
        parser.add_argument(
            "product_type",
            type=str,
            help="Type of the insurance product or policy",
        )
        parser.add_argument(
            "product_code",
            type=str,
            help="Code of the insurance product or policy",
            required=False,
        )
        parser.add_argument(
            "payment_method",
            type=str,
            help="Payment method to use for the purchase",
            choices=["card", "wallet", "bank_transfer", "online_banking"],
        )
        parser.add_argument(
            "payment_reference",
            type=str,
            help="Reference number of the payment made",
            required=False,
        )
        parser.add_argument(
            "payment_status",
            type=str,
            choices=["completed", "pending"],
            help="Status of the payment",
            optional=True,
        )
        parser.add_argument(
            "premium_amount",
            type=Decimal,
            help="Amount paid for the policy",
            required=False,
        )
        parser.add_argument(
            "policy_expiry_date",
            type=str,
            help="Date the policy is expected to expire in the format YYYY-MM-DD",
        )
        parser.add_argument(
            "--renew",
            action="store_true",
            help="Flag to indicate if the policy should be renewed",
        )
        parser.add_argument(
            "merchant_code",
            type=str,
            help="Unique short code identifier assigned to the merchant",
        )

    def handle(self, args, options) -> "Policy" | None:
        pass
