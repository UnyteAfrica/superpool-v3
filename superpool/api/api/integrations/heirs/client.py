from django.conf import settings

from api.integrations.base import BaseClient

HEIRS_SERVER_URL = (
    settings.HEIRS_ASSURANCE_STAGING_URL or settings.HEIRS_ASSURANCE_PROD_URL
)
"""
Endpoint for the Heirs Assurance API

This approach allows us to switch between the staging and production urls easily
"""


class HeirsLifeAssuranceClient(BaseClient):
    def __init__(self) -> None:
        headers = {
            "X-APP-ID": settings.HEIRS_APP_ID,
        }
        super().__init__(HEIRS_SERVER_URL, settings.HEIRS_APP_ID, headers=headers)

    def get_policy_details(self, policy_id):
        """
        Returns information on a given policy ID
        """
        return self.get(f"/policies/{policy_id}")
