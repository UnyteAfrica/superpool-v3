# Generated by Django 5.0.6 on 2024-09-18 14:24

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0011_producttier_tier_type_alter_producttier_tier_name"),
        ("core", "0006_coverage_coverage_type"),
    ]

    operations = [
        migrations.AddField(
            model_name="quote",
            name="purchase_id",
            field=models.CharField(
                blank=True,
                help_text="Unique identifier provided to payment processors to identify a quote purchase",
                max_length=100,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="quote",
            name="purchase_id_created_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="producttier",
            name="base_preimum",
            field=models.DecimalField(
                decimal_places=2,
                help_text="The base premium price for this tier before any adjustments or discounts",
                max_digits=10,
            ),
        ),
        migrations.AlterField(
            model_name="producttier",
            name="coverages",
            field=models.ManyToManyField(
                blank=True,
                help_text="Detailed breakdown of coverages provided in this tier. Example: Health, Accident, etc.",
                to="core.coverage",
            ),
        ),
        migrations.AlterField(
            model_name="producttier",
            name="description",
            field=models.TextField(
                blank=True,
                help_text="Optional description of what the tier offers, such as specific benefits or target audience",
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="producttier",
            name="pricing",
            field=models.ForeignKey(
                blank=True,
                help_text="Pricing details for this tier, including surcharges or discounts",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="catalog.price",
            ),
        ),
        migrations.AlterField(
            model_name="producttier",
            name="tier_type",
            field=models.CharField(
                blank=True,
                choices=[
                    ("Basic", "Basic Insurance"),
                    ("Advanced", "Advanced"),
                    ("Standard", "Standard Insurance"),
                    ("Premium", "Premium"),
                    ("Bronze", "Bronze"),
                    ("Silver", "Silver"),
                    ("Other", "Other"),
                ],
                help_text="Type of tier. Choose from predefined options such as Basic, Premium, Silver, Corporate, Comprehensive, etc. An optional classification that further categorizes the tier",
                max_length=255,
                null=True,
            ),
        ),
    ]