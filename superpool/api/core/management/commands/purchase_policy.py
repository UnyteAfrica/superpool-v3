from django.core.management import BaseCommand
from django.core.exceptions import ValidationError
from django.utils.dateparse import parse_date
import sys
from decimal import Decimal

from core.catalog.models import Quote
from core.merchants.models import Merchant
from api.catalog.services import PolicyService


class Command(BaseCommand):
    """
    This command is used to create a purchase insurance policy for a given quote
    """

    help = "urchase a policy by providing necessary details"

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "quote_code",
            type=str,
            help="Quote code for which policy needs to be purchased",
        )
        parser.add_argument("customer_email", type=str, help="Email of the customer")
        parser.add_argument(
            "product_name", type=str, help="Name of the insurance policy"
        )
        parser.add_argument(
            "product_type", type=str, help="Type of the insurance policy"
        )
        parser.add_argument("payment_method", type=str)
        parser.add_argument("payment_status", type=str)
        parser.add_argument("premium_amount", type=Decimal)
        parser.add_argument("policy_expiry_date", type=str)
        parser.add_argument(
            "renew", type=bool, default=False, help="Should the policy be renewed?"
        )
        parser.add_argument("agreement", type=bool, default=True)
        parser.add_argument("confirmation", type=bool, default=True)
        parser.add_argument(
            "merchant_code",
            type=str,
            help="Unique short code identifier assigned to the merchant",
        )

    def handle(self, *args, **options):
        try:
            quote_code = options["quote_code"]
            customer_email = options["customer_email"]
            product_name = options["product_name"]
            product_type = options["product_type"]
            payment_method = options["payment_method"]
            payment_status = options["payment_status"]
            premium_amount = options["premium_amount"]
            policy_expiry_date = parse_date(options["policy_expiry_date"])
            renew = options["renew"]
            agreement = options["agreement"]
            confirmation = options["confirmation"]
            merchant_code = options["merchant_code"]

            quote = Quote.objects.get(quote_code=quote_code)

            # TODO: fetch neccessary information from quotes

            policy_data = {
                "quote_code": quote_code,
                "customer_metadata": {
                    "customer_email": customer_email,
                },
                "product_metadata": {
                    "product_name": product_name,
                    "product_type": product_type,
                },
                "payment_metadata": {
                    "payment_method": payment_method,
                    "payment_status": payment_status,
                    "premium_amount": premium_amount,
                },
                "activation_metadata": {
                    "policy_expiry_date": policy_expiry_date,
                    "renew": renew,
                },
                "agreement": agreement,
                "confirmation": confirmation,
                "merchant_code": merchant_code,
            }

            PolicyService.purchase_policy(policy_data)
        except ValidationError as e:
            sys.stderr.write(f"Validation Error: {e}")
        except Quote.DoesNotExist:
            sys.stderr.write("Quote does not exist")
        except Merchant.DoesNotExist:
            sys.stderr.write("Merchant does not exist")
        except Exception as e:
            sys.stderr.write(f"Error: {e}")
