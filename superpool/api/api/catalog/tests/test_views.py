import unittest.mock as mock

import pytest
from api.catalog.views import PolicyByProductTypeView, PolicyListView, ProductListView
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from .factories import PolicyFactory, ProductFactory


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def setup_policy_data():
    policy_data = PolicyFactory()
    return policy_data


class TestPolicyViewSet:
    @pytest.mark.django_db
    def test_search_policies_valid_params_is_successful(
        self, api_client, setup_policy_data
    ):
        url = reverse("policy-search")
        response = api_client.get(
            url, {"product_type": setup_policy_data.product.product_type}
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) > 0

    def test_search_policies_empty_params_returns_empty_qs(self, api_client):
        url = reverse("policy-search")
        response = api_client.get(url, {})
        assert response.status_code == status.HTTP_200_OK
        assert response.data == []
        assert len(response.data) == 0

    @pytest.mark.django_db
    def test_retrieve_policy(self, api_client, setup_policy_data):
        url = reverse("policy-detail", kwargs={"pk": setup_policy_data.policy_id})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["policy_id"] == str(setup_policy_data["policy"].policy_id)

    def test_retrieve_policy_not_found(self, api_client):
        url = reverse("policy-detail", kwargs={"pk": "some-non-existent-id"})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND
