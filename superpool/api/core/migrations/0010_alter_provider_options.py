# Generated by Django 5.0.6 on 2024-07-29 17:11

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0009_remove_provider_short_code_and_more"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="provider",
            options={"verbose_name": "Insurer", "verbose_name_plural": "Insurers"},
        ),
    ]