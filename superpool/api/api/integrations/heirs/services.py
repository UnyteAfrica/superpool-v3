from api.integrations.heirs.client import HeirsLifeAssuranceClient


class HeirsAssuranceService:
    def __init__(self) -> None:
        self.client = HeirsLifeAssuranceClient()
