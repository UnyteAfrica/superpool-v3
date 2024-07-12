import abc
from dataclasses import dataclass
from datetime import date
from typing import Optional, TypedDict

from api.integrations.heirs.client import HeirsLifeAssuranceClient


class Policy(abc.ABC):
    id: str
    policy_num: Optional[str] = None

    @abc.abstractmethod
    def policy_information(self):
        pass


class Quote(TypedDict):
    product_id: str


@dataclass
class AutoPolicy(Policy):
    id: str
    owner: str
    vehicle_make: str
    vehicle_model: str
    year: str
    chassis_num: str
    vehicle_reg_num: str
    vehicle_engine_num: str
    vehicle_designated_use: str
    vehicle_type: str
    value: int
    policy_num: Optional[str]

    def policy_information(self):
        client = HeirsLifeAssuranceClient()
        return client.get_policy_details(self.id)


@dataclass
class TravelPolicy(Policy):
    # THe "owner" prefix had been added here for readability
    # In the API, please match these to appropriate keys without the prefixes
    owner_first_name: str
    owner_last_name: str
    owner_other_name: str

    owner_date_of_birth: date
    policy_start_date: date
    policy_end_date: date

    category: str
    country_id: str
    email: str
    address: str

    next_of_kin_name: str
    relation: str
    passport_num: str
    spouse_email: str  # For clarity, this had been renamed. Its reffered to as, partnersEmail in the API
    gender: str
    phone: str
    occupation: str

    policy_id: str
    policy_holder_id: str
    premium: int
    policy_status: str


class CustomerInfo(TypedDict):
    firstName: str
    lastName: str
    dateOfBirth: str
    gender: str
    phone: str
    occupation: str
    email: str
    idCardImgUrl: str
    utilityImgUrl: str
    city: str
    state: str
    address: str
    country: str
    street: str
    streetNumber: str
    postCode: str
    number: str
    expiry: str
    type: str
