# Generated by Django 5.0.6 on 2024-08-05 12:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0010_policy_cancellation_date_and_more"),
    ]

    operations = [
        migrations.RenameField(
            model_name="price",
            old_name="value",
            new_name="amount",
        ),
        migrations.RenameField(
            model_name="price",
            old_name="comission",
            new_name="commision",
        ),
        migrations.AddField(
            model_name="price",
            name="description",
            field=models.TextField(blank=True, null=True),
        ),
    ]