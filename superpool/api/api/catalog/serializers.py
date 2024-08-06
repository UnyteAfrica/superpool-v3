import logging
from datetime import datetime
from typing import Union

from api.catalog.services import PolicyService
from core.catalog.models import Policy, Price, Product, Quote
from core.merchants.models import Merchant
from core.models import Coverage
from core.providers.models import Provider as Partner
from django.db.models import Q
from core.user.models import Customer
from rest_framework import serializers
from rest_framework.serializers import ModelSerializer, ValidationError

logger = logging.getLogger(__name__)


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


class BaseQuoteRequestSerializer(serializers.Serializer):
    """
    Validate the base quote request payload
    """

    customer_metadata = CustomerDetailsSerializer(required=False)


class TravelInsuranceSerializer(BaseQuoteRequestSerializer):
    """
    Validate the travel insurance quote request payload

    """

    destination = serializers.CharField(max_length=255)
    departure_date = serializers.DateField(input_formats=["%Y-%m-%d"])
    return_date = serializers.DateField(input_formats=["%Y-%m-%d"])
    number_of_travellers = serializers.IntegerField(min_value=1, max_value=10)
    trip_duration = serializers.IntegerField(min_value=1, max_value=365, required=False)
    trip_type = serializers.ChoiceField(
        choices=[("one_way", "One Way"), ("round_trip", "Round Trip")]
    )
    trip_type_details = serializers.ChoiceField(
        choices=[
            ("business", "Business"),
            ("leisure", "Leisure"),
            ("education", "Education"),
            ("religious", "Religious"),
            ("medical", "Medical"),
        ],
        required=False,
    )


class HealthInsuranceSerializer(BaseQuoteRequestSerializer):
    """
    Validate the health insurance quote request payload

    """

    health_condition = serializers.ChoiceField(
        choices=[
            ("good", "Good"),
            ("fair", "Fair"),
            ("poor", "Poor"),
            ("critical", "Critical"),
        ]
    )
    age = serializers.IntegerField(min_value=1, max_value=100)
    coverage_type = serializers.ChoiceField(
        choices=[
            ("basic", "Basic"),
            ("standard", "Standard"),
            ("premium", "Premium"),
        ],
    )
    coverage_type_details = serializers.ChoiceField(
        choices=[
            ("individual", "Individual"),
            ("family", "Family"),
            ("group", "Group"),
        ],
        required=False,
    )


class AutoInsuranceSerializer(BaseQuoteRequestSerializer):
    """
    Validate the auto insurance quote request payload

    """

    vehicle_type = serializers.ChoiceField(
        choices=[
            ("car", "Car"),
            ("bike", "Bike"),
        ]
    )
    vehicle_make = serializers.CharField(max_length=100, required=False)
    vehicle_model = serializers.CharField(max_length=100, required=False)
    vehicle_year = serializers.IntegerField(
        min_value=1900,
        max_value=datetime.now().year,
    )
    vehicle_value = serializers.DecimalField(
        max_digits=10, decimal_places=2, required=False
    )
    vehicle_usage = serializers.ChoiceField(
        choices=[
            ("personal", "Personal"),
            ("commercial", "Commercial"),
            ("rideshare", "Ride Share"),
        ]
    )
    vehicle_usage_details = serializers.ChoiceField(
        choices=[
            ("private", "Private"),
            ("public", "Public"),
            ("commercial", "Commercial"),
        ],
        required=False,
    )
    vehicle_mileage = serializers.IntegerField(min_value=1, max_value=100000)
    vehicle_location = serializers.ChoiceField(
        choices=[
            ("urban", "Urban"),
            ("suburban", "Suburban"),
            ("rural", "Rural"),
        ]
    )
    vehicle_location_details = serializers.ChoiceField(
        choices=[
            ("high_crime", "High Crime"),
            ("low_crime", "Low Crime"),
            ("safe", "Safe"),
        ],
        required=False,
    )
    vehicle_purpose = serializers.ChoiceField(
        choices=[
            ("personal", "Personal"),
            ("commercial", "Commercial"),
        ]
    )
    vehicle_purpose_details = serializers.ChoiceField(
        choices=[
            ("business", "Business"),
            ("commute", "Commute"),
        ],
        required=False,
    )


class PersonalAccidentInsuranceSerializer(BaseQuoteRequestSerializer):
    """
    Validate the personal accident insurance quote request payload


    """

    occupation = serializers.CharField(max_length=255)
    occupation_risk_level = serializers.ChoiceField(
        choices=[
            ("low", "Low"),
            ("medium", "Medium"),
            ("high", "High"),
        ],
        required=False,
    )
    occupation_risk_details = serializers.ChoiceField(
        choices=[
            ("office", "Office"),
            ("field", "Field"),
            ("remote", "Remote"),
        ],
        required=False,
    )
    age = serializers.IntegerField(min_value=1, max_value=100)


class HomeInsuranceSerializer(BaseQuoteRequestSerializer):
    """
    Validate the home insurance quote request payload

    """

    property_type = serializers.ChoiceField(
        choices=[
            ("house", "House"),
            ("apartment", "Apartment"),
            ("condo", "Condo"),
        ]
    )
    property_value = serializers.DecimalField(max_digits=10, decimal_places=2)
    property_location = serializers.CharField(max_length=255)
    security_details = serializers.JSONField(required=False)


class GadgetInsuranceSerializer(BaseQuoteRequestSerializer):
    """
    Validate the gadget insurance quote request payload


    """

    gadget_type = serializers.ChoiceField(
        choices=[
            ("smartphone", "Smartphone"),
            ("laptop", "Laptop"),
            ("tablet", "Tablet"),
            ("smartwatch", "Smartwatch"),
            ("camera", "Camera"),
            ("headphones", "Headphones"),
            ("other", "Other"),
        ]
    )
    gadget_information = serializers.JSONField(required=False)
    usage_history = serializers.JSONField(required=False)


class QuoteRequestSerializer(serializers.Serializer):
    """Validate the entire quote request payload"""

    product_type = serializers.ChoiceField(
        choices=[
            ("health", "Health Insurance"),
            ("auto", "Auto Insurance"),
            ("travel", "Travel Insurance"),
            ("personal_accident", "Personal Accident Insurance"),
            ("home", "Home Insurance"),
            ("gadget", "Gadget Insurance"),
        ]
    )
    quote_code = serializers.CharField(required=False)
    insurance_name = serializers.CharField(required=False)
    # customer_metadata = CustomerDetailsSerializer()
    insurance_details = serializers.JSONField()

    def get_serializer_class(self, product_type):
        """Return the appropriate serializer class based on the product type"""
        # product_type = self.initial_data.get("insurance_type")
        serializer_mapping = {
            "health": HealthInsuranceSerializer,
            "auto": AutoInsuranceSerializer,
            "travel": TravelInsuranceSerializer,
            "personal_accident": PersonalAccidentInsuranceSerializer,
            "home": HomeInsuranceSerializer,
            "gadget": GadgetInsuranceSerializer,
        }
        return serializer_mapping.get(product_type)

    def validate_insurance_details(self, value):
        """Return the insurance details based on the product type"""
        product_type = self.initial_data.get("product_type")
        serializer_class = self.get_serializer_class(product_type)

        if not serializer_class:
            raise ValidationError(f"Invalid product type: {product_type}")

        insurance_serializer = serializer_class(data=value)
        if not insurance_serializer.is_valid():
            raise ValidationError(insurance_serializer.errors)

        return insurance_serializer.validated_data

    def validate(self, data):
        """Validates the incoming request based on the product type"""
        product_type = data.get("product_type")
        if not product_type:
            raise ValidationError("Product type must be provided.")

        data["insurance_details"] = self.validate_insurance_details(
            data["insurance_details"]
        )
        logger.info(f"Validated data: {data}")
        return data


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


class PolicyCancellationRequestSerializer(serializers.Serializer):
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


class PolicyCancellationSerializer(serializers.ModelSerializer):
    """Allow us to audit list of cancelled policy or a single cancelled policy"""

    class Meta:
        model = Policy
        fields = [
            "policy_id",
            "policy_number",
            "status",
            "cancellation_reason",
            "cancellation_date",
        ]


class PolicyCancellationResponseSerializer(serializers.Serializer):
    """
    Formats response information for cancellation request
    """

    message = serializers.CharField()
    status = serializers.CharField()
    policy_id = serializers.UUIDField()
    cancellation_reason = serializers.CharField()
    cancellation_date = serializers.DateTimeField()
    refund_amount = serializers.DecimalField(
        max_digits=10, decimal_places=2, required=False
    )


class PolicyRenewalRequestSerializer(serializers.Serializer):
    """
    Validates a policy renewal request
    """

    policy_id = serializers.UUIDField(required=False)
    policy_number = serializers.CharField(max_length=255, required=False)
    policy_end_date = serializers.DateField()
    auto_renew = serializers.BooleanField(required=False)

    def validate(self, data):
        """Validates the existence of a policy with the given policy ID or policy reference number"""
        policy_identifier = PolicyService.validate_policy(
            policy_id=data.get("policy_id"), policy_number=data.get("policy_number")
        )
        self.validate_auto_renew(policy_identifier, data.get("auto_renew"))
        data["policy_identifier"] = policy_identifier
        return data

    def validate_auto_renew(self, policy_identifier, auto_renew):
        """Ensure that auto_renew is only possible if model instance contains a 'renewable' field set to True"""
        if auto_renew:
            # check for an existing policy with this policy number (or ID), that could be autorenewed
            if not Policy.objects.filter(
                Q(policy_id=policy_identifier) | Q(policy_number=policy_identifier),
                renewable=True,
            ).exists():
                raise ValidationError(
                    "Policy does not support auto-renewal. Please contact suppport team to renew manually."
                )

    def validate_policy_end_date(self, value):
        """Ensures that the policy end date is valid (not in the past)"""
        today = datetime.now()

        if value <= today:
            raise ValidationError("Policy end date must be a future date.")
        return value


class PolicyMetadataSerializer(serializers.ModelSerializer):
    """
    Formats response information for insurance renewal request

    Its a limited view  of the PolicySerializer - exposing just enough informtion
    """

    class Meta:
        model = Policy
        fields = [
            "product_name",
            "product_type",
            "insurer",
            "customer_name",
            "customer_email",
            "customer_phone",
            "customer_address",
            "policy_status",
            "policy_id",
            "renewable",
        ]

    product_name = serializers.CharField(source="product.name")
    product_type = serializers.CharField(source="product.product_type")
    insurer = serializers.CharField(source="provider_id.name")
    customer_name = serializers.SerializerMethodField()
    customer_email = serializers.EmailField(source="policy_holder.email")
    customer_phone = serializers.CharField(source="policy_holder.phone_number")
    customer_address = serializers.CharField(source="policy_holder.address")
    policy_status = serializers.CharField(source="status")

    def get_customer_name(self, instance):
        """Returns the full name of the policy holder"""
        return f"{instance.policy_holder.first_name} {instance.policy_holder.last_name}"


class PolicyRenewalSerializer(serializers.ModelSerializer):
    """
    Formats response information for insurance renewal request
    """

    policy_duration = serializers.SerializerMethodField()
    renewal_date = serializers.SerializerMethodField()
    policy_metadata = PolicyMetadataSerializer()

    class Meta:
        model = Policy
        fields = [
            "policy_number",
            "policy_duration",
            "policy_metadata",
            "renewal_date",
        ]

    def get_policy_duration(self, instance):
        """Calculate the duration of the policy (in days)"""
        duration = instance.effective_through - instance.effective_from
        return duration.days

    def get_renewal_date(self, instance):
        """Gets the renewal date if auto_renew is set to True"""
        request = self.context.get("request")
        if request and request.data.get("auto_renew"):
            return instance.effective_through
        return None
