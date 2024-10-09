"""
Heirs Assurance Service
"""

import logging
from typing import Any, Dict, List, Optional, Union

import requests
from typing_extensions import deprecated

from api.integrations.heirs.client import HEIRS_SERVER_URL, HeirsLifeAssuranceClient
from api.integrations.heirs.exceptions import HeirsAPIException
from core.providers.integrations.heirs.registry import (
    APIErrorResponse,
    AutoPolicy,
    BikerPolicy,
    DevicePolicy,
    InsuranceProduct,
    MotorPolicy,
    PersonalAccidentPolicy,
    PolicyInfo,
    Product,
    TravelPolicyClass,
)

# logger = logging.getLogger(__name__)
logger = logging.getLogger("api_client")


class HeirsAssuranceService:
    def __init__(self) -> None:
        self.client = HeirsLifeAssuranceClient()
        logger.info("HeirsAssuranceService initialized.")

    @deprecated(
        "This method is deprecated and will be removed in future versions. Use the appropriate method for the specific policy type"
    )
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

    def _is_api_error_response(self, response: Dict[str, Any]) -> bool:
        """
        Determines if the returned response matches the APIErrorResponse structure.

        Returns True if the response is an error response, False otherwise
        """
        return all(key in response for key in ["type", "title", "detail", "status"])

    def _validate_params(
        self, required_params: list, category: str, params: dict
    ) -> None:
        """
        Validates that the required parameters are present in the params dictionary
        """
        missing_params = [
            param
            for param in required_params
            if param not in params or params.get(param) is None
        ]
        if missing_params:
            logger.error(
                f"Missing required parameters {missing_params} for category {category}"
            )
            raise ValueError(
                f"Missing required parameters for category '{category}': {missing_params}"
            )

    def get_quote(
        self, category: Optional[str] = None, **params: dict
    ) -> Union[Dict[str, Any], Dict[str, Any]]:
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
            "device",
            "pos",
        )
        if not category:
            logger.error("get_quote called without a category")
            raise ValueError(
                "Policy category must be provided in order to retrieve quotes"
            )
        if category not in RECOGNIZED_INSURANCE_CATEGORIES:
            logger.error(f"Unsupported category received: {category}")
            raise ValueError(
                f"Product category must be one of {RECOGNIZED_INSURANCE_CATEGORIES} categories."
            )

        try:
            endpoint = self._get_endpoint_by_category(category, **params)
            logger.info(f"Constructed endpoint for category '{category}': {endpoint}")
            response = self.client.get(endpoint)
            logger.info(f"Received response for category '{category}': {response}")

            if self._is_api_error_response(response):
                api_error = APIErrorResponse(response)
                # return HeirsAPIException(api_error)
                raise HeirsAPIException(
                    type=api_error.get("type"),
                    title=api_error.get("title"),
                    detail=api_error.get("detail"),
                    status=api_error.get("status"),
                )

            return response
        except HeirsAPIException as e:
            logger.error(f"Failed to retrieve quote: {e}", exc_info=True)
            logger.error(
                f"Heirs API Error | Type: {e.type} | Title: {e.title} | Detail: {e.detail} | Status: {e.status}"
            )
            return {
                "error": {
                    "type": e.type,
                    "title": e.title,
                    "detail": e.detail,
                    "status": e.status,
                }
            }
        except requests.HTTPError as http_err:
            logger.error(
                f"HTTPError during get_quote | Error: {http_err}", exc_info=True
            )
            return {
                "error": {
                    "type": "http_error",
                    "title": "HTTP Error when get_quote was called to Heirs",
                    "detail": str(http_err),
                    "status": "HTTP Error",
                }
            }
        except Exception as e:
            logger.error(f"Unexpected Error in get_quote: {e}", exc_info=True)
            return {
                "error": {
                    "type": "unexpected_error",
                    "title": "An unexpected error occurred when requesting quotes from Heirs",
                    "detail": str(e),
                    "status": "500",
                }
            }

    def register_policy(self, product_id: str | int, product_class: InsuranceProduct):
        """
        Register a policy given its product ID and the product class on Heirs API

        Arguments:
            product_id: The ID of the product to register
            product_class: An instance of an InsuranceProduct subclass containing policy details passed to the request body

        Returns:
            APIResponse or APIErrorResponse
        """
        endpoint = self._get_policy_endpoint(product_id, product_class)
        return self.client.post(endpoint, data=product_class.to_dict())

    def register_policy_holder(self, beneficiary_data: dict):
        """
        Register a customer as a policy holder on Heirs platform
        """
        register_policy_holder_url = f"{HEIRS_SERVER_URL}/policy_holder"

        if hasattr(beneficiary_data, "to_dict"):
            beneficiary_dict = beneficiary_data
        elif not isinstance(beneficiary_data, dict):
            beneficiary_dict = beneficiary_data
        else:
            raise TypeError("Policy holder object must be of type dict")

        response = self.client.post(
            url=register_policy_holder_url, data=beneficiary_dict
        )
        return response

    def fetch_all_products(self) -> List[Product]:
        """
        Fetch all products offered by Heirs Insurance
        """
        company = "Heirs%20Insurance"
        fetch_products_url = f"{HEIRS_SERVER_URL}/{company}/product"
        response = self.client.get(fetch_products_url)
        if response.status_code == 200:
            products_data = response.json()
            return [Product(**product) for product in products_data]
        else:
            logger.error(
                f"Failed to fetch products from Heirs API. Status Code: {response.status_code}"
            )
            return []

    def fetch_insurance_products(self, product_class: str) -> list[Product]:
        """
        Get Insurance products that belongs to a specific product category

        Fetches all subproducts offered under a product class
        """
        company = "Heirs%20Insurance"
        fetch_products_url = (
            f"{HEIRS_SERVER_URL}/{company}/class/{product_class}/product"
        )
        response = self.client.get(fetch_products_url)
        return response

    def get_product_info(self, product_id: str | int):
        """
        Retrieve information about a specific product from the Heirs API
        """
        company = "Heirs%20Insurance"
        fetch_product_info_url = (
            f"{HEIRS_SERVER_URL}/{company}/product/{product_id}/info"
        )
        response = self.client.get(fetch_product_info_url)
        return response

    def get_policy_details(self, policy_num: str) -> PolicyInfo:
        """
        Retrieves information about a Policy from the Heirs API

        Args:
            policyNumber string unique reference used to identify a policy
        """
        company = "Heirs%20Insurance"
        fetch_policy_info_url = f"{HEIRS_SERVER_URL}/{company}/policy/{policy_num}"
        response = self.client.get(fetch_policy_info_url)

        if response.status_code == 200:
            policy_data = response.json()
            return PolicyInfo(**policy_data)
        else:
            logger.error(
                f"Failed to fetch products from Heirs API. Status Code: {response.status_code}"
            )

    def _get_endpoint_by_category(self, category: str, params: Any) -> str:
        """
        Contruct the API endpoint based on the category and parameters

        Arguments:
            category: Product category
            params: Additional parameters passed unto the API call

        """
        required_params = {
            "auto": ["product_id", "motor_value", "motor_class", "motor_type"],
            "biker": ["product_id", "motor_value", "motor_class"],
            "travel": ["user_age", "start_date", "end_date", "category_name"],
            "personal_accident": ["product_id"],
            "device": ["item_value"],
            "pos": ["item_value"],
        }
        # if category in required_params:
        #     for param in required_params[category]:
        #         if param not in params:
        #             raise ValueError(f"Missing required parameter: {param}")
        match category:
            case "auto" | "motor":
                self._validate_params(required_params["auto"], category, params)
                return f'{HEIRS_SERVER_URL}/motor/quote/{params.get("product_id")}/{params.get("motor_value")}/{params.get("motor_class")}/{params.get("motor_type")}'
            case "biker":
                self._validate_params(required_params["biker"], category, params)
                return f'{HEIRS_SERVER_URL}/biker/quote/{params.get("product_id")}/{params.get("motor_value")}/{params.get("motor_class")}'
            case "travel":
                self._validate_params(required_params["travel"], category, params)
                return f'{HEIRS_SERVER_URL}/travel/quote/{params.get("user_age")}/{params.get("start_date")}/{params.get("end_date")}/{params.get("category_name")}'
            case "personal_accident" | "accident":
                self._validate_params(
                    required_params["personal_accident"], category, params
                )
                return f'{HEIRS_SERVER_URL}/personal-accident/quote/{params.get("product_id")}'
            case "device":
                self._validate_params(required_params["device"], category, params)
                return f'{HEIRS_SERVER_URL}/device/quote/{params.get("item_value")}'
            case "pos":
                self._validate_params(required_params["pos"], category, params)
                return f'{HEIRS_SERVER_URL}/pos/quote/{params.get("item_value")}'
            case _:
                logger.error(
                    f"Unsupported category for insurance quote: {category} during API call"
                )
                raise ValueError("Unsupported category for insurance quote")

    def _get_policy_endpoint(
        self, product_id: str | int, product_class: InsuranceProduct
    ) -> str:
        """
        Construct a string representation of the API endpoint for the specific policy based
        on the provided Product Class and Policy ID
        """
        if isinstance(product_class, MotorPolicy) or isinstance(
            product_class, AutoPolicy
        ):
            return f"{HEIRS_SERVER_URL}/motor/{product_id}/policy"
        elif isinstance(product_class, BikerPolicy):
            return f"{HEIRS_SERVER_URL}/biker/{product_id}/policy"
        elif isinstance(product_class, TravelPolicyClass):
            return f"{HEIRS_SERVER_URL}/travel/{product_id}/policy"
        elif isinstance(product_class, PersonalAccidentPolicy):
            return f"{HEIRS_SERVER_URL}/personal-accident/{product_id}/policy"
        elif isinstance(product_class, DevicePolicy):
            return f"{HEIRS_SERVER_URL}/device/policy"
        else:
            return "Unsupported Policy/Product Class"
