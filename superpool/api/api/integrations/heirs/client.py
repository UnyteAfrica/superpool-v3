from api.integrations.base import BaseClient
from django.conf import settings


class HeirsLifeAssuranceClient(BaseClient):
    def __init__(self) -> None:
        super().__init__(
            settings.HEIRS_ASSURANCE_STAGING_URL, settings.HEIRS_ASSURANCE_APP_ID
        )

    def get_policy_details(self, policy_id):
        """
        Returns information on a given policy ID
        """
        return self.get(f"/policies/{policy_id}")
