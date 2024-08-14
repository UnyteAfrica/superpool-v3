import uuid
from django.core.management import BaseCommand
from core.utils import send_verification_email
from core.models import Merchant
from django.core.exceptions import ObjectDoesNotExist


class Command(BaseCommand):
    help = "Resend verification email to a given merchant"

    def add_arguments(self, parser):
        parser.add_argument("short_code", type=str, help="Merchant Short code")
        parser.add_argument(
            "--tenant_id", type=uuid.UUID, help="Tenant ID", required=False
        )

    def handle(self, *args, **options):
        short_code = options["short_code"]
        tenant_id = options.get("tenant_id")

        try:
            if tenant_id:
                # attempt to get merchant with both short_code and tenant_id
                merchant = Merchant.objects.get(
                    short_code=short_code, tenant_id=tenant_id
                )
            else:
                merchant = Merchant.objects.get(short_code=short_code)

            # merchant does not have a verification token?
            if not merchant.token:
                self.stdout.write(
                    self.style.WARNING(f"No verification token found for {short_code}.")
                )
                return

            send_verification_email(
                merchant.business_email, merchant.token, merchant.short_code
            )

            self.stdout.write(
                self.style.SUCCESS(
                    f"Verification email sent to {merchant.business_email} for {merchant.short_code}"
                )
            )

        except ObjectDoesNotExist:
            self.stdout.write(
                self.style.ERROR(
                    f"Merchant with short code '{short_code}' does not exist."
                )
            )
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error: {e}"))
