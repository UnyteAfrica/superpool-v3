from django.apps import AppConfig


class ClaimsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core.claims"


# We using config class to create a new configguration class tat utilize UUID
# to avoid the problem of migraitons in future
class ClaimsV2Config(AppConfig):
    default_auto_field = "django.db.models.UUIDField"
    name = "core.claims"
