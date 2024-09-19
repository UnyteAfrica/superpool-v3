import uuid

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient


@pytest.fixture
def client():
    return APIClient()


@pytest.mark.django_db
def test_claim_id_present_in_API_response(client):
    CLAIMS_API_URL = reverse("claims-list")

    response = client.get(CLAIMS_API_URL)

    assert response.status_code == status.HTTP_200_OK
    # ensure that there is at least a claim in the  response
    assert len(response.data) > 0
    # ensure that the claim_id is present in a claim
    assert "claim_id" in response.data[0]
    # ensure that the claim_id is a UUID
    assert isinstance(response.data[0]["claim_id"], uuid.UUID)
