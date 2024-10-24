# Generated by Django 5.0.6 on 2024-09-23 13:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0013_rename_base_preimum_producttier_base_premium_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="quote",
            name="policy_terms",
            field=models.JSONField(
                blank=True,
                default={},
                help_text="Terms and conditions of the insurance policy, stored as a JSON object.",
            ),
        ),
    ]
