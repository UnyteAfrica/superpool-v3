import abc
from dataclasses import dataclass
from typing import Optional, TypedDict


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
    policy_num: Optional[str]
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
