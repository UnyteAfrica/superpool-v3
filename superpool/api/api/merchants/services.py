from core.merchants.models import Merchant
from core.models import Application
from core.registries import ApplicationRegistry
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from .exceptions import ApplicationCreationError


class AppicationService:
    """
    Handler for the manging and working with application instances
    """

    registry = ApplicationRegistry()

    @classmethod
    def create_application(cls, merchant: Merchant) -> tuple[Application, str]:
        """
        Create a new application instance
        """

        application_id = cls.registry.generate_uuid()
        try:
            application = Application.objects.create(
                merchant=merchant, application_id=application_id
            )
        except (IntegrityError, ValidationError, Exception) as e:
            raise ApplicationCreationError(
                "An error occurred while creating the application for this merchant", e
            )
        cls.registry.set_application_instance(
            merchant_id=merchant.internal_id, instance=application
        )
        return application, application_id

    @classmethod
    def get_application(cls, merchant: Merchant) -> Application:
        """
        Get the application instance for a merchant
        """
        return cls.registry.get_application_instance(merchant.internal_id)

    @classmethod
    def set_test_mode(cls, application: Application, test_mode: bool) -> Application:
        """
        Set the test mode for an application
        """
        application.test_mode = test_mode
        application.save()
        return application
