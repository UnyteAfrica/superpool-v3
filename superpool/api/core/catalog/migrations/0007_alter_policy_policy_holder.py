# Generated by Django 5.0.6 on 2024-09-10 05:47

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0006_alter_quote_expires_in"),
        ("core", "0005_remove_coverage_product_coverage_currency"),
    ]

    operations = [
        migrations.AlterField(
            model_name="policy",
            name="policy_holder",
            field=models.ForeignKey(
                help_text="User who purchased the policy",
                on_delete=django.db.models.deletion.CASCADE,
                related_name="policies",
                to="core.customer",
            ),
        ),
    ]