import abc


class IClient:
    def __init__(self):
        self.base_url = None
        self.api_key = None
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
