import pytest
from django.urls import reverse
from rest_framework.test import APIClient


@pytest.fixture
def client():
    return APIClient()


class TestClaimsAPIView:
    @pytest.mark.django_db
    def test_filter_claims_incorrect_query_param_returns_empty_list(self, client):
        url = reverse("claims-list")
        query_params = {"insurer": "non_existent_insurer"}
        response = client.get(url, query_params)

        assert response.status_code == 200
        assert len(response.data) == 0
