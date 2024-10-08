import logging
from abc import ABC, abstractmethod
from typing import Any, Union

from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.db.models import Q, QuerySet
from django.db.utils import IntegrityError
from django.shortcuts import get_object_or_404
from rest_framework.serializers import ValidationError

from api.notifications.services import PolicyNotificationService
from core.catalog.models import Beneficiary, Policy
from core.claims.models import Claim, ClaimDocument, StatusTimeline
from core.user.models import Customer

logger = logging.getLogger(__name__)


class IClaim(ABC):
    @staticmethod
    @abstractmethod
    def submit_claim(validated_data):
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

    def get_claims(self, query_params: dict[str, Any] = {}) -> QuerySet:
        """
        Retrieve a list of claim based on query parameters
        """
        queryset = Claim.objects.all()

        # If no query parameters are provided, return all claims
        if not query_params:
            return queryset

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
            queryset = queryset.filter(
                Q(product__product_type__icontains=query_params["claim_type"])
            )
        if "offer_amount" in query_params:
            queryset = queryset.filter(claim_amount=query_params["offer_amount"])

        if "insurer" in query_params:
            queryset = queryset.filter(
                Q(provider__name__icontains=query_params["insurer"])
                | Q(product__provider__name__icontains=query_params["insurer"])
            )

        return queryset

    def get_claim(
        self,
        claim_number: Union[str, int, None] = None,
        claim_id: Union[str, int, None] = None,
    ):
        """
        Retrieve a single claim instance by its unique ID or Claim Reference Number
        """
        id = claim_id if claim_id is not None else None
        if claim_id:
            return Claim.objects.get(id=id)
        if claim_number:
            return Claim.objects.get(claim_number=claim_number)

    @staticmethod
    def submit_claim(validated_data):
        """
        Ensures that a claim is created with the given data while ensuring data integrity
        """
        try:
            claim = ClaimService._create_claim(validated_data)
        except IntegrityError as exc:
            if "duplicate key value violates unique constraint" in str(exc):
                raise ValidationError(
                    "A customer with the provided email already exists. Please use a different email address."
                )
            # handle other integrity errors
            raise ValidationError(
                f"An error occurred while processing the claim. Please try again later. Error: {exc}"
            ) from exc
        except Exception as exc:
            raise ValidationError(
                f"An error occurred while processing the claim. Please try again later. Error: {exc}"
            ) from exc
        return claim

    @staticmethod
    def validate_claimant(policy: Policy, claimant_metadata: dict) -> Union[str, None]:
        """
        Validates the claimant against the policyholder or beneficiaries.
        The claimant must be either the policyholder or a beneficiary (for Life/Health insurance).
        """

        policy_holder = policy.policy_holder
        policy_type = policy.product.product_type

        policy_holder_birth_date = policy_holder.dob

        if policy_holder.email == claimant_metadata.get(
            "email"
        ) and policy_holder_birth_date == claimant_metadata.get("birth_date"):
            return "policyholder"

        # additionally, check to see if `policy_type` of the policy to be claimed is either
        # health or life insurance, that way, a beneficiary can also claim the policy
        if policy_type in ("Life", "Health"):
            for beneficiary in policy.beneficiaries.all():
                if beneficiary.email == policy_holder.email:
                    return "beneficiary"

        # no matches? okay return None
        return None

    @staticmethod
    def _check_claimant_role(policy, claimant_metadata):
        """
        Check if the claimant is either the policy holder or a valid beneficiary
        """

        claimant_role = ClaimService.validate_claimant(policy, claimant_metadata)

        match claimant_role:
            case "policyholder":
                return claimant_role
            case "beneficiary":
                return claimant_role
            case _:
                # base condition
                return ValidationError(
                    "Claimant is neither the policyholder nor a valid beneficiary for this policy."
                )

    @staticmethod
    @transaction.atomic
    def _create_claim(validated_data):
        """
        Create a new claim with the given data
        """
        claimant_metadata = validated_data.pop("claimant_metadata")
        claim_details = validated_data.pop("claim_details")
        witness_information = validated_data.pop("witness_details", [])
        authority_report = validated_data.pop("authority_report", None)

        # retrieve relatrd objects needed for claim processng
        # e.g. policy, product, provider, customer
        policy_id = validated_data.get("policy_id")

        # policy = Policy.objects.get(id=policy_id)
        # customer = Customer.objects.get(id=claimant_metadata.get("customer_id"))
        policy = get_object_or_404(Policy, policy_id=policy_id)

        # check if the claimant is valid (either a policyholder or a beneficiary to a policy
        claimant_role = ClaimService._check_claimant_role(policy, claimant_metadata)

        if claimant_role == "policyholder":
            claimant = policy.policy_holder
            claimant_type = "customer"
            claimant_content_type = ContentType.objects.get_for_model(Customer)
        else:
            # retrieve the beneficiary who is making the claim
            claimant_birth_date = claimant_metadata.get("birth_date")

            if claimant_birth_date:
                claimant = policy.beneficiaries.get(
                    email=claimant_metadata.get("email"),
                    date_of_birth=claimant_birth_date,
                )
                claimant_content_type = ContentType.objects.get_for_model(Beneficiary)
                claimant_type = "beneficiary"
            else:
                claimant = policy.beneficiaries.get(
                    email=claimant_metadata.get("email")
                )
                claimant_content_type = ContentType.objects.get_for_model(Beneficiary)
                claimant_type = "beneficiary"

        product = policy.product
        provider = product.provider

        claim = Claim.objects.create(
            incident_date=claim_details["incident_date"],
            amount=claim_details.get("claim_amount", 0.0),
            estimated_loss=claim_details.get("claim_amount", 0.0),
            policy=policy,
            claimant_type=claimant_type,
            claimant_content_type=claimant_content_type,
            claimant_object_id=claimant.id,
            provider=provider,
            product=product,
            status="pending",
        )

        ClaimService._create_claim_documents(
            claim, claim_details.get("supporting_documents", [])
        )
        ClaimService._handle_witnesses_and_report(
            claim, witness_information, authority_report
        )

        StatusTimeline.objects.create(claim=claim, status="pending")

        # we want to use this transaction date when notifying the merchant
        transaction_date = claim.created_at.strftime("%Y-%m-%d %H:%M:%S")
        customer = {
            "first_name": claimant.first_name,
            "last_name": claimant.last_name,
            "customer_email": claimant.email,
        }
        PolicyNotificationService.notify_merchant(
            action="claim_policy",
            policy=policy,
            customer=customer,
            transaction_date=transaction_date,
        )
        return claim

    @staticmethod
    def _create_claim_documents(claim, documents):
        """
        Associate claim documents with the claim
        """
        try:
            ClaimDocument.objects.bulk_create(
                [
                    ClaimDocument(
                        claim=claim,
                        evidence_type=doc.get("evidence_type"),
                        document_name=doc.get("document_name"),
                        document_url=doc.get("document_url"),
                        uploaded_at=doc.get("uploaded_at"),
                    )
                    for doc in documents
                ]
            )
        except Exception as exc:
            raise ValidationError(
                "An error occurred while creating the claim documents"
            ) from exc

    @staticmethod
    def _handle_witnesses_and_report(claim, witnesses, report):
        """
        Attempts to create witnesses and authority report for the claim, with graceful error handling

        NO ONE HERE IS A WIZARD COOK!
        """
        try:
            ClaimService._create_witnesses(claim, witnesses)
        except NotImplementedError as feature_exc:
            logger.error(
                f"Feature not implemented: {feature_exc}",
                exc_info=True,
            )

        # handle authority report creation
        try:
            ClaimService._create_authority_report(claim, report)
        except NotImplementedError as feature_exc:
            logger.error(
                f"Feature not implemented: {feature_exc}",
                exc_info=True,
            )

    @staticmethod
    def _create_witnesses(claim, witnesses):
        """
        Create witnesses for the claim
        """
        if witnesses:
            # TODO: Implement this at a later date
            raise NotImplementedError

    @staticmethod
    def _create_authority_report(claim, report):
        """
        Create an authority report for the claim
        """
        if report:
            # TODO: Implement this at a later date
            raise NotImplementedError

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
