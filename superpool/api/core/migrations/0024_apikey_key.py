# Generated by Django 5.0.6 on 2024-08-28 14:20

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
                default="default_key",
                help_text="Unique key generated on the platform for use in subsequent request",
                max_length=150,
                unique=True,
            ),
            preserve_default=False,
        ),
    ]