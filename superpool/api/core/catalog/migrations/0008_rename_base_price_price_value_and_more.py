# Generated by Django 5.0.6 on 2024-07-25 12:59

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        (
            "catalog",
            "0007_price_remove_quote_id_quote_expires_in_quote_product_and_more",
        ),
    ]

    operations = [
        migrations.RenameField(
            model_name="price",
            old_name="base_price",
            new_name="value",
        ),
        migrations.RemoveField(
            model_name="product",
            name="base_price",
        ),
    ]