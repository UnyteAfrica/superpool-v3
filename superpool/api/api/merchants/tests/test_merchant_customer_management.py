import pytest
from rest_framework.test import APIClient, APITestCase
from rest_framework import status
from django.urls import reverse
from .factories import CustomerFactory, MerchantFactory


class TestCustomerDetailEndpointView(APITestCase):
    def setUp(self) -> None:
        self.merchant = MerchantFactory.build()
        self.customer = CustomerFactory.build()
        self.url = reverse(
            "merchant-customer-detail", args=[self.merchant.tenant_id, self.customer.pk]
        )

    def test_merchant_cannot_access_other_merchant_customers(self):
        pass

    def test_merchant_can_retrieve_customer_details(self):
        response = self.client.get(self.url)

        self.assertTrue(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["customer_id"], self.customer.id)
        self.assertEqual(response.data["first_name"], self.customer.first_name)
        self.assertEqual(response.data["last_name"], self.customer.last_name)
        self.assertEqual(response.data["customer_email"], self.customer.email)

    def test_merchant_cannot_retrieve_customer_details_with_invalid_details(self):
        pass

    def test_merchant_cannot_retrieve_customer_details_with_no_arguments(self):
        self.url = reverse("merchant-customer-detail", args=[])

        response = self.client.get(self.url)
        self.assertTrue(response.status_code, status.HTTP_400_BAD_REQUEST)
