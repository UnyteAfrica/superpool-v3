import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from api.merchants.tests.factories import MerchantFactory
from core.providers.models import Provider

# WE WOULD BE TESTING OUR MIDDLEWARE SINCE ITS MEANT TO INTERACT WITH
# THE REQUEST AND RESPONSE OBJECTS


@pytest.fixture
def auth_data():
    merchant = MerchantFactory()
    application = merchant.application_set.first()
    return {
        "merchant": merchant,
        "application": application,
    }


@pytest.mark.django_db
def test_request_authenticated_with_middleware_and_correct_credentials(auth_data):
    pass


@pytest.mark.django_db
def test_request_unauthenticated_with_middleware_and_incorrect_credentials():
    pass


@pytest.mark.django_db
def test_request_unauthenticated_with_middleware_and_no_credentials():
    pass


@pytest.mark.insurer
class TestInsurerAPIView(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.provider1 = Provider.objects.create(
            id="e1a5d88c-4b23-4b90-8e7a-b3fef95e3a80",
            name="Acme Insurance Co.",
            address="123 Elm Street, Springfield, IL",
            phone_number="+1-800-555-1234",
        )
        cls.provider2 = Provider.objects.create(
            id="d8e9d79a-d1c1-4f07-b6d8-7399be13b47e",
            name="Globex Corporation",
            address="456 Oak Avenue, Metropolis, NY",
            phone_number="+1-800-555-5678",
        )
        cls.provider3 = Provider.objects.create(
            id="ff7b7b3c-2df9-4b93-9f2e-9bde4b7a40da",
            name="Initech Insurance",
            address="789 Pine Road, Silicon Valley, CA",
            phone_number="+1-800-555-9876",
        )

    def test_insurer_list(self):
        url = reverse("insurers")
        response = self.client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 3
        assert response.data[0]["name"] == "Acme Insurance Co."
        assert response.data[1]["name"] == "Globex Corporation"
        assert response.data[2]["name"] == "Initech Insurance"
