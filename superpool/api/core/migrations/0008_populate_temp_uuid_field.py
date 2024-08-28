# This migration is used to populate the temp_uuid field from 0007_migration file
# with a random uuid

import uuid
from django.db import migrations


def populate_temp_uuid(apps, schema_editor):
    # quickly help us populate the db with some random uuid
    ApiKey = apps.get_model("core", "ApiKey")
    for api_key in ApiKey.objects.all():
        api_key.temp_uuid = uuid.uuid4()
        api_key.save()


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0007_add_temp_uuid_field"),
    ]

    operations = [
        migrations.RunPython(populate_temp_uuid),
    ]
