import abc

import requests


class IClient(abc.ABC):
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.api_key = api_key
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

    @abc.abstractmethod
    def get(self, url: str):
        raise NotImplementedError

    @abc.abstractmethod
    def post(self, url: str, data: dict):
        raise NotImplementedError


class BaseClient(IClient):
    def __init__(self, base_url: str, api_key: str):
        super().__init__(base_url, api_key)

    def get(self, url: str):
        response = requests.get(f"{self.base_url}/{url}", headers=self.headers)
        response.raise_for_status()
        return response.json()

    def post(self, url: str, data: dict):
        response = requests.post(
            f"{self.base_url}/{url}", headers=self.headers, json=data
        )
        response.raise_for_status()
        return response.json()
