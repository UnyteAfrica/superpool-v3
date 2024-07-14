import json
import uuid
from typing import List, TypedDict, Union

from api.integrations.heirs.client import HeirsLifeAssuranceClient
from core.providers.integrations.heirs.registry import (APIErrorResponse,
                                                        AutoPolicy,
                                                        CustomerInfo, Policy,
                                                        PolicyInfo, Product,
                                                        QuoteAPIResponse)
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

    def get_quote(
        self, category: str = None, **params: dict
    ) -> Union[QuoteAPIResponse, APIErrorResponse]
        """
        Retrieve an Insurance Quotation from the Heirs API

        Arguments:
            category Product category
            params Additional parameters passed unto the API call
        """
        RECOGNIZED_INSURANCE_CATEGORIES = (
            "auto",
            "travel",
            "biker",
            "personal_accident",
        )
        if not category:
            raise Exception(
                "Policy category must be provided in order to retrieve quotes"
            )
        if category not in RECOGNIZED_INSURANCE_CATEGORIES:
            return Exception(
                "Product category must be one of auto, travel, biker or personal accident categories."
            )
        endpoint = self._get_endpoint_by_category(category, params)
        return self.client.get(endpoint)

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

    def product_queryset(self, product_class: str) -> List[Product]:
        """
        Get Insurance products that belongs to a product class

        Fetches all subproducts offered under a product class

        A product class, can also be reffered, as the product category
        """
        company = "Heirs%20Insurance"
        fetch_products_url = f"{settings.HEIRS_ASSURANCE_STAGING_URL}/{company}/class/{product_class}/product"
        response = self.client.get(fetch_products_url)
        return response

    def get_policy_details(self, policy_num: str) -> PolicyInfo:
        """
        Retrieves information about a Policy from the Heirs API

        Args:
            policyNumber string unique reference used to identify a policy
        """
        company = "Heirs%20Insurance"
        fetch_policy_info_url = (
            f"{settings.HEIRS_ASSURANCE_STAGING_URL}/{company}/policy/{policy_num}"
        )
        response = self.client.get(fetch_policy_info_url)
        return response

    def _get_endpoint_by_category(self, category: str, params: dict) -> str:
        """
        Contruct the API endpoint based on the category and parameters

        Arguments:
            category: Product category
            params: Additional parameters passed unto the API call

        """
        match category:
            case "auto" | "motor" | "biker":
                return f'{settings.HEIRS_ASSURANCE_STAGING_URL}/motor/quote/{params.get('product_id')}/{params.get('motor_value')}/{params.get('motor_class')}/{params.get('motor_type')}'
            case "travel":
                return f'{settings.HEIRS_ASSURANCE_STAGING_URL}/travel/quote/{params.get('user_age')}/{params.get('start_date')}/{params.get('end_date')}/{params.get('category_name')}'
            case "personal_accident":
                return f'{settings.HEIRS_ASSURANCE_STAGING_URL}/personal-accident/quote/{params.get('product_id')}'
            case _:
                return "Unsupported category"
