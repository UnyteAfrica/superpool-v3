# Generated by Django 5.0.6 on 2024-09-10 05:55

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("claims", "0003_alter_claim_policy"),
        ("core", "0005_remove_coverage_product_coverage_currency"),
    ]

    operations = [
        migrations.AlterField(
            model_name="claim",
            name="customer",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="claims",
                to="core.customer",
            ),
        ),
    ]