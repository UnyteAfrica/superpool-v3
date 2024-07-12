import requests
from api.integrations.base import IClient
from django.conf import settings
from rest_framework import status


class HeirsLifeAssuranceClient(IClient):
    def __init__(self):
        self.base_url = settings.HEIRS_ASSURANCE_BASE_URL
        self.api_key = settings.HEIRS_ASSURANCE_API_KEY
        super().__init__()

    def get(self, url):
        url = f"{self.base_url}/url"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def post(self, url, data):
        url = f"{self.base_url}/url"
        response = requests.post(url, headers=self.headers, json=data)
        response.raise_for_status()
        return response.json()

    def get_policy_details(self, policy_id):
        """
        Returns information on a given policy ID
        """
        return self.get(f"/policies/{policy_id}")
