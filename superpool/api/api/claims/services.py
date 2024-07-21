from abc import ABC, abstractmethod
from typing import Any


class IClaim(ABC):
    @abstractmethod
    def submit_claim(self, data): ...

    @abstractmethod
    def get_claim(self, claim_number): ...

    @abstractmethod
    def get_claims(self, query_params): ...

    @abstractmethod
    def update_claim(self, claim_number, data): ...


class ClaimService(IClaim):
    """
    Service class for managing claims in the Claims Management API

    This class provides methods for tracking and managing claims, including
    creating, updating, and retrieving claim data.

    It encapsulates the domain logic associated with claim management.
    """

    def get_claims(self, query_params: dict[str, Any]):
        """
        Retrieve a list of claim based on query parameters
        """
        pass

    def get_claim(self, claim_number: str | int):
        """
        Retrieve a single claim instance by its unique ID or Claim Reference Number
        """
        pass

    def submit_claim(self, data: dict[str, Any]):
        """
        Create a new claim with the given data
        """
        pass

    def update_claim(self, claim_number: str | int, data: dict[str, Any]):
        """
        Update an existing claim with the provided data
        """
        pass
