from _pytest.config import argparsing
import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
import api
from api.merchants.tests.factories import MerchantFactory, CustomerFactory

User = get_user_model()


@pytest.fixture(scope="function")
def admin_user():
    admin = User.objects.create_superuser("admin", "admin@example.com")
    return admin


@pytest.fixture
def merchant_user():
    user = User("randommerchant", "merchant@example.com")
    user.set_password("password")
    merchant = MerchantFactory.build(user=user)
    return merchant


@pytest.fixture
def api_client():
    return APIClient()


class TestCustomerManagementAPI:
    def test_admin_can_view_all_customers(self, api_client, admin_user):
        api_client.force_authenticate(user=admin_user)

        response = api_client.get(reverse("customers-list"))

        assert response.status_code == 200
        assert len(response.data) > 0

    def test_merchant_can_view_all_their_customers(self, api_client, merchant_user):
        api_client.force_authenticate(user=merchant_user)
        response = api_client.get(
            reverse("merchant-customers-list"),
            kwargs={"tenant_id": merchant_user.tenant_id},
        )

        assert response.status_code == 200
        assert len(response.data > 0)

    def test_merchant_cannot_view_another_merchant_customers(
        self, api_client, merchant_user
    ):
        different_merchant = MerchantFactory.build(
            name="DIfferent Merchant PLC",
            business_email="different.merchant@example.com",
            support_email="different.merchant@example.com",
            is_active=True,
            user__username="different.merchant@example.com",
            user__password="examplepassword",
            user__role="merchant",
        )

        # authenticate this merchant
        api_client.force_authenticate(user=different_merchant.user)

        response = api_client.get(
            reverse("merchant-customers-list"),
            kwargs={"tenant_id": different_merchant.tenant_id},
        )

        assert response.status_code == 200
        assert len(response.data > 0)

    def test_merchant_admin_support_can_view_detailed_customer_information(
        self, api_client
    ):
        pass
