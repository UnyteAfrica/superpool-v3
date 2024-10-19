import abc
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import List, Literal, Optional, Required, TypeAlias, TypedDict, Union

from api.integrations.heirs.client import HeirsLifeAssuranceClient


class Policy(abc.ABC):
    id: str
    policy_num: Optional[str] = None

    @abc.abstractmethod
    def policy_information(self):
        pass


class QuoteAPIResponse(TypedDict):
    premium: str
    contribution: Optional[str]


class APIErrorResponse(TypedDict, total=False):
    type: str
    title: str
    detail: str
    status: str


class Error(TypedDict):
    type: str
    title: str
    detail: str
    status: int | str


ErrorResponse: TypeAlias = dict[Literal["error"], Error]


class Quote(TypedDict):
    origin_product_id: int
    product_name: str
    premium: Decimal
    additional_information: str
    origin: Optional[str]
    contribution: Optional[Decimal]


QuoteResponse: TypeAlias = list[Quote]


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


class Product(TypedDict):
    productId: str
    productName: str
    imageUrl: Optional[str]
    canBuyByUssd: Optional[bool]
    canRenewByUssd: Optional[bool]


class PolicyInfo(TypedDict):
    policyName: str
    policyStatus: str
    policyNumber: str
    policyStartDate: str
    policyExpiryDate: str
    premium: str
    issueDate: str


class TravelQuoteParams(TypedDict):
    userAge: str
    startDate: str
    endDate: str
    categoryName: str


class MotorQuoteParams(TypedDict):
    productId: str | int
    motorValue: str | int
    motorClass: str
    motorType: str


class BikerQuoteParams(TypedDict):
    productId: str
    motorValue: str
    motorClass: str


class PersonalAccidentQuoteParams(TypedDict):
    productId: str


class DeviceQuoteParams(TypedDict, total=False):
    productId: int
    itemValue: Required[int]


QuoteDefinition = Union[
    TravelQuoteParams,
    PersonalAccidentQuoteParams,
    MotorQuoteParams,
    BikerQuoteParams,
    DeviceQuoteParams,
]


# POLICIES IMPLEMENTATION
class TravelPerson(TypedDict, total=False):
    firstName: str
    lastName: str
    otherName: str
    dateOfBirth: str
    startDate: str
    endDate: str
    categoryName: str
    country_id: str
    email: str
    address: str
    nextOfKinName: str
    relation: str
    passportNo: str
    partnersEmail: str
    gender: str
    phone: str
    occupation: str


class TravelPolicyRequest(TypedDict):
    policyHolderId: str
    items: List[TravelPerson]


class PersonalAccidentPerson(TypedDict, total=False):
    firstName: str
    lastName: str
    otherName: str
    dateOfBirth: str
    startDate: str
    endDate: str
    categoryName: str
    country_id: str
    email: str
    address: str
    nextOfKinName: str
    relation: str
    passportNo: str
    partnersEmail: str
    gender: str
    phone: str
    occupation: str


class MotorParticulars(TypedDict, total=False):
    owner: str
    make: str
    model: str
    year: int
    chassis: str
    registrationNumber: str
    engineNumber: str
    value: int
    use: str  # could be private or commercial
    type: str  # could be saloon, suv, light truck or heavy duty truck


class DeviceParticulars(TypedDict, total=False):
    value: int
    make: str
    model: str
    serialNumber: str
    imei: str
    deviceType: str  # could be Phone, Tablet, Laptop, POS


class DevicePolicyRequest(TypedDict, total=False):
    policyHolderId: str
    items: List[DeviceParticulars]


class PersonalAccidentPolicyRequest(TypedDict):
    policyHolderId: str
    items: List[PersonalAccidentPerson]


class MotorPolicyRequest(TypedDict, total=False):
    policyHolderId: str
    items: List[MotorParticulars]


class BikerPolicyRequest(TypedDict, total=False):
    policyHolderId: str
    items: List[MotorParticulars]


class InsuranceProduct:
    def to_dict(self):
        raise NotImplementedError("Subclasses must implement this method")


class MotorPolicy(InsuranceProduct):
    def __init__(self, policy_details: MotorPolicyRequest) -> None:
        self.policy_details = policy_details

    def to_dict(self):
        return self.policy_details


class BikerPolicy(InsuranceProduct):
    def __init__(self, policy_details: BikerPolicyRequest) -> None:
        self.policy_details = policy_details

    def to_dict(self):
        return self.policy_details


class PersonalAccidentPolicy(InsuranceProduct):
    def __init__(self, policy_details: PersonalAccidentPolicyRequest) -> None:
        self.policy_details = policy_details

    def to_dict(self):
        return self.policy_details


class TravelPolicyClass(InsuranceProduct):
    def __init__(self, policy_details: TravelPolicyRequest) -> None:
        self.policy_details = policy_details

    def to_dict(self):
        return self.policy_details


class DevicePolicy(InsuranceProduct):
    def __init__(self, policy_details: DevicePolicyRequest) -> None:
        self.policy_details = policy_details

    def to_dict(self):
        return self.policy_details
