from abc import ABC, abstractmethod
from typing import Any, List, Union

from core.claims.models import Claim
from django.db.models import F, Q, QuerySet


class IClaim(ABC):
    @abstractmethod
    def submit_claim(self, data):
        raise NotImplementedError()

    @abstractmethod
    def get_claim(self, claim_number, claim_id):
        raise NotImplementedError()

    @abstractmethod
    def get_claims(self, query_params):
        raise NotImplementedError()

    @abstractmethod
    def update_claim(self, claim_number, data):
        raise NotImplementedError()


class ClaimService(IClaim):
    """
    Service class for managing claims in the Claims Management API

    This class provides methods for tracking and managing claims, including
    creating, updating, and retrieving claim data.
    """

    def get_claims(self, query_params: dict[str, Any]) -> QuerySet:
        """
        Retrieve a list of claim based on query parameters
        """
        queryset = Claim.objects.all()
        return queryset

    def get_claim(
        self, claim_number: Union[str, int], claim_id: Union[str, int, None] = None
    ):
        """
        Retrieve a single claim instance by its unique ID or Claim Reference Number
        """
        id = claim_id if claim_id is not None else None
        return Claim.objects.get(Q(claim_number) | Q(id))

    def submit_claim(self, data: dict[str, Any]):
        """
        Create a new claim with the given data
        """
        claim = Claim.objects.create(**data)
        return claim

    def update_claim(self, claim_number: str | int, data: dict[str, Any]):
        """
        Update an existing claim with the provided data
        """
        claim = self.get_claim(claim_number=claim_number)
        for key, val in data.items():
            setattr(claim, key, val)
        claim.save()
        return claim
