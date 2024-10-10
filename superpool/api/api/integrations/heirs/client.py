import logging

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
        HEIRS_APP_ID = settings.HEIRS_ASSURANCE_APP_ID
        headers = {"X-APP-ID": HEIRS_APP_ID}
        super().__init__(HEIRS_SERVER_URL, HEIRS_APP_ID, headers=headers)

        logger = logging.getLogger("api_client")
        logger.info("HeirsLifeAssuranceClient initialized.")
