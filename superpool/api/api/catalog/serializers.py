from datetime import datetime
from typing import Union

from core.catalog.models import Policy, Price, Product, Quote
from core.user.models import Customer
from django.db.models import fields
from rest_framework import serializers
from rest_framework.serializers import ModelSerializer, ValidationError


class ProductSerializer(ModelSerializer):
    """
    Serializer for the Product model
    """

    class Meta:
        model = Product
        fields = "__all__"


class PolicySerializer(ModelSerializer):
    """
    Serializer for the Policy model
    """

    class Meta:
        model = Policy
        depth = 1
        fields = [
            "policy_id",
            "product",
            "policy_holder",
            "effective_from",
            "effective_through",
            "premium",
            "coverage",
            "merchant_id",
            "provider_id",
            "renewable",
            "inspection_required",
            "cerfication_required",
        ]
        extra_kwargs = {
            "policy_id": {"read_only": True},
            "merchant_id": {"read_only": True},
            "provider_id": {"read_only": True},
        }


class CreatePolicySerializer(ModelSerializer):
    """
    Serializer for creating a Policy model

    This serializer is used to create a new policy

    """

    class Meta:
        model = Policy
        fields = (
            "name",
            "policy_holder",
            "premium",
            "coverage",
            "merchant_id",
            "provider_id",
            "renewable",
        )
        exclude = ("cerfication_required", "inspection_required")


class PriceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Price
        exclude = ["id"]


class QuoteSerializer(serializers.ModelSerializer):
    price = PriceSerializer(source="premium")
    product = ProductSerializer()
    quote_expiry_date = serializers.DateTimeField(source="expires_in", read_only=True)

    class Meta:
        model = Quote
        fields = ["quote_code", "base_price", "product", "quote_expiry_date", "price"]
        extra_kwargs = {"quote_code": {"read_only": True}}

    def create(self, validated_data):
        # Verify that when creating new quote there is a quote_code, corresponding product,
        # and calculated premium
        product_data = validated_data.pop("product")
        price_data = validated_data.pop("premium")

        product = Product.objects.create(**product_data)
        price = Price.objects.create(**price_data)

        quote = Quote.objects.create(product=product, premium=price, **validated_data)
        return quote

    def update(self, instance, validated_data):
        # when updating quotes we only care about two thing, price and the quote_code
        price_data = validated_data.pop("premium", None)

        if price_data:
            # Update the Price object with new data
            Price.objects.filter(pk=instance.premium.pk).update(**price_data)
        return super().update(instance, validated_data)


class CustomerDetailsSerializer(serializers.Serializer):
    """
    Validate customer-specific information in incoming requests

    Information could vary based on the type of insurance

    TODO: maybe use composition/inheritance for child serializers for
          the product-specific customer information:

     - AutoInsuranceDetailsSerializer
     - HealthInsuranceDetailsSerializer
     - PersonalAccidentInsuranceDetailsSerializer
     - TravelInsuranceDetailsSerializer
    """

    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100)
    customer_email = serializers.EmailField()
    customer_phone = serializers.CharField(max_length=20, required=False)
    customer_address = serializers.CharField()


class QuoteRequestSerializer(serializers.Serializer):
    """Validate the entire quote request payload"""

    insurance_type = serializers.ChoiceField(
        choices=[
            ("health", "Health Insurance"),
            ("auto", "Auto Insurance"),
            ("travel", "Travel Insurance"),
            ("personal_accident", "Personal Accident Insurance"),
        ]
    )
    quote_code = serializers.CharField(required=False)
    insurance_name = serializers.CharField(required=False)
    customer_metadata = CustomerDetailsSerializer()


class ProductMetadataSerializer(serializers.Serializer):
    product_name = serializers.CharField(max_length=255)
    product_type = serializers.CharField(max_length=50)
    insurer = serializers.CharField(max_length=100, required=False)


class PaymentInformationSerializer(serializers.Serializer):
    payment_method = serializers.CharField(max_length=50)
    payment_status = serializers.CharField(max_length=50)
    premium_amount = serializers.DecimalField(max_digits=10, decimal_places=2)


class ActivationMetadataSerializer(serializers.Serializer):
    policy_duration = serializers.DateField(write_only=True, input_formats=["%Y-%m-%d"])
    renew = serializers.BooleanField()

    def validate_policy_duration(self, value) -> Union[bool, ValidationError]:
        """Ensures that a policy duration date is valid (not in the past)"""
        today = datetime.now()

        try:
            policy_duration = datetime.strptime(value, "%Y-%m-%d")
            if policy_duration <= today:
                raise ValidationError("Policy duration must be a future date.")
        except ValueError:
            raise ValidationError("Invalid date format for policy duration")
        return value


class PolicyPurchaseSerializer(serializers.Serializer):
    """
    Validates the purchase request payload

    Issues a new policy based on customer information and some
    other metadata

    For example:

    ```json
        {
          "customer_information": {
            "customer_name": "John Doe",
            "customer_email": "john.doe@example.com",
            "customer_phone": "123-456-7890",
            "customer_address": "123 Main St, Anytown, Country",
          },
          'quote_code': 'quo_DADDY_HELP_ME',
          "product_selection": {
            "product_name": "Smart Motorist Protection Plan",
            "product_type": "Basic",
            "insurer": "NEM"
          },
          "payment_information": {
            "payment_method": "credit_card",
            'payment_status': 'completed',
            "premium_amount": 2000.00,
          },
          "activation_details": {
            "policy_duration": "1 year"
            'renew': True # or False
          },
          "agreement": true,
          "confirmation": true
        }
    ```
    """

    quote_code = serializers.CharField(required=True)
    customer_metadata = CustomerDetailsSerializer()
    product_metadata = ProductMetadataSerializer()
    payment_metadata = PaymentInformationSerializer()
    acivation_metadata = ActivationMetadataSerializer()
    agreement = serializers.BooleanField(write_only=True)
    confirmation = serializers.BooleanField(write_only=True)

    def validate_agreement(self, value):
        if not value:
            raise ValidationError(
                "Agreement must be confirmed to proceed with the purchase of this policy"
            )
        return value

    def validate_confirmation(self, value):
        if not value:
            raise ValidationError(
                "Confirmation must be provided to proceed with the purchase of this policy"
            )
        return value
