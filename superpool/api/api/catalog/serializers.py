import logging
from datetime import datetime, date, timedelta
from typing import Union

from api.catalog.services import PolicyService
from api.notifications.services import PolicyNotificationService
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
    customer_information = serializers.SerializerMethodField()
    renewal_information = serializers.SerializerMethodField()
    insurer = serializers.CharField(source="provider_id.name")
    product_information = serializers.SerializerMethodField()
    policy_status = serializers.CharField(source="status")

    class Meta:
        model = Policy
        fields = [
            "policy_id",
            "policy_reference_number",
            "effective_from",
            "effective_through",
            "premium",
            "insurer",
            "policy_status",
            "product_information",
            "customer_information",
            "renewal_information",
        ]
        # depth = 1

    def get_customer_information(self, instance):
        """Returns the customer information as a dictionary"""
        return {
            "customer_name": f"{instance.policy_holder.full_name}",
            "customer_email": instance.policy_holder.email,
            "customer_phone": instance.policy_holder.phone_number,
            "customer_address": instance.policy_holder.address,
        }

    def get_renewal_information(self, instance):
        """Returns the renewal information as a dictionary"""
        if instance.renewable:
            return {
                "renewable": instance.renewable,
                "renewal_date": instance.renewal_date,
            }
        return {"renewable": instance.renewable}

    def get_product_information(self, instance):
        """Returns the product information as a dictionary"""
        return {
            "product_name": instance.product.name,
            "product_type": instance.product.product_type,
            "product_description": instance.product.description,
        }


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
    customer_date_of_birth = serializers.DateField(
        input_formats=["%d-%m-%Y"], required=False
    )
    customer_gender = serializers.ChoiceField(
        choices=[("M", "Male"), ("F", "Female")], required=False
    )

    def validate_customer_date_of_birth(self, value):
        """Ensures that the date of birth is valid (not in the future)"""
        today = datetime.now().date()

        if value >= today:
            raise ValidationError("Date of birth must be in the past.")
        return value


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
    HEALTH = "health"
    AUTO = "auto"
    TRAVEL = "travel"
    PERSONAL_ACCIDENT = "personal_accident"
    HOME = "home"
    GADGET = "gadget"

    VALID_PRODUCT_TYPES = [
        HEALTH,
        AUTO,
        TRAVEL,
        PERSONAL_ACCIDENT,
        HOME,
        GADGET,
    ]
    product_type = serializers.ChoiceField(choices=VALID_PRODUCT_TYPES)
    product_name = serializers.CharField(max_length=100, required=False)
    insurer = serializers.CharField(max_length=100, required=False)


class PaymentInformationSerializer(serializers.Serializer):
    payment_method = serializers.CharField(max_length=50)
    payment_status = serializers.CharField(max_length=50)
    premium_amount = serializers.DecimalField(max_digits=10, decimal_places=2)

    def validate_premium_amount(self, value):
        if value <= 0:
            raise ValidationError("Premium amount must be greater than zero.")
        return value

    def validate(self, attrs):
        VALID_PAYMENT_METHODS = [
            "credit_card",
            "debit_card",
            "bank_transfer",
            "cash",
        ]
        VALID_PAYMENT_STATUS = ["completed", "pending", "failed"]

        if attrs.get("payment_method") not in VALID_PAYMENT_METHODS:
            raise ValidationError("Invalid payment method.")

        if attrs.get("payment_status") not in VALID_PAYMENT_STATUS:
            raise ValidationError("Invalid payment status")
        return attrs


class ActivationMetadataSerializer(serializers.Serializer):
    policy_expiry_date = serializers.DateField(input_formats=["%Y-%m-%d"])
    renew = serializers.BooleanField(default=False, required=False)

    def validate_policy_expiry_date(
        self, value: Union[str, date]
    ) -> Union[str, date, ValidationError]:
        """Ensures that a policy duration date is valid (not in the past)"""
        today = datetime.now().date()

        try:
            if isinstance(value, date):
                policy_expiry_date = value
            else:
                policy_expiry_date = datetime.strptime(value, "%Y-%m-%d").date()

            if policy_expiry_date <= today:
                raise ValidationError("Policy duration must be a future date.")
        except ValueError:
            raise ValidationError("Invalid date format for policy duration")

        return value


class PolicyPurchaseSerializer(serializers.Serializer):
    """
    Validates the purchase request payload
    """

    quote_code = serializers.CharField()
    customer_metadata = CustomerDetailsSerializer()
    product_metadata = ProductMetadataSerializer()
    payment_metadata = PaymentInformationSerializer()
    activation_metadata = ActivationMetadataSerializer()
    agreement = serializers.BooleanField()
    confirmation = serializers.BooleanField()
    merchant_code = serializers.CharField(
        max_length=50, help_text="Merchant short code"
    )

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

    def validate_quote_code(self, value):
        if not value.startswith("Q"):
            raise ValidationError("Invalid quote code. Must start with 'Q'")

        if not value:
            raise ValidationError("Quote code must be provided.")
        return value

    def validate(self, attrs):
        # validate merchant code
        VALID_MERCHANT_CODE_LENGTH = 8
        if len(attrs.get("merchant_code")) != VALID_MERCHANT_CODE_LENGTH:
            raise ValidationError("Invalid merchant code. Must be 7 characters long")
        return attrs


class PolicyCancellationRequestSerializer(serializers.Serializer):
    """
    Validates a policy cancellation request
    """

    policy_id = serializers.UUIDField(required=False)
    policy_number = serializers.CharField(max_length=255, required=False)
    cancellation_reason = serializers.CharField(max_length=500)
    alternative_offerings = serializers.JSONField(
        required=False,
        help_text=(
            "Optional: Information on alternative policies or offers that might suit the policyholder needs, provided by the merchant before proceeding with cancellation"
        ),
    )
    merchant_feedback = serializers.CharField(
        max_length=500,
        required=False,
        help_text=(
            "Optional: Feedback or comments from the merchant on the policyholder's request for cancellation"
        ),
    )

    def validate(self, attrs):
        """Validates a policy exist wth the given policy ID or policy reference number"""
        policy_id = attrs.get("policy_id")
        policy_number = attrs.get("policy_number")

        if policy_id and policy_number:
            raise ValidationError(
                "Only one of Policy ID or Policy Number must be provided in a request"
            )
        if policy_id and not Policy.objects.filter(policy_id=policy_id).exists():
            raise ValidationError("Policy not found or already cancelled.")

        if (
            policy_number
            and not Policy.objects.filter(policy_number=policy_number).exists()
        ):
            raise ValidationError("Policy not found or already cancelled.")

        return attrs


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

    policy_id = serializers.UUIDField()
    policy_number = serializers.CharField()
    cancellation_reason = serializers.CharField()
    cancellation_date = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")


class PolicyRenewalRequestSerializer(serializers.Serializer):
    """
    Validates a policy renewal request
    """

    policy_id = serializers.UUIDField(required=False)
    policy_number = serializers.CharField(required=False)
    preferred_policy_start_date = serializers.DateField(input_formats=["%Y-%m-%d"])
    policy_duration = serializers.IntegerField(min_value=1, max_value=365)
    include_additional_coverage = serializers.BooleanField(default=False)
    modify_exisitng_coverage = serializers.BooleanField(default=False)
    coverage_details = serializers.JSONField(required=False)
    auto_renew = serializers.BooleanField(default=False)

    def validate(self, attrs):
        # validate only one of Policy ID or Policy Number can be present in a given request
        policy_id = attrs.get("policy_id")
        policy_number = attrs.get("policy_number")
        preferred_policy_start_date = attrs.get("preferred_policy_start_date")

        if policy_id and policy_number:
            raise ValidationError(
                "Only one of Policy ID or Policy Number must be provided in a request"
            )

        # validate a policy is renewable
        try:
            if policy_id:
                policy = Policy.objects.get(policy_id=attrs["policy_id"])
            if policy_number:
                policy = Policy.objects.get(policy_id=attrs["policy_id"])
        except Policy.DoesNotExist:
            raise ValidationError("Policy not found with the provided policy ID")
        if not policy.renewable:
            raise ValidationError("Policy is not renewable")

        # guard against un-nessary renewal in as much policy is active within effective date
        now = datetime.now().date()
        if (
            policy.status == "active"
            and policy.effective_from <= now <= policy.effective_through
        ):
            raise ValidationError(
                "Policy is currently active and within its valid effective period. Renewal is not needed."
            )

        # merchant can choose to modify coverage based on customer preferance or
        # include additional coverage as part of the renewal
        # however, both options cannot be selected at the same time
        if attrs.get("modify_exisitng_coverage") and attrs.get(
            "include_additional_coverage"
        ):
            raise ValidationError(
                "Only one of modify_exisitng_coverage or include_additional_coverage must be selected"
            )

        # if one of these above are set, we can then require the coverage details
        if attrs.get("modify_exisitng_coverage") or attrs.get(
            "include_additional_coverage"
        ):
            if not attrs.get("coverage_details"):
                raise ValidationError(
                    "Coverage details must be provided when modifying or including additional coverage"
                )

        # additional security layer!
        # supplmentary to
        # you can't set current preferred policy start date is < than that previously on the db
        preferred_policy_start_date = attrs.get("preferred_policy_start_date")
        if preferred_policy_start_date:
            if (
                policy.effective_through
                and preferred_policy_start_date <= policy.effective_through
            ):
                raise ValidationError(
                    "Preferred start date must be after the current policy's effective end date."
                )
            if (
                policy.effective_from
                and preferred_policy_start_date <= policy.effective_from
            ):
                raise ValidationError(
                    "Preferred start date must be after the current policy's effective start date."
                )
        return attrs

    def validate_preferred_policy_start_date(self, value):
        """Ensures that the preferred start date is valid (not in the past)"""
        today = datetime.now().date()

        # check the preferred renewal date is in the future
        if value <= today:
            raise ValidationError("Preferred start date must be in the future.")

        # TODO: check the preffered renewal date is whithin the renewal window
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
            "policy_id",
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
