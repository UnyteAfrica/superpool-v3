import unittest.mock as mock

import pytest
from api.catalog.views import PolicyByProductTypeView, PolicyListView, ProductListView
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .factories import PolicyFactory, ProductFactory


class PolicyByProductTypeViewTest(APITestCase):
    def test_get_policy_by_product_type(self):
        url = reverse("policy-by-product-type", kwargs={"product_type": "Gadget"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
