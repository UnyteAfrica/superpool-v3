from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core"

    def ready(self):
        print(f"Core app is ready! Successsfully loaded all signals")
        import core.signals
