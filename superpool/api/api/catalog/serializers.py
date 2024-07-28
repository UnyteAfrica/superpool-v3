from datetime import datetime
from typing import Union

from core.catalog.models import Policy, Price, Product, Quote
from core.merchants.models import Merchant
from core.models import Coverage
from core.providers.models import Provider as Partner
from core.user.models import Customer
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
        fields = "__all__"
        extra_kwargs = {
            "policy_id": {"read_only": True},
            "merchant_id": {"read_only": True},
            "provider_id": {"read_only": True},
        }


class PolicyPurchaseResponseSerializer(serializers.ModelSerializer):
    """
    Limited view of the PolicySerializer for the purchase response
    """

    policy_reference_number = serializers.CharField(source="policy_number")

    class Meta:
        model = Policy
        fields = [
            "policy_id",
            "policy_reference_number",
            "product",
            "premium",
        ]
        depth = 1


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
    product_name = serializers.CharField(max_length=255, required=False)
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

    quote_code = serializers.CharField()
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

    def create(self, validated_data):
        """
        Creates and save the policy in the database
        """
        # first we prep all information to use in creating the new policy
        customer_metadata = validated_data["customer_metadata"]
        product_metadata = validated_data["product_metadata"]
        payment_information = validated_data["payment_information"]
        activation_details = validated_data["activation_details"]

        # next we create each object with our information
        product = Product.objects.get(name=product_metadata["product_name"])
        coverage = Coverage.objects.get(name=product_metadata["product_type"])
        merchant = Merchant.objects.get(id=validated_data["merchant_id"])
        provider = Partner.objects.get(name=product_metadata["insurer"])
        policy_holder = Customer.objects.get_or_create(
            email=customer_metadata["customer_email"]
        )

        # then we create the actual policy object and return the policy
        policy = Policy.objects.create(
            policy_holder=policy_holder,
            product=product,
            coverage=coverage,
            premium=payment_information["premium_amount"],
            effective_from=datetime.now(),
            effective_through=datetime.strptime(
                activation_details["policy_duration"], "%Y-%m-%d"
            ),
            merchant_id=merchant,
            provider_id=provider,
            renewable=activation_details["renew"],
            inspection_required=False,
            certification_required=False,
        )
        return policy


class PolicyCancellationSerializer(serializers.Serializer):
    """
    Validates a policy cancellation request
    """

    policy_id = serializers.UUIDField(required=False)
    policy_number = serializers.CharField(max_length=255, required=False)
    cancellation_reason = serializers.CharField(max_length=500)

    def validate(self, data):
        """Validates a policy exist wth the given policy ID or policy reference number"""
        if not data.get("policy_id") and not data.get("policy_number"):
            raise ValidationError("Either policy_id or policy_number must be provided.")

        if data.get("policy_id"):
            if not Policy.objects.filter(
                policy_id=data["policy_id"], status="active"
            ).exists():
                raise ValidationError("Policy not found or already cancelled.")

        if data.get("policy_number"):
            if not Policy.objects.filter(
                policy_number=data["policy_number"], status="active"
            ).exists():
                raise ValidationError("Policy not found or already cancelled.")

        return data


class PolicyCancellationResponseSerializer(serializers.Serializer):
    """
    Formats response information for cancellation request
    """

    policy_id = serializers.UUIDField()
    status = serializers.CharField()
    cancellation_reason = serializers.CharField()
    cancellation_date = serializers.DateTimeField()
    refund_amount = serializers.DecimalField(
        max_digits=10, decimal_places=2, required=False
    )
    message = serializers.CharField()
