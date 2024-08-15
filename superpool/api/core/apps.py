import warnings
from django.apps import AppConfig


def suppress_warnings():
    warnings.filterwarnings(
        "ignore", category=RuntimeWarning, module="django.db.backends.util"
    )


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core"

    def ready(self):
        try:
            import core.signals

            suppress_warnings()
        except ImportError:
            pass
