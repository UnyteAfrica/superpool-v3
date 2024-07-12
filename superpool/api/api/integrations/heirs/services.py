import json
import uuid
from typing import Union

from api.integrations.heirs.client import HeirsLifeAssuranceClient
from core.providers.integrations.heirs.registry import AutoPolicy, CustomerInfo
from django.conf import settings


class HeirsAssuranceService:
    def __init__(self) -> None:
        self.client = HeirsLifeAssuranceClient()

    def get_auto_policy(self, policy_id):
        policy_data = self.client.get_policy_details(policy_id)
        return AutoPolicy(
            id=policy_data["id"],
            policy_num=policy_data.get("policy_num"),
            owner=policy_data["owner"],
            vehicle_make=policy_data["vehicle_make"],
            vehicle_model=policy_data["vehicle_model"],
            year=policy_data["year"],
            chassis_num=policy_data["chassis_num"],
            vehicle_reg_num=policy_data["vehicle_reg_num"],
            vehicle_engine_num=policy_data["vehicle_engine_num"],
            vehicle_designated_use=policy_data["vehicle_designated_use"],
            vehicle_type=policy_data["vehicle_type"],
            value=policy_data["value"],
        )

    def retrieve_quotes(self, category: str = None, **params: dict):
        if not category:
            raise Exception("Policy category must be provided to retrieve quotes")

        # do some pattern matching and return the quotes from the issurer

        # update the database (or maybe call a celery task to update the database)
        return

    def register_policy(self, policy_id: Union[str, int, uuid], reciever: object):
        """
        Register a policy given its policy and the reciever class on Heirs API
        """
        pass

    def register_policy_holder(self, beneficiary_data: CustomerInfo):
        """
        Register a customer as a policy holder on Heirs platform
        """
        register_policy_holder_url = (
            f"{settings.HEIRS_ASSURANCE_STAGING_URL}/policy_holder"
        )

        if not isinstance(beneficiary_data, dict):
            raise TypeError("Policy holder object must be of type dict")

        response = self.client.post(
            url=register_policy_holder_url, data=beneficiary_data
        )
        return response
