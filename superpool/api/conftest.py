import sys

import pytest
from django.conf import settings
from django.test.utils import override_settings


@pytest.fixture(scope="session", autouse=True)
def configure_tests_db():
    """
    Sets up the database for testing.

    """
    # We've got to make a copy of the actual settings,
    # because directly modifying settings.DATABASES will
    # affect the actual database settings, creating conflicts
    test_settings = settings.copy()
    test_settings["DATABASES"]["default"] = {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
    test_settings["DEBUG"] = True
    test_settings["TEST_RUNNER"] = "django.test.runner.DiscoverRunner"
    test_settings["DATABASE_ROUTERS"] = []

    with override_settings(**test_settings):
        settings.configure(**test_settings)

        # We need to reload the models to avoid the "AppRegistryNotReady: Apps aren't loaded yet." error
        import django

        django.setup()
        yield
