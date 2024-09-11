from datetime import timezone
from typing import Union
from decimal import Decimal
from django.db import transaction

from api.serializers import LimitedScopeSerializer
from core.claims.models import Claim
from core.catalog.models import Policy
from core.merchants.models import Merchant
from core.user.models import Customer
from rest_framework import serializers
from rest_framework.exceptions import ValidationError


class MerchantSerializer(serializers.ModelSerializer):
    """
    Serializer for Merchant model
    """

    class Meta:
        model = Merchant
        exclude = [
            "token",
            "token_expires_at",
            "verified",
        ]

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        # dates to format
        dates_to_format = ["created_at", "updated_at", "restored_at", "trashed_at"]

        for field_date in dates_to_format:
            # access the actual date from the instance
            date_value = getattr(instance, field_date, None)
            # format date if its not null
            formatted_date = (
                date_value.strftime("%Y-%m-%d %H:%M:%S") if date_value else None
            )
            representation[field_date] = formatted_date
        return representation


class MerchantSerializerV2(serializers.ModelSerializer):
    """
    Serializer for Merchant model
    """

    class Meta:
        model = Merchant
        exclude = ["id", "token", "token_expires_at"]

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        # dates to format
        dates_to_format = ["created_at", "updated_at", "restored_at", "trashed_at"]

        for field_date in dates_to_format:
            # access the actual date from the instance
            date_value = getattr(instance, field_date, None)
            # format date if its not null
            formatted_date = (
                date_value.strftime("%Y-%m-%d %H:%M:%S") if date_value else None
            )
            representation[field_date] = formatted_date
        return representation


class MerchantLimitedSerializer(LimitedScopeSerializer):
    """
    Serializer to display Merchant model with limited fields
    """

    model_class = Merchant
    fields = [
        "id",
        "name",
        "short_code",
        "business_email",
        "is_active",  # noqa: E231
        "support_email",
        "created_at",
    ]


class CreateMerchantSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a Merchant
    """

    class Meta:
        model = Merchant
        fields = (
            "name",
            "business_email",
            "support_email",
        )
        extra_kwargs = {
            "name": {"required": True},
            "business_email": {"required": True},
            "support_email": {"required": False},
        }

    def get_short_code(self, obj):
        return self.Meta.model.generate_short_code()


class MerchantWriteSerializerV2(serializers.ModelSerializer):
    """
    Handles the creation of new Merchants
    """

    company_name = serializers.CharField(source="name")

    class Meta:
        model = Merchant
        fields = ("company_name", "business_email", "support_email", "short_code")
        extra_kwargs = {
            "company_name": {"required": True},
            "business_email": {"required": True},
            "support_email": {"required": False},
            "short_code": {"read_only": True},
        }

    def validate_business_email(self, value: str) -> Union[str, ValidationError]:
        """
        Check that the business email is unique
        """
        if Merchant.objects.filter(business_email=value).exists():
            raise ValidationError("A merchant with this business email already exists.")
        return value


class MerchantUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating core information of a Merchant.

    This serializer handles the validation and serialization of the data
    required to update the core details of a Merchant. It is used in
    the API endpoint that allows customer support to update merchant
    information.

    Supported Fields:
        - name: Business name of the merchant.
        - business_email: Email address used for business communications.
        - support_email: Contact email address for support inquiries.
        - tax_identification_number: Unique tax identification number issued by tax authorities.
        - registration_number: Government-issued registration number with the corporate affairs commission.
        - address: Physical address of the merchant's business.
    """

    class Meta:
        model = Merchant
        fields = [
            "name",
            "business_email",
            "support_email",
            "tax_identification_number",
            "registration_number",
            "address",
        ]
        read_only_fields = ["tenant_id", "active", "kyc_verified"]

    def validate(self, attrs):
        """
        Validate the data before updating the merchant instance.
        """

        business_email = attrs.get("business_email", None)
        # ensure the business email is unique (if provided)

        if self.instance:
            instance = self.instance
            if (
                business_email
                and Merchant.objects.exclude(pk=instance.pk)
                .filter(business_email=business_email)
                .exists()
            ):
                raise serializers.ValidationError(
                    {"business_email": "This email address is already in use."}
                )
        return attrs

    def update(self, instance, validated_data):
        """
        Updates the merchant instance with the provided validated data

        Allows us wrap the update operation with a dtabase transaction
        """
        with transaction.atomic():
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()
            return instance


class MerchantUpdateResponseSerializer(serializers.Serializer):
    """
    Serializer for the response after updating a merchant's information.

    Fields:
        - message: A message indicating the success of the operation.
        - updated_merchant: The updated merchant information.
    """

    message = serializers.CharField(
        max_length=255,
        help_text="A message indicating the success of the update operation.",
    )
    updated_merchant = MerchantUpdateSerializer(
        help_text="The updated information of the merchant."
    )
