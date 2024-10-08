# Generated by Django 5.0.6 on 2024-09-10 05:47

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0007_alter_policy_policy_holder"),
        ("claims", "0002_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="claim",
            name="policy",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="claims",
                to="catalog.policy",
            ),
        ),
    ]
