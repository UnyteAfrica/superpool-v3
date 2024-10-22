import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from api.claims.tests.factories import ClaimFactory


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def claim():
    return ClaimFactory.build(
        claim_number="CLM202410",
        incident_date="2024-08-01",
    )


class TestClaimsAPIView:
    @pytest.mark.django_db
    def test_filter_claims_incorrect_query_param_returns_empty_list(
        self, client, claim
    ):
        url = reverse("claims-list")
        query_params = {"insurer": "non_existent_insurer"}
        response = client.get(url, query_params)

        assert response.status_code == 200
        assert len(response.data) == 0

    @pytest.mark.django_db
    def test_update_claim_with_put_request_returns_405(self, client, claim):
        url = reverse("claims-detail", args=[claim.id])
        payload = {
            "claimant_metadata": {"email": "new.email@example.com"},
            "claim_details": {"incident_date": "2024-09-01"},
        }
        response = client.put(url, payload, format="json")
        assert response.status_code == 405

    @pytest.mark.django_db
    def test_update_claim_with_patch_request_returns_200(self, client, claim):
        url = reverse("claims-detail", args=[claim.id])
        payload = {
            "claimant_metadata": {"email": "new.email@example.com"},
            "claim_details": {"incident_date": "2024-09-01"},
        }
        response = client.patch(url, payload, format="json")
        assert response.status_code == 200

        claim.refresh_from_db()

        # reassert
        assert claim.claimant.email == "new.email@example.com"
        assert str(claim.incident_date) == "2024-09-01"
