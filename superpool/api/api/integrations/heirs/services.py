"""
Heirs Assurance Service
"""

import logging
from decimal import Decimal
from typing import Any, Dict, List

import requests
from typing_extensions import deprecated

from api.integrations.heirs.client import HEIRS_SERVER_URL, HeirsLifeAssuranceClient
from api.integrations.heirs.exceptions import HeirsAPIException
from core.providers.integrations.heirs.registry import (
    AutoPolicy,
    BikerPolicy,
    DevicePolicy,
    Error,
    ErrorResponse,
    InsuranceProduct,
    MotorPolicy,
    PersonalAccidentPolicy,
    PolicyInfo,
    Product,
    Quote,
    QuoteResponse,
    TravelPolicyClass,
)

logger = logging.getLogger("api_client")


RECOGNIZED_INSURANCE_CATEGORIES = [
    "Motor",
    "TenantProtect",
    "HomeProtect",
    "BusinessProtect",
    "Personal Accident",
    "Marine Cargo",
    "Device",
    "Travel",
]

INTERNAL_RECOGNIZED_CLASSES = ("Auto", "Travel", "Personal_Accident", "Device", "Home")


class HeirsAssuranceService:
    def __init__(self) -> None:
        self.client = HeirsLifeAssuranceClient()
        logger.info("HeirsAssuranceService initialized.")

    def _is_api_error_response(self, response: Dict[str, Any]) -> bool:
        """
        Determines if the returned response matches the APIErrorResponse structure.

        Returns True if the response is an error response, False otherwise
        """
        return all(key in response for key in ["type", "title", "detail", "status"])

    @deprecated("This method is deprecated. Use `_sanitize_params` instead.")
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

    def _sanitize_params(self, category: str, params: dict) -> dict[str, Any]:
        """
        Sanitize and map input parameters to match the required API parameters.

        Arguments:
            category: The insurance category.
            params: The input parameters provided by the user.

        Returns:
            A dictionary containing only the required parameters with correct keys.
        """
        mappings = {
            "travel": {
                "user_age": "user_age",
                "category_name": "category_name",
                "departure_date": "start_date",
                "return_date": "end_date",
            },
        }
        category_key = category.lower()
        logger.debug(f"Category when sanitizing: {category_key}")
        mapped_params = {}

        # only apply mappings if the category is recognized
        if category_key in mappings:
            for k, v in params.items():
                mapped_key = mappings[category_key].get(k, k)
                mapped_params[mapped_key] = v
        else:
            mapped_params = params

        # then extract and propate the required keys
        required_keys = self._get_required_params(category)
        logger.info(f"Required Keys: {required_keys}")
        sanitized_params = {
            k: mapped_params[k] for k in required_keys if k in mapped_params
        }
        logger.info(f"Sanitized Params: {sanitized_params}")

        # we wnat o ensre all required parameters are present
        missing_keys = [k for k in required_keys if k not in sanitized_params]
        if missing_keys:
            logger.error(f"Missing required keys: {missing_keys}")
            raise ValueError(
                f"Missing required keys: {missing_keys} for category:  {category}"
            )

        # only reeturn if we have all required keys in the sanitized params
        return sanitized_params

    def _get_required_params(self, category: str) -> list[str]:
        """
        Extract the required parameters for a specific category
        """
        logger.debug(f"Getting required params for category: {category}")
        required_params = {
            "auto": ["product_id", "motor_value", "motor_class", "motor_type"],
            "motor": ["product_id", "motor_value", "motor_class", "motor_type"],
            "biker": ["product_id", "motor_value", "motor_class"],
            "travel": ["user_age", "start_date", "end_date", "category_name"],
            "personal_accident": ["product_id"],
            "accident": ["product_id"],
            "device": ["item_value"],
            "pos": ["item_value"],
        }
        result = required_params.get(category.lower(), [])
        logger.info(f"Returning required params for {category}: {result}")
        return result

    def get_quotes(
        self, category: str, params: dict[str, Any]
    ) -> QuoteResponse | ErrorResponse:
        """
        Retrieve an Insurance Quotation from the Heirs API

        Args:
            category (str): Insurance category.
            params (dict[str, Any]): Additional parameters.

        Returns:
            QuoteResponse: List of quotes.
            ErrorResponse: An Error response.
        """
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
            products = self.fetch_insurance_products(category)
            if not products:
                logger.error(f"No products found for category '{category}'")
                return {
                    "error": {
                        "type": "no_products",
                        "title": "No products found for the specified category",
                        "detail": f"No products found for category '{category}'",
                        "status": "404",
                    }
                }

            # collate the quotes
            quotes: QuoteResponse = []
            for product in products:
                quote = self._construct_quote(product, params, category)
                quotes.append(quote)
            return quotes
        except HeirsAPIException as e:
            logger.error(f"Failed to retrieve quote: {e}", exc_info=True)
            logger.error(
                f"Heirs API Error | Type: {e.type} | Title: {e.title} | Detail: {e.detail} | Status: {e.status}"
            )
            return {
                "error": Error(
                    type=e.type, title=e.title, detail=e.detail, status=e.status
                )
            }
        except requests.HTTPError as http_err:
            logger.error(
                f"HTTPError during get_quote | Error: {http_err}", exc_info=True
            )
            return {
                "error": Error(
                    type="http_error",
                    title="HTTP Error when get_quote was called to Heirs",
                    detail=str(http_err),
                    status="HTTP Error",
                )
            }
        except Exception as e:
            logger.error(f"Unexpected Error in get_quote: {e}", exc_info=True)
            return {
                "error": Error(
                    type="unexpected_error",
                    title="An unexpected error occurred when requesting quotes from Heirs",
                    detail=str(e),
                    status="500",
                )
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

    def fetch_insurance_products(self, product_class: str) -> list[dict[str, Any]]:
        """
        Get Insurance products that belongs to a specific product category

        Fetches all subproducts offered under a product class
        """
        company = "Heirs%20Insurance"
        fetch_products_url = (
            f"{HEIRS_SERVER_URL}/{company}/class/{product_class}/product"
        )
        logger.info(f"Fetching products for class '{product_class}'")

        products = self.client.get(fetch_products_url)
        logger.info(f"Fetched {len(products)} products for class '{product_class}'")
        return products

    def fetch_product_info(self, product_id: int) -> dict[str, Any]:
        """
        Fetch detailed product information about a specific product

        Arguments:
            product_id: The ID of the product

        Returns:
            A dictionary containing product information
        """
        company = "Heirs%20Insurance"
        fetch_product_info_url = (
            f"{HEIRS_SERVER_URL}/{company}/product/{product_id}/info"
        )
        response = self.client.get(fetch_product_info_url)
        return response

    def _construct_quote(
        self, product: dict[str, Any], params: dict[str, Any], category: str
    ) -> Quote:
        """
        Construct a Quote hashmap for a single product

        Arguments:
            product: A dictionary containing product information
            params: Additional parameters required for the quote
            category: The category of the product

        Returns:
            A consolidated information in a Quote dictionary
        """
        product_id = product.get("productId")
        product_name = product.get("productName")

        logger.info(
            f"Constructing quote for Product ID: {product_id}, Name: {product_name}"
        )
        product_info = self.fetch_product_info(product_id)
        logger.info(f'Product info for "{product_name}": {product_info}')
        premium = self.fetch_premium(product_id, category, params)

        quote: Quote = {
            "origin_product_id": product_id,
            "product_name": product_name,
            "premium": premium,
            "additional_information": product_info.get("info", ""),
        }
        logger.info(f"Constructed quote: {quote}")
        return quote

    def fetch_premium(self, product_id: int, category: str, params: dict) -> Decimal:
        """
        Fetch the premium for a specific product

        Arguments:
            category: The product category
            product: The product dictionary
            params: Additional parameters required for the quote

        Returns:
            The premium as a Decimal
        """

        sanitized_params = self._sanitize_params(category, params)

        if sanitized_params is None or sanitized_params == {}:
            logger.error("Sanitized params are empty. Cannot fetch premium")
            raise ValueError("Sanitized params are empty. Cannot fetch premium")

        endpoint = self._get_endpoint_by_category(category, sanitized_params)

        logger.info(f'Fetching premium from endpoint "{endpoint}"')
        premium_data = self.client.get(endpoint)

        if self._is_api_error_response(premium_data):
            api_error = premium_data
            raise HeirsAPIException(
                type=api_error.get("type", "unknown_error"),
                title=api_error.get("title", "Unknown Error"),
                detail=api_error.get("detail", "An unknown error occurred."),
                status=str(api_error.get("status", "500")),
            )
        premium = Decimal(str(premium_data.get("premium", 0.0)))
        logger.info(f"Received premium: {premium} for product ID: {product_id}")
        return premium

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

    def _get_endpoint_by_category(self, category: str, params: dict[str, Any]) -> str:
        """
        Contruct the API endpoint based on the category and parameters

        Arguments:
            category: Product category
            params: Additional parameters passed unto the API call

        Returns:
            The API endpoint as a string
        """
        # required_params = {
        #     "auto": ["product_id", "motor_value", "motor_class", "motor_type"],
        #     "motor": ["product_id", "motor_value", "motor_class", "motor_type"],
        #     "biker": ["product_id", "motor_value", "motor_class"],
        #     "travel": ["user_age", "start_date", "end_date", "category_name"],
        #     "personal_accident": ["product_id"],
        #     "accident": ["product_id"],
        #     "device": ["item_value"],
        #     "pos": ["item_value"],
        # }

        category_key = category.lower().replace(" ", "_")
        print(f"Category: {category_key}")
        # if category_key not in required_params:
        #     logger.error(
        #         f"Unsupported category for insurance quote: {category} during API call"
        #     )
        #     raise ValueError("Unsupported category for insurance quote")

        logger.info(f'Preparing to fetch premium for category "{category}"')
        # self._validate_params(required_params[category_key], category, params)

        if category_key in ["auto", "motor"]:
            base_url = f"{HEIRS_SERVER_URL}/motor/quote"
            endpoint = (
                f"{base_url}/"
                f'{params.get("product_id")}/{params.get("motor_value")}/'
                f'{params.get("motor_class")}/{params.get("motor_type")}'
            )
        elif category_key == "biker":
            base_url = f"{HEIRS_SERVER_URL}/biker/quote"
            endpoint = (
                f"{base_url}/"
                f'{params.get("product_id")}/{params.get("motor_value")}/'
                f'{params.get("motor_class")}'
            )
        elif category_key == "travel":
            base_url = f"{HEIRS_SERVER_URL}/travel/quote"
            endpoint = (
                f"{base_url}/"
                f'{params.get("user_age")}/{params.get("start_date")}/'
                f'{params.get("end_date")}/{params.get("category_name")}'
            )
        elif category_key in ["personal_accident", "accident"]:
            base_url = f"{HEIRS_SERVER_URL}/personal-accident/quote"
            endpoint = f'{base_url}/{params.get("product_id")}'
        elif category_key == "device":
            base_url = f"{HEIRS_SERVER_URL}/device/quote"
            endpoint = f'{base_url}/{params.get("item_value")}'
        elif category_key == "pos":
            base_url = f"{HEIRS_SERVER_URL}/pos/quote"
            endpoint = f'{base_url}/{params.get("item_value")}'
        else:
            logger.error(
                f"Unsupported category for insurance quote: {category} during API call"
            )
            raise ValueError("Unsupported category for insurance quote")

        logger.info(f"Constructed endpoint for category '{category}': {endpoint}")
        return endpoint

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
