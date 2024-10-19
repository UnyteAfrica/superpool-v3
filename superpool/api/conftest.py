import pytest

#
# @pytest.fixture(autouse=True)
# def setup_django_db():
#     # setup
#     # setup_test_environment()
#     # call_command("migrate", interactive=False, verbosity=3)
#
#     yield
#
#     # teardown
#     teardown_test_environment()
#     connections.close_all()


@pytest.fixture
def api_client():
    from rest_framework.test import APIClient

    return APIClient()
