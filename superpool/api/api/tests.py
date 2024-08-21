from django.test import TestCase
import pytest
from rest_framework.test import APIClient
from api.merchants.tests.factories import MerchantFactory
from rest_framework import status
from django.urls import reverse
from django.db import connections

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


MERCHANTS_URL = reverse("merchants-list")


@pytest.mark.django_db
def test_request_authenticated_with_middleware_and_correct_credentials(auth_data):
    client = APIClient()
    headers = {
        "X-Merchant-ID": auth_data["merchant"].id,
        "X-APP-ID": auth_data["application"].id,
    }

    response = client.get(
        MERCHANTS_URL,
        HTTP_X_MERCHANT_ID=headers["X-Merchant-ID"],
        HTTP_X_APP_ID=headers["X-APP-ID"],
    )

    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_request_unauthenticated_with_middleware_and_incorrect_credentials():
    client = APIClient()
    headers = {
        "X-Merchant-ID": "123",
        "X-APP-ID": "123",
    }
    response = client.get(
        MERCHANTS_URL,
        HTTP_X_MERCHANT_ID=headers["X-Merchant-ID"],
        HTTP_X_APP_ID=headers["X-APP-ID"],
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_request_unauthenticated_with_middleware_and_no_credentials():
    client = APIClient()

    response = client.get(MERCHANTS_URL)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_db_connection(self):
    connection = connections["default"]
    connection.ensure_connection()
    assert connection.is_usable()
