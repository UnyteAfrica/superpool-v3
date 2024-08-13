from api.claims.services import ClaimService
from core.catalog.models import Policy, Product
from core.claims.models import Claim, ClaimDocument, StatusTimeline
from core.providers.models import Provider
from core.user.models import Customer
from rest_framework import serializers


class ProviderSerializer(serializers.ModelSerializer):
    """Helps us to serialize the Insurer name from the Provider object"""

    class Meta:
        model = Provider
        fields = ["name"]


class ClaimOwnerSerializer(serializers.ModelSerializer):
    """Serializes the metadata about at claim owner"""

    class Meta:
        model = Customer
        fields = ["first_name", "last_name", "dob", "email", "phone_number"]


class ClaimProductSerializer(serializers.ModelSerializer):
    """Serilizes the metadata about the product category a claim belongs to"""

    class Meta:
        model = Product
        fields = [
            "name",
            "product_type",
        ]


class ClaimProviderSerializer(serializers.ModelSerializer):
    provider = ProviderSerializer()

    class Meta:
        # We are using product here, so we can use the product to reference the insurer who offered this package
        model = Product
        fields = ["provider"]


class StatusTimelineSerializer(serializers.ModelSerializer):
    time_stamp = serializers.DateTimeField(
        source="timestamp", format="%Y-%m-%d %H:%M:%S"
    )

    class Meta:
        model = StatusTimeline
        fields = ["status", "time_stamp"]

    def to_representation(self, instance):
        repr = super().to_representation(instance)
        repr["name"] = repr.pop("status")
        # repr["time_stamp"] = repr.pop("timestamp")
        return repr


class ClaimSerializer(serializers.ModelSerializer):
    """
    Serializer for Claim instances.

    This serializer includes fields that are intended to be visible when
    retrieving or listing Claim objects. It provides a human-readable
    representation of the Claim, including status descriptions.
    """

    product = ClaimProductSerializer()
    customer = ClaimOwnerSerializer()
    # insurer = ClaimProviderSerializer()
    insurer = serializers.CharField(source="provider.name")
    claim_amount = serializers.DecimalField(
        source="amount", max_digits=10, decimal_places=2
    )
    claim_reference_number = serializers.CharField(source="claim_number")
    claim_status = serializers.CharField(source="status")
    claim_status_timeline = StatusTimelineSerializer(many=True, read_only=True)

    class Meta:
        model = Claim
        fields = [
            "claim_reference_number",
            "claim_status",
            "claim_date",
            "customer",
            "claim_amount",
            "insurer",
            "product",
            "policy",
            "claim_status_timeline",
        ]
        extra_kwargs = {
            "id": {"read_only": True},
            "claim_reference_number": {"required": False},
        }


class ClaimResponseSerializer(serializers.ModelSerializer):
    """
    V2 Serializer for formating responses when
    """

    claim_id = serializers.UUIDField(source="id")
    claim_status = serializers.CharField(source="status")
    policy_id = serializers.CharField(source="policy.policy_id")
    insurer = serializers.CharField(source="policy.provider.name")

    class Meta:
        model = Claim
        fields = [
            "claim_id",
            "policy_id",
            "claim_status",
            "insurer",
        ]


class ClaimantMetadataSerializer(serializers.Serializer):
    """
    Validates incoming request data for creating a new claim.
    """

    first_name = serializers.CharField()
    last_name = serializers.CharField()
    birth_date = serializers.DateField(input_formats=["%Y-%m-%d"])
    email = serializers.EmailField()
    phone_number = serializers.CharField(required=False)
    relationship = serializers.CharField(
        help_text="The relationship of the claimant to the policyholder"
    )


class AuthorityReportSerializer(serializers.Serializer):
    """
    Specifies the data structure for the Authority Report e.g Police Report
    """

    report_number = serializers.CharField()
    report_date = serializers.DateField(input_formats=["%Y-%m-%d"])
    filing_station = serializers.CharField(required=False)


class WitnessSerializer(serializers.Serializer):
    """
    Specifies the data structure for capturing witness information of a claim

    There can be 0 - n witnesses for a claim
    """

    witness_name = serializers.CharField(
        help_text='Full name of the witness in the format, "First Name Last Name"'
    )
    witness_contact_phone = serializers.CharField()
    witness_contact_email = serializers.EmailField(required=False)
    witness_statement = serializers.CharField(
        help_text="A brief statement from the witness about the incident"
    )


class ClaimDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClaimDocument
        fields = ["document_name", "evidence_type", "document_url", "uploaded_at"]


class ClaimDetailsSerializer(serializers.Serializer):
    """
    Specifies the data structure for capturing claim details
    """

    ACCIDENT = "accident"
    DEATH = "death"
    ILLNESS = "illness"
    THEFT = "theft"
    OTHER = "other"

    CLAIM_TYPES = [
        (ACCIDENT, "Accident"),
        (DEATH, "Death"),
        (ILLNESS, "Illness"),
        (THEFT, "Theft"),
        (OTHER, "Other"),
    ]
    claim_type = serializers.ChoiceField(choices=CLAIM_TYPES)
    incident_description = serializers.CharField(
        required=False, help_text="Detailed account of the event that led to the claim"
    )
    incident_date = serializers.DateField(input_formats=["%Y-%m-%d"])
    claim_amount = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        help_text='Estimated amount of the claim in the format "1000.00"',
    )
    supporting_documents = ClaimDocumentSerializer(
        many=True,
        required=False,
        help_text=(
            'List of supporting documents in the format [{"document_name": "Name of Document", "evidence_type": "Type of Evidence", "blob": "Base64 encoded document"}]'
        ),
    )


class ClaimRequestSerializer(serializers.Serializer):
    """
    Validates incoming request data for creating a new claim.
    """

    claimant_metadata = ClaimantMetadataSerializer()
    claim_details = ClaimDetailsSerializer()
    policy_id = serializers.UUIDField(required=False)
    policy_number = serializers.CharField(required=False)
    witness_details = WitnessSerializer(many=True, required=False)
    authority_report = AuthorityReportSerializer(required=False)

    def validate(self, attrs):
        policy_id = attrs.get("policy_id")
        policy_number = attrs.get("policy_number")

        namespace = {}
        if policy_id:
            namespace["policy_id"] = policy_id
        if policy_number:
            namespace["policy_number"] = policy_number

        if not namespace:
            raise serializers.ValidationError(
                "You must provide either a policy ID or a policy number"
            )
        if policy_id and policy_number:
            raise serializers.ValidationError(
                "You cannot provide both a policy ID and a policy number"
            )
        # check if a policy with the provided ID exists
        if not Policy.objects.filter(**namespace).exists():
            raise serializers.ValidationError("Policy does not exist")

        # enforce that the same policy cannot be claimed twice
        # we may need to add a claim type to this validation, therefore
        # validating the claim type against the policy id
        claim_type = attrs["claim_details"].get("claim_type")
        if Claim.objects.filter(policy=policy_id, claim_type=claim_type).exists():
            raise serializers.ValidationError(
                "A claim of this type has already been submitted for this policy. Please await a status update before submitting another claim."
            )

        return attrs

    def create(self, validated_data):
        ClaimService.submit_claim(validated_data)


class ClaimUpdateSerializer(serializers.Serializer):
    """
    Handles updating of a claim instance

    Excludes read-only fields, like claim ID and claim reference number from being updated
    """

    claimant_metadata = ClaimantMetadataSerializer(required=False)
    claim_details = ClaimDetailsSerializer(required=False)
    witness_details = WitnessSerializer(many=True, required=False)
    authority_report = AuthorityReportSerializer(required=False)

    def validate(self, attrs):
        authority_report = attrs.get("authority_report")
        claimant_metadata = attrs.get("claimant_metadata")
        claim_information = attrs.get("claim_details")
        witness_information = attrs.get("witness_details")

        if not any(
            [
                claimant_metadata,
                claim_information,
                witness_information,
                authority_report,
            ]
        ):
            raise serializers.ValidationError(
                "You must provide at least one field to update. "
                "Updates include: claimant_metadata, claim_details, witness_details, authority_report"
            )

        if authority_report:
            raise serializers.ValidationError(
                "Updating the authority report is not supported yet. \n"
                "Please contact the support team for assistance. \n"
                "Error Code: AUTHORITY_REPORT_UPDATE_NOT_SUPPORTED"
            )

        if witness_information:
            raise serializers.ValidationError(
                "Updating witness information is not supported yet. \n"
                "Please contact the support team for assistance. \n"
                "Error code: WITNESS_INFO_NOT_SUPPORTED."
            )
        if claimant_metadata:
            raise serializers.ValidationError(
                "At the moment, updating the claim's information is not support yet. "
                "We are aware of this, and are working to ensure this is possible for your customer "
                "Please reach out to support team with error code: CLAIMANT_UPDATE_NOT_SUPPORTED"
            )

        return attrs

    def update(self, instance, validated_data):
        # Update claimant information if provided
        claimant_metadata = validated_data.get("claimant_metadata")
        if claimant_metadata:
            for attr, value in claimant_metadata.items():
                setattr(instance.claimant, attr, value)
            instance.claimant.save()

        # Update claim information if provided
        claim_details = validated_data.get("claim_details")
        if claim_details:
            for attr, value in claim_details.items():
                setattr(instance, attr, value)

        # Handle supporting documents update if needed
        supporting_documents = claim_details.get("supporting_documents", [])
        if supporting_documents:
            instance.documents.all().delete()  # Delete old documents
            for document_data in supporting_documents:
                ClaimDocument.objects.create(claim=instance, **document_data)

        # TODO: update witness details if provided
        # TODO: update authority report if provided
        #
        # Handle these later

        instance.save()
        return instance
