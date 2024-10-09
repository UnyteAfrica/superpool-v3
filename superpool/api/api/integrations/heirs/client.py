import logging

from django.conf import settings
from typing_extensions import deprecated

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
        HEIRS_APP_ID = settings.HEIRS_APP_ID
        headers = {"X-APP-ID": HEIRS_APP_ID}
        super().__init__(HEIRS_SERVER_URL, HEIRS_APP_ID, headers=headers)

        logger = logging.getLogger("api_client")
        logger.info("HeirsLifeAssuranceClient initialized.")

    @deprecated(
        "This method is not meant to be used and would be removed in future release"
    )
    def get_policy_details(self, policy_id):
        """
        Returns information on a given policy ID
        """
        return self.get(f"/policies/{policy_id}")
