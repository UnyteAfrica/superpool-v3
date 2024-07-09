from api.integrations.heirs.client import HeirsLifeAssuranceClient
from core.providers.integrations.heirs.registry import AutoPolicy


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
