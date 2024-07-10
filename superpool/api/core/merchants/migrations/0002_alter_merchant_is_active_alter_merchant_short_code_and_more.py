
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("merchants", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="merchant",
            name="is_active",
            field=models.BooleanField(
                default=False, help_text="Designates if the merchant is active"
            ),
        ),
        migrations.AlterField(
            model_name="merchant",
            name="short_code",
            field=models.CharField(
                help_text="Unique short code indentifier used internally to identify a merchant or distributore.g. UBA-X224, GTB-3X2, KON-001, SLOT-001, WEMA-2286, etc.",
                max_length=10,
                null=True,
                unique=True,
                verbose_name="Merchant Short code",
            ),
        ),
        migrations.AlterField(
            model_name="merchant",
            name="support_email",
            field=models.EmailField(
                blank=True,
                help_text="The contact email address of the business, for support if any",
                max_length=254,
                null=True,
                verbose_name="Support Email",
            ),
        ),
    ]
