import abc
import logging
from typing import Optional

import requests
from typing_extensions import deprecated

logger = logging.getLogger("api_client")


class IClient(abc.ABC):
    def __init__(self, base_url: str, api_key: str, headers: dict = {}):
        self.base_url = base_url
        self.api_key = api_key
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if additional_headers := headers:
            self.headers.update(additional_headers)

    @abc.abstractmethod
    def get(self, url: str, params: Optional[dict]):
        raise NotImplementedError

    @abc.abstractmethod
    def post(self, url: str, data: dict):
        raise NotImplementedError


class BaseClient(IClient):
    def __init__(self, base_url: str, api_key: str, headers: dict):
        super().__init__(base_url, api_key=api_key, headers=headers)
        logger.info(f"Initialized BaseClient with base_url: {self.base_url}")
        logger.info(f"BaseClient initialized with headers: {self.headers}.")

    @deprecated("Deprecated in favor of get method")
    def getter(self, url: str, params: Optional[dict] = None):
        full_url = f'{url.lstrip("/")}'
        logger.info(f"GET Request | URL: {full_url} | Params: {params}")

        response = requests.get(full_url, headers=self.headers)
        response.raise_for_status()
        response_data = response.json()
        logger.info(
            f"GET Response | Status: {response.status_code} | Response: {response_data}"
        )
        return response_data

    def get(self, url: str, params: Optional[dict] = None):
        full_url = f'{url.lstrip("/")}'
        logger.info(f"GET Request | URL: {full_url} | Params: {params}")

        try:
            response = requests.get(full_url, headers=self.headers, params=params)
            response.raise_for_status()
            response_data = response.json()
            logger.info(
                f"GET Response | Status: {response.status_code} | Response: {response_data}"
            )
            return response_data
        except requests.RequestException as http_err:
            logger.error(
                f"GET Request Failed | URL: {full_url} | Params: {params} | Error: {e}",
                exc_info=True,
            )
            raise http_err

    def post(self, url: str, data: dict):
        full_url = f'{url.lstrip("/")}'
        logger.info(f"POST Request | URL: {full_url} | Data: {data}")

        try:
            response = requests.post(
                full_url, headers=self.headers, json=data, timeout=15
            )
            response.raise_for_status()
            response_data = response.json()
            logger.info(
                f"POST Response | Status: {response.status_code} | Response: {response_data}"
            )
            return response_data
        except requests.RequestException as http_err:
            logger.error(
                f"POST Request Failed | URL: {full_url} | Data: {data} | Error: {e}",
                exc_info=True,
            )
            raise http_err
