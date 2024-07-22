from abc import ABC, abstractmethod
from typing import Any, List, Union

from core.claims.models import Claim
from django.db import transaction
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

        # TODO: REFACTOR OUT INTO A CUSTOM FILTER
        # A CUSTOM REST FRAMEWORK OR DJANGO FILTER SUBCLASS
        #
        # T FOR THANKS!
        if "claim_status" in query_params:
            queryset = queryset.filter(status=query_params["claim_status"])
        if "customer_id" in query_params:
            queryset = queryset.filter(customer__id=query_params["customer_id"])
        if "customer_email" in query_params:
            queryset = queryset.filter(customer__email=query_params["customer_email"])
        if "first_name" in query_params:
            queryset = queryset.filter(
                customer__first_name__icontains=query_params["first_name"]
            )
        if "last_name" in query_params:
            queryset = queryset.filter(
                customer__last_name__icontains=query_params["last_name"]
            )
        if "phone_number" in query_params:
            queryset = queryset.filter(
                customer__phone_number=query_params["phone_number"]
            )
        if "claim_type" in query_params:
            queryset = queryset.filter(claim_type=query_params["claim_type"])
        if "claim_owner" in query_params:
            queryset = queryset.filter(
                claim_owner__icontains=query_params["claim_owner"]
            )
        if "offer_amount" in query_params:
            queryset = queryset.filter(claim_amount=query_params["offer_amount"])

        return queryset

    def get_claim(
        self, claim_number: Union[str, int], claim_id: Union[str, int, None] = None
    ):
        """
        Retrieve a single claim instance by its unique ID or Claim Reference Number
        """
        id = claim_id if claim_id is not None else None
        return Claim.objects.get(Q(claim_number) | Q(id))

    @transaction.atomic
    def submit_claim(self, data: dict[str, Any]):
        """
        Create a new claim with the given data
        """
        claim = Claim.objects.create(**data)
        return claim

    @transaction.atomic
    def update_claim(self, claim_number: str | int, data: dict[str, Any]):
        """
        Update an existing claim with the provided data
        """
        claim = self.get_claim(claim_number=claim_number)
        for key, val in data.items():
            setattr(claim, key, val)
        claim.save()
        return claim
