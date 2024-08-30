from api.claims.services import ClaimService
from core.catalog.models import Policy, Product
from core.claims.models import Claim, ClaimDocument, ClaimWitness, StatusTimeline
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
    claim_id = serializers.UUIDField(source="id", read_only=True)
    claim_reference_number = serializers.CharField(source="claim_number")
    claim_status = serializers.CharField(source="status")
    claim_status_timeline = StatusTimelineSerializer(many=True, read_only=True)

    class Meta:
        model = Claim
        fields = [
            "claim_id",
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
        help_text="The relationship of the claimant to the policyholder",
        required=False,
    )


class AuthorityReportSerializer(serializers.Serializer):
    """
    Specifies the data structure for the Authority Report e.g Police Report
    """

    report_number = serializers.CharField()
    report_date = serializers.DateField(input_formats=["%Y-%m-%d"])
    filing_station = serializers.CharField(required=False)


class WitnessSerializer(serializers.ModelSerializer):
    """
    Specifies the data structure for capturing witness information of a claim

    There can be 0 - n witnesses for a claim
    """

    witness_name = serializers.CharField(
        source="full_name",
        help_text='Full name of the witness in the format, "First Name Last Name"',
    )
    witness_contact_phone = serializers.CharField(
        required=False, source="contact_phone"
    )
    witness_contact_email = serializers.EmailField(
        required=False, source="contact_email"
    )
    witness_statement = serializers.CharField(
        help_text="A brief statement from the witness about the incident",
        source="statement",
    )

    class Meta:
        model = ClaimWitness
        fields = [
            "witness_name",
            "witness_contact_phone",
            "witness_contact_email",
            "witness_statement",
        ]


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
    BASIC = "basic"
    PREMIUM = "premium"
    ADVANCED = "advanced"

    CLAIM_TYPES = [
        (BASIC, "Basic"),
        (PREMIUM, "Premium"),
        (ADVANCED, "Advanced"),
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

    We are only allowing updates to the following fields:
    - Customer information - age, email, phone number
    - Claim details - incident date, incident description
    - Witness information - name, contact phone, contact email, statement

    Fields you cannot update:
    - Claim ID
    - First Name and Surname of the claimant - you would have to reach out to support team with your verifying documents
    - Claim number provided by the merchant
    - Authority report - report number, report date, filing station - For now not supported
    - Supporting documents for a claim (Claim details) - For now not supported
    - Claim amount
    """

    claimant_metadata = ClaimantMetadataSerializer(required=False)
    claim_details = ClaimDetailsSerializer(required=False)
    witness_details = WitnessSerializer(many=True, required=False)
    authority_report = AuthorityReportSerializer(required=False)

    def validate(self, attrs):
        authority_report = attrs.get("authority_report")
        claimant_metadata = attrs.get("claimant_metadata")
        claim_details = attrs.get("claim_details")
        witness_details = attrs.get("witness_details")

        # Ensure at least one updatable field is provided
        # if not (
        #     claimant_metadata or claim_details or witness_details or authority_report
        # ):
        if not any(
            field in attrs
            for field in ["claimant_metadata", "claim_details", "witness_details"]
        ):
            raise serializers.ValidationError(
                {
                    "detail": "You must provide at least one field to update. "
                    "Options include claimant_metadata, claim_details, or witness_details."
                }
            )

        # Restrict authority report updates
        if authority_report:
            raise serializers.ValidationError(
                {
                    "authority_report": "Updating authority reports is not supported yet. "
                    "Please contact the support team for assistance. "
                    "Error Code: AUTHORITY_REPORT_UPDATE_NOT_SUPPORTED"
                }
            )

        # Restrict updates to claim number, claim amount, and supporting documents
        if claim_details:
            if "claim_number" in claim_details:
                raise serializers.ValidationError(
                    {"claim_details": "Claim number cannot be updated."}
                )
            if "claim_amount" in claim_details:
                raise serializers.ValidationError(
                    {"claim_details": "Claim amount cannot be updated."}
                )
            if "supporting_documents" in claim_details:
                raise serializers.ValidationError(
                    {"claim_details": "Supporting documents cannot be updated."}
                )

        # Restrict witness updates
        if witness_details:
            for witness in witness_details:
                if "name" not in witness:
                    raise serializers.ValidationError(
                        {"witness_details": "Each witness must have a name."}
                    )
            raise serializers.ValidationError(
                {
                    "witness_details": "Updating witness information is not supported yet. "
                    "Please contact the support team for assistance. "
                    "Error Code: WITNESS_INFO_NOT_SUPPORTED"
                }
            )

        return attrs

    def update(self, instance, validated_data):
        """
        Update the claim instance with the provided validated data
        """

        claimant_metadata = validated_data.get("claimant_metadata")
        if claimant_metadata:
            claimant = instance.customer
            # Only allow updates to email, phone_number, and age
            allowed_fields = ["email", "phone_number", "age"]
            for field in allowed_fields:
                if field in claimant_metadata:
                    setattr(claimant, field, claimant_metadata[field])
            claimant.save()

        # for claim details
        claim_details = validated_data.get("claim_details")
        if claim_details:
            # Only allow updates to incident_date and incident_description
            allowed_fields = ["incident_date", "incident_description"]
            for field in allowed_fields:
                if field in claim_details:
                    setattr(instance, field, claim_details[field])

        # for witness details
        witness_details = validated_data.get("witness_details")
        if witness_details:
            # remove all existing witnesses of this claim
            instance.witnesses.all().delete()
            for witness_data in witness_details:
                ClaimWitness.objects.create(claim=instance, **witness_data)

        # for supporting documents in future
        supporting_documents = (
            claim_details.get("supporting_documents", []) if claim_details else []
        )

        if supporting_documents:
            instance.documents.all().delete()  # Delete existing documents
            for document_data in supporting_documents:
                ClaimDocument.objects.create(claim=instance, **document_data)

        instance.save()
        return instance
