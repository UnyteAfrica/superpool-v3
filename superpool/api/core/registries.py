import uuid  # noqa: F401

from core.models import Application  # noqa: F401
from rest_framework_api_key.models import APIKey  # noqa: F401


class ApplicationRegistry:
    instance = {}

    def generate_uuid(self) -> str:
        """
        Generate a new UUID
        """
        return str(uuid.uuid4())

    def get_application_instance(self, merchant_id: str) -> Application:
        """
        Returns application instance from the registry
        """
        if merchant_id not in self.instance:
            self.instance[merchant_id] = Application.objects.get(
                merchant_id=merchant_id
            )
        return self.instance[merchant_id]

    def set_application_instance(self, merchant_id: str, instance: Application) -> None:
        """
        Set application instance in the registry
        """
        self.instance[merchant_id] = instance
