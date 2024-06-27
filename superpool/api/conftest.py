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

    with override_settings(
        DATABASES=test_settings["DATABASES"],
    ):
        settings.configure(
            DEBUG=True,
        )

        import django

        django.setup()
        yield
