# Generated by Django 5.0.6 on 2024-08-28 15:08

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0023_apikey_key_apikey_key_hash"),
    ]

    operations = [
        migrations.AddField(
            model_name="apikey",
            name="key",
            field=models.CharField(
                blank=True,
                help_text="Unique key generated on the platform for use in subsequent request",
                max_length=150,
                unique=True,
            ),
        ),
        migrations.AlterField(
            model_name="apikey",
            name="key_hash",
            field=models.CharField(
                blank=True,
                help_text="Hashed value of the key shared with the merchant. Always use this and never use the actual `key` in requests.",
                max_length=150,
                unique=True,
            ),
        ),
        migrations.AlterField(
            model_name="application",
            name="api_key",
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="applications",
                to="core.apikey",
            ),
        ),
    ]