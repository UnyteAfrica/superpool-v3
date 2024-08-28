# manual migration written to resolve type conversion from bigint to uuid
# for field id

import uuid
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0006_remove_application_api_token_remove_application_id_and_more")
    ]

    operations = [
        migrations.AddField(
            model_name="apikey",
            name="temp_uuid",
            field=models.UUIDField(default=uuid.uuid4, editable=False),
        )
    ]
