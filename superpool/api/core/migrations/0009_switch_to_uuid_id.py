from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0008_populate_temp_uuid_field"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="apikey",
            name="id",
        ),
        migrations.RenameField(
            model_name="apikey",
            old_name="temp_uuid",
            new_name="id",
        ),
    ]
