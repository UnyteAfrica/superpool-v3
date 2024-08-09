from django.core.management import BaseCommand
from django.core.exceptions import ValidationError
from django.utils.dateparse import parse_date
import sys
from decimal import Decimal

from rest_framework.generics import RetrieveUpdateAPIView

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
            "--quote_code",
            type=str,
            required=True,
            help="Quote code to purchase policy for",
        )
        parser.add_argument(
            "--first_name",
            type=str,
            required=True,
            help="First name of the policy holder",
        )
        parser.add_argument(
            "--last_name",
            type=str,
            required=True,
            help="Last name of the policy holder",
        )
        parser.add_argument(
            "--customer_email", type=str, required=True, help="Email of the customer"
        )
        parser.add_argument(
            "--customer_phone",
            type=str,
            required=True,
            help="Phone number of the customer",
        )
        parser.add_argument(
            "--customer_address",
            type=str,
            required=False,
            help="Address of the policy holder",
        )
        parser.add_argument(
            "--customer_date_of_birth",
            type=str,
            required=False,
            help="Date of birth of the policy holder",
        )
        parser.add_argument(
            "--customer_gender",
            choices=["M", "F"],
            type=str,
            required=False,
            help="Sexual orientation of the policy holder",
        )
        parser.add_argument(
            "--policy_name",
            type=str,
            required=True,
            help="Name of the insurance policy (or product) to purchase",
        )
        parser.add_argument(
            "--product_type",
            type=str,
            required=True,
            help="Type of the insurance product or policy",
        )
        parser.add_argument(
            "--product_code",
            type=str,
            required=False,
            help="Code of the insurance product or policy",
        )
        parser.add_argument(
            "--payment_method",
            type=str,
            choices=["card", "wallet", "bank_transfer", "online_banking"],
            default="card",
            help="Payment method to use for the purchase",
        )
        parser.add_argument(
            "--payment_reference",
            type=str,
            required=False,
            help="Reference number of the payment made",
        )
        parser.add_argument(
            "--payment_status",
            type=str,
            choices=["completed", "pending"],
            help="Status of the payment",
            required=False,
        )
        parser.add_argument(
            "--premium_amount",
            type=Decimal,
            required=True,
            help="Amount paid for the policy",
        )
        parser.add_argument(
            "--policy_expiry_date",
            type=str,
            required=True,
            help="Date the policy is expected to expire in the format YYYY-MM-DD",
        )
        parser.add_argument(
            "--renew",
            action="store_true",
            help="Flag to indicate if the policy should be renewed",
        )
        parser.add_argument(
            "--merchant_code",
            type=str,
            required=True,
            help="Unique short code identifier assigned to the merchant",
        )

    def handle(self, args, options):
        try:
            policy_data = {
                "quote_code": options["quote_code"],
                "customer_metadata": {
                    "first_name": options["first_name"],
                    "last_name": options["last_name"],
                    "customer_email": options["customer_email"],
                    "customer_phone": options["customer_phone"],
                    "customer_address": options.get("customer_address"),
                    "customer_date_of_birth": options.get("customer_date_of_birth"),
                    "customer_gender": options.get("customer_gender"),
                },
                "payment_metadata": {
                    "payment_status": options["payment_status"],
                    "premium_amount": options["premium_amount"],
                },
                "activation_metadata": {
                    "policy_expiry_date": parse_date(options["policy_expiry_date"]),
                    "renew": options.get("renew", False),
                },
                "merchant_code": options["merchant_code"],
            }

            policy = PolicyService.purchase_policy(policy_data)
            sys.stdout.write(
                f"Policy purchased successfully for quote {options['quote_code']}: {policy.policy_id} \n"
            )
            sys.stdout.write(f"Policy details: {policy}\n")
        except ValueError as e:
            sys.stderr.write(f"An error occurred: {e}\n")
        except ValidationError as e:
            sys.stderr.write(f"Validation error: {e}\n")
        except Quote.DoesNotExist:
            sys.stderr.write("Quote does not exist\n")
        except Merchant.DoesNotExist:
            sys.stderr.write("Merchant does not exist\n")
        except Exception as e:
            sys.stderr.write(f"An error occurred: {e}\n")
