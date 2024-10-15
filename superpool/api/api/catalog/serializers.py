import logging
from datetime import date, datetime
from decimal import Decimal
from typing import Union

from django.db import models, transaction
from django.urls import NoReverseMatch, reverse
from django.utils import timezone
from rest_framework import serializers
from rest_framework.serializers import ModelSerializer, ValidationError

from core.catalog.models import Beneficiary, Policy, Price, Product, ProductTier, Quote
from core.merchants.models import Merchant
from core.models import Coverage
from core.providers.models import Provider
from core.user.models import Customer

logger = logging.getLogger(__name__)


class CoverageSerializer(serializers.ModelSerializer):
    coverage_description = serializers.CharField(source="description")
    url = serializers.SerializerMethodField()

    class Meta:
        model = Coverage
        fields = ["coverage_id", "coverage_name", "coverage_description", "url"]
        read_only_fields = fields

    def get_url(self, obj):
        """
        Generates a URL to access the coverage details.
        """
        try:
            return reverse("coverage-detail", kwargs={"pk": obj.coverage_id})
        except NoReverseMatch:
            return "no-url-implementation-for-this-coverage-yet"


class FullCoverageSerializer(serializers.ModelSerializer):
    """
    Serializer for formatting the full information regarding an insurance coverage
    """

    coverage_id = serializers.CharField()
    coverage_name = serializers.CharField()
    coverage_limit = serializers.DecimalField(
        max_digits=10, decimal_places=2, allow_null=True, required=False
    )
    currency = serializers.CharField(default="NGN")
    description = serializers.CharField()
    coverage_period_end = serializers.DateField(
        format="%Y-%m-%d", allow_null=True, required=False
    )
    benefits = serializers.CharField(allow_blank=True, required=False)
    exclusions = serializers.CharField(allow_blank=True, required=False)

    class Meta:
        model = Coverage
        fields = [
            "coverage_id",
            "coverage_name",
            "coverage_limit",
            "currency",
            "description",
            "coverage_period_end",
            "benefits",
            "exclusions",
        ]


class PolicyProviderSerializer(serializers.ModelSerializer):
    provider_id = serializers.UUIDField(source="id")
    provider_name = serializers.CharField(source="name")
    email = serializers.EmailField(source="support_email")

    class Meta:
        model = Provider
        fields = ["provider_id", "provider_name", "email"]
        read_only_fields = fields


class ProductSerializer(ModelSerializer):
    """
    Serializer for the Product model
    """

    coverages = CoverageSerializer(many=True)
    provider = PolicyProviderSerializer()

    class Meta:
        model = Product
        fields = "__all__"

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        representation["updated_at"] = instance.updated_at.strftime("%Y-%m-%d %H:%M:%S")
        representation["created_at"] = instance.created_at.strftime("%Y-%m-%d %H:%M:%S")

        if instance.provider:
            representation["provider"] = PolicyProviderSerializer(
                instance.provider
            ).data

        if instance.coverages.exists():
            representation["coverages"] = CoverageSerializer(
                instance.coverages.all(), many=True
            ).data

        return representation


class ProductSerializerV2(serializers.ModelSerializer):
    """
    Data serilaiser for the Product model

    Designed to handle optimized data serialization for the Product model
    """

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "product_type",
            "coverages",
            "tiers",
            "provider",
            "base_premium",
            "updated_at",
            "created_at",
        ]

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        representation["updated_at"] = instance.updated_at.strftime("%Y-%m-%d %H:%M:%S")
        representation["created_at"] = instance.created_at.strftime("%Y-%m-%d %H:%M:%S")

        if instance.provider:
            representation["provider"] = PolicyProviderSerializer(
                instance.provider
            ).data

        if instance.coverages.exists():
            representation["coverages"] = CoverageSerializer(
                instance.prefetched_coverages, many=True
            ).data

        if instance.tiers.exists():
            representation["tiers"] = TierSerializer(
                instance.prefetched_tiers, many=True
            ).data

        return representation


class TierSerializer(serializers.ModelSerializer):
    """
    Serializer for the a given  product Tier model
    """

    tier_price = serializers.DecimalField(
        max_digits=10, decimal_places=2, required=False, source="base_premium"
    )

    class Meta:
        model = ProductTier
        fields = ["tier_name", "description", "tier_price", "pricing"]
        read_only_fields = fields


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
        fields = [
            "currency",
            "amount",
            "description",
            "discount_amount",
            "surcharges",
        ]


class QuoteSerializer(serializers.ModelSerializer):
    price = PriceSerializer(source="premium")
    product = ProductSerializer()
    quote_expiry_date = serializers.DateTimeField(source="expires_in", read_only=True)

    class Meta:
        model = Quote
        fields = ["quote_code", "base_price", "product", "quote_expiry_date", "price"]
        extra_kwargs = {"quote_code": {"read_only": True}}

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        representation["quote_expiry_date"] = instance.expires_in.strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        return representation

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
    Captures essential personal information about the applicant
    """

    class CustomerGenderChoices(models.TextChoices):
        MALE = "M", "Male"
        FEMALE = "F", "Female"

    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100)
    email = serializers.EmailField()
    phone = serializers.CharField(max_length=20, required=False)
    residential_address = serializers.CharField()
    date_of_birth = serializers.DateField(input_formats=["%Y-%m-%d"], required=False)
    customer_gender = serializers.ChoiceField(
        choices=CustomerGenderChoices.choices,
        required=False,
        help_text="Biological inclination; Male (M) or Female (F)",
    )

    def validate_customer_date_of_birth(self, value):
        """Ensures that the date of birth is valid (not in the future)"""
        today = timezone.now().date()

        if value >= today:
            raise ValidationError("Date of birth must be in the past.")
        return value


class BaseQuoteRequestSerializer(serializers.Serializer):
    """
    Validate the base quote request payload
    """

    customer_metadata = CustomerDetailsSerializer(required=False)


class TravelInsuranceSerializer(serializers.Serializer):
    """
    Validate the travel insurance quote request payload

    """

    class TravelPurposeChoices(models.TextChoices):
        BUSINESS = "business", "Business"
        LEISURE = "leisure", "Leisure"
        EDUCATION = "education", "Education"
        RELIGIOUS = "religious", "Religious"
        MEDICAL = "medical", "Medical"

    class TravelTripTypeChoices(models.TextChoices):
        ONE_WAY = "one_way", "One Way"
        ROUND_TRIP = "round_trip", "Round Trip"

    destination = serializers.CharField(
        max_length=255, help_text="Destination of travel"
    )
    departure_date = serializers.DateField(input_formats=["%Y-%m-%d"])
    return_date = serializers.DateField(input_formats=["%Y-%m-%d"])
    number_of_travellers = serializers.IntegerField(
        min_value=1, max_value=10, default=1
    )
    trip_duration = serializers.IntegerField(
        min_value=1,
        max_value=365,
        required=False,
        help_text="Duration of the trip in days",
    )
    trip_type = serializers.ChoiceField(
        choices=TravelTripTypeChoices.choices,
        required=False,
        help_text="Type of trip e.g One Way, Round Trip",
    )
    trip_type_details = serializers.CharField(
        required=False,
    )
    international_flight = serializers.BooleanField(
        default=False,
        help_text="Is this insurance for an international flight?",
        required=False,
    )


class HealthInsuranceSerializer(BaseQuoteRequestSerializer):
    """
    Validate the health insurance quote request payload
    """

    class CoverageTypeChoices(models.TextChoices):
        BASIC = "basic", "Basic"
        STANDARD = "standard", "Standard"
        PREMIUM = "premium", "Premium"

    class HealthCoverageType(models.TextChoices):
        INDIVIDUAL = "individual", "Individual"
        FAMILY = "family", "Family"
        GROUP = "group", "Group"

    class HealthConditionChoices(models.TextChoices):
        GOOD = "good", "Good"
        FAIR = "fair", "Fair"
        POOR = "poor", "Poor"
        CRITICAL = "critical", "Critical"

    health_condition = serializers.ChoiceField(
        choices=HealthConditionChoices.choices,
        help_text="Health condition of the applicant e.g Good, Fair, Poor, Critical",
    )
    age = serializers.IntegerField(min_value=1, max_value=100)
    coverage_type = serializers.ChoiceField(
        choices=CoverageTypeChoices.choices,
        help_text="Type of coverage e.g Basic, Standard, Premium",
        required=False,
    )
    coverage_type_details = serializers.ChoiceField(
        choices=HealthCoverageType.choices,
        required=False,
        help_text="Additional details on the type of coverage e.g Individual, Family, Group",
    )


class AutoInsuranceSerializer(serializers.Serializer):
    """
    Validate the auto insurance quote request payload
    """

    class VehicleUsageChoices(models.TextChoices):
        PERSONAL = "Personal", "Personal"
        COMMERCIAL = "Commercial", "Commercial"
        RIDESHARE = "Rideshare", "Ride Share"

    class VehicleUsageMetadata(models.TextChoices):
        PRIVATE = "Private", "Private"
        PUBLIC = "Public", "Public"
        COMMERCIAL = "Commercial", "Commercial"

    class VehicleTypeChoices(models.TextChoices):
        CAR = "Car", "Car"
        BIKE = "Bike", "Bike"

    class VehiclePurposeChoices(models.TextChoices):
        BUSINESS = "Business", "Business"
        COMMUTE = "Commute", "Commute"

    class VehicleCategory(models.TextChoices):
        SALOON = "Saloon", "Saloon"
        SUV = "Suv", "SUV"
        TRUCK = "Truck", "Truck"
        VAN = "Van", "Van"
        MOTORCYCLE = "Motorcycle", "Motorcycle"

    vehicle_type = serializers.ChoiceField(
        choices=VehicleTypeChoices.choices, help_text="Type of vehicle e.g Car, Bike"
    )
    vehicle_make = serializers.CharField(max_length=100, required=False)
    vehicle_model = serializers.CharField(max_length=100, required=False)
    vehicle_year = serializers.IntegerField(
        min_value=1950,
        max_value=datetime.now().year,
        help_text="Year of manufacture of the vehicle",
    )
    vehicle_value = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Estimated value of the vehicle",
    )
    vehicle_usage = serializers.ChoiceField(
        choices=VehicleUsageChoices.choices,
        help_text="How the vehicle is used e.g Personal, Commercial",
        required=False,
    )
    vehicle_usage_details = serializers.ChoiceField(
        choices=VehicleUsageMetadata.choices,
        required=False,
        help_text="Additional details on how the vehicle is used, e.g Private, Public, Commercial",
    )
    vehicle_mileage = serializers.IntegerField(
        min_value=1,
        max_value=100000,
        help_text="Mileage of the vehicle in KM",
        required=False,
    )
    vehicle_location = serializers.ChoiceField(
        choices=[
            ("urban", "Urban"),
            ("suburban", "Suburban"),
            ("rural", "Rural"),
        ],
        required=False,
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
        choices=VehicleUsageMetadata.choices,
        required=False,
    )
    vehicle_purpose_details = serializers.ChoiceField(
        choices=VehiclePurposeChoices.choices,
        required=False,
    )
    vehicle_category = serializers.ChoiceField(
        choices=VehicleCategory.choices,
        required=False,
        help_text="Category of the vehicle e.g Saloon, SUV, Truck, Van, Motorcycle",
    )

    def validate(self, attrs: dict) -> dict:
        """
        Validate the auto insurance quote request payload
        """
        # We want to use this opportunity to handle how we would
        # be passing information from API layer to the service layer
        # depending on the vehicle choices

        # If vehicle is Bike - we would want to ensure that the vehicle
        # the value, usage, model and year are provided

        # Otherwise if vehicle is Car - we would want to ensure that the vehicle
        # make, value, usage, model and year are provided

        vehicle_type = attrs.get("vehicle_type")
        vehicle_make = attrs.get("vehicle_make")
        vehicle_class = attrs.get("vehicle_category")

        is_bike = vehicle_type == self.VehicleTypeChoices.BIKE
        is_car = vehicle_type == self.VehicleTypeChoices.CAR

        if is_bike:
            required_fields = ["vehicle_value", "vehicle_usage", "vehicle_year"]
            for field in required_fields:
                if field not in attrs:
                    raise ValidationError(f"{field} is required for a bike")

        if is_car:
            required_fields = [
                "vehicle_make",
                "vehicle_value",
                "vehicle_usage",
                "vehicle_year",
            ]
            for field in required_fields:
                if field not in attrs:
                    raise ValidationError(f"{field} is required for a car")

            unsupported_brands = {"Ferrari", "Lamborghini", "Bugatti", "Toyota"}
            if vehicle_make in unsupported_brands:
                raise ValidationError(f"We do not insure {vehicle_make} vehicles")

            _TRUCK_MAPPING = {
                "Van": "Light Truck",
                "Truck": "Heavy Duty Truck",
            }
            if vehicle_class in _TRUCK_MAPPING:
                attrs["vehicle_class"] = _TRUCK_MAPPING[vehicle_class]

        return attrs


class PersonalAccidentInsuranceSerializer(serializers.Serializer):
    """
    Validate the personal accident insurance quote request payload
    """

    occupation = serializers.CharField(
        max_length=255, help_text="Occupation of the applicant"
    )
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


class HomeInsuranceSerializer(serializers.Serializer):
    """
    Validate the home insurance quote request payload

    """

    class PropertyTypeChoices(models.TextChoices):
        HOUSE = "house", "House"
        APARTMENT = "apartment", "Apartment"
        CONDO = "condo", "Condo"

    property_type = serializers.ChoiceField(
        choices=PropertyTypeChoices.choices,
        help_text="Type of property e.g House, Apartment",
    )
    property_value = serializers.DecimalField(
        max_digits=10, decimal_places=2, help_text="Estimated value of the property"
    )
    stationary_items_value = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Estimated value of stationary (immobile) items in the property",
    )
    mobile_items_value = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Estimated value of mobile items in the property",
    )
    property_location = serializers.CharField(
        max_length=255,
        help_text="Location of the property in format: State, Country",
    )
    security_details = serializers.JSONField(required=False)


class ShipmentInsuranceSerializer(serializers.Serializer):
    """
    Validate the shipment insurance quote request payload
    """

    class ShipmentTypeChoices(models.TextChoices):
        DOMESTIC = "domestic", "Domestic"
        INTERNATIONAL = "international", "International"

    shipment_type = serializers.ChoiceField(
        choices=ShipmentTypeChoices.choices,
        help_text="Type of shipment e.g Domestic, International",
    )
    shipment_value = serializers.DecimalField(
        max_digits=10, decimal_places=2, help_text="Estimated value of the shipment"
    )
    shipment_origin = serializers.CharField(
        max_length=255, help_text="Location where the shipment originates"
    )
    shipment_destination = serializers.CharField(
        max_length=255, help_text="Location where the shipment is destined"
    )
    shipment_carrier = serializers.CharField(
        max_length=255, help_text="Carrier company handling the shipment"
    )
    shipment_carrier_details = serializers.JSONField(required=False)
    exchange_rate = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        help_text="Current Exchange rate for international shipments",
    )


class GadgetInsuranceSerializer(serializers.Serializer):
    """
    Validate the gadget (Device) insurance quote request payload
    """

    class DeviceTypeCategory(models.TextChoices):
        MOBILE = "mobile", "Mobile"
        COMPUTER = "computer", "Computer"
        CAMERA = "camera", "Camera"
        AUDIO = "audio", "Audio"
        WEARABLE = "wearable", "Wearable"
        OTHER = "other", "Other"

    class DeviceTypeChoices(models.TextChoices):
        POS = "pos", "Point-of-Sale Terminal (POS)"
        SMARTPHONE = "smartphone", "Smartphone"
        LAPTOP = "laptop", "Laptop"
        TABLET = "tablet", "Tablet"
        SMARTWATCH = "smartwatch", "Smartwatch"
        CAMERA = "camera", "Camera"
        HEADPHONES = "headphones", "Headphones"
        OTHER = "other", "Other"

    gadget_type = serializers.ChoiceField(
        choices=[
            (DeviceTypeChoices.POS, "Point-of-Sale Terminal (POS)"),
            (DeviceTypeChoices.SMARTPHONE, "Smartphone"),
            (DeviceTypeChoices.LAPTOP, "Laptop"),
            (DeviceTypeChoices.TABLET, "Tablet"),
            (DeviceTypeChoices.SMARTWATCH, "Smartwatch"),
            (DeviceTypeChoices.CAMERA, "Camera"),
            (DeviceTypeChoices.HEADPHONES, "Headphones"),
            (DeviceTypeChoices.OTHER, "Other"),
        ],
        help_text="Type of gadget e.g Smartphone, Laptop, etc",
    )
    gadget_information = serializers.JSONField(
        required=False,
        help_text="Additional information about the gadget in JSON e.g IMEI number, Serial number",
    )
    usage_history = serializers.JSONField(
        required=False, help_text="Usage history in JSON"
    )

    def get_device_category(self, gadget_type: str):
        """
        Returns the category of the device based on the device type
        """
        if gadget_type in [
            self.DeviceTypeChoices.SMARTPHONE,
            self.DeviceTypeChoices.TABLET,
        ]:
            return self.DeviceTypeCategory.MOBILE
        elif gadget_type in [
            self.DeviceTypeChoices.LAPTOP,
            self.DeviceTypeChoices.POS,
        ]:
            return self.DeviceTypeCategory.COMPUTER
        elif gadget_type == self.DeviceTypeChoices.CAMERA:
            return self.DeviceTypeCategory.CAMERA
        elif gadget_type == self.DeviceTypeChoices.HEADPHONES:
            return self.DeviceTypeCategory.AUDIO
        elif gadget_type == self.DeviceTypeChoices.SMARTWATCH:
            return self.DeviceTypeCategory.WEARABLE
        else:
            return self.DeviceTypeCategory.OTHER

    def validate(self, attrs: dict):
        """
        Validate the gadget insurance quote request payload
        """
        gadget_type = attrs.get("gadget_type")
        if gadget_type:
            attrs["gadget_category"] = self.get_device_category(gadget_type)
        return attrs


class QuoteRequestSerializer(serializers.Serializer):
    """Validate the entire quote request payload"""

    product_id = serializers.UUIDField(required=False)
    product_type = serializers.CharField(
        required=False,
    )
    quote_code = serializers.CharField(required=False)
    insurance_name = serializers.CharField(required=False)
    # customer_metadata = CustomerDetailsSerializer(required=False)
    insurance_details = serializers.JSONField()

    def _normalize_product_type(self, product_type):
        if product_type:
            product_type_normalized = product_type.strip().title()
            for ptype in Product.ProductType:
                if ptype.label == product_type_normalized:
                    return ptype
        return None

    def get_serializer_class(self, product_type):
        """Return the appropriate serializer class based on the product type"""

        if product_type is None:
            return None

        product_type = product_type.lower()

        serializer_mapping = {
            Product.ProductType.HEALTH: HealthInsuranceSerializer,
            Product.ProductType.AUTO: AutoInsuranceSerializer,
            Product.ProductType.TRAVEL: TravelInsuranceSerializer,
            Product.ProductType.PERSONAL_ACCIDENT: PersonalAccidentInsuranceSerializer,
            Product.ProductType.HOME: HomeInsuranceSerializer,
            Product.ProductType.GADGET: GadgetInsuranceSerializer,
        }
        return serializer_mapping.get(product_type)

    def get_product_from_id(self, product_id):
        """Fetch product details based on the provided product ID"""
        try:
            product = Product.objects.get(id=product_id)
            return product
        except Product.DoesNotExist:
            return None

    #
    # def validate_insurance_details(self, value, product_type):
    #     """Return the insurance details based on the product type"""
    #
    #     serializer_class = self.get_serializer_class(product_type)
    #
    #     if not serializer_class:
    #         logger.error(
    #             f"Invalid product type recieved: {product_type}. Full data: {value}"
    #         )
    #         raise ValidationError(f"Invalid product type: {product_type}")
    #
    #     insurance_serializer = serializer_class(data=value)
    #     if not insurance_serializer.is_valid():
    #         raise ValidationError(insurance_serializer.errors)
    #
    #     return insurance_serializer.validated_data

    def validate(self, attrs):
        """Validates the incoming request based on the product type"""

        product_type = attrs.get("product_type")
        product_id = attrs.get("product_id")
        insurance_name = attrs.get("insurance_name")
        insurance_details = attrs.get("insurance_details", {})

        print(
            f"Initial validation values: product_type={product_type}, product_id={product_id}, "
            f"insurance_name={insurance_name}, insurance_details={insurance_details}"
        )

        # normalize prouct type to lowercase for consitent matching
        normalized_product_type = self._normalize_product_type(product_type)
        if normalized_product_type:
            attrs["product_type"] = normalized_product_type

        # ensure either product_id or product_type and insurance_name are provided
        if not product_id:
            if not normalized_product_type or not insurance_name:
                raise ValidationError(
                    "You must provide either 'product_id' "
                    "or 'product_type' and 'insurance_name'"
                )

            # ensure coverage_type is provided if product_id is not
            if not insurance_details.get("coverage_type"):
                raise serializers.ValidationError(
                    "If no product ID is provided, 'coverage_type' must be specified in 'insurance_details'."
                )

            # ensure product type is valid
            valid_product_types = [p.lower() for p in Product.ProductType.values]
            if normalized_product_type not in valid_product_types:
                raise ValidationError(
                    f"Invalid product type: {product_type}"
                    f"Expected one of: {valid_product_types}"
                )

            serializer_class = self.get_serializer_class(normalized_product_type)
            if not serializer_class:
                raise ValidationError(
                    f"Invalid product type: {normalized_product_type}"
                )

            insurance_serializer = serializer_class(data=insurance_details)
            if not insurance_serializer.is_valid():
                raise ValidationError(insurance_serializer.errors)

            attrs["insurance_details"] = insurance_serializer.validated_data

            # validate insurance details from the provided product type
            # insurance_details["product_type"] = product_type
            # attrs["insurance_details"] = self.validate_insurance_details(
            #     product_type, insurance_details
            # )

        else:
            product = self.get_product_from_id(product_id)
            if not product:
                raise ValidationError("Product with the provided ID not found.")
            attrs["product_type"] = product.product_type
            attrs["insurance_name"] = product.name

        logger.info(f"Validated data: {attrs}")
        return attrs


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
            raise ValidationError("Policy not found")

        if (
            policy_number
            and not Policy.objects.filter(policy_number=policy_number).exists()
        ):
            raise ValidationError("Policy not found")

        # check if a policy had been previously cancelled, YOU CAN'T CANCEL AN ALREADY CANCELLED POLICY
        if policy_id or policy_number:
            filters = {}
            if policy_id:
                filters["policy_id"] = policy_id
            if policy_number:
                filters["policy_number"] = policy_number

            if Policy.objects.filter(**filters, status="cancelled").exists():
                raise ValidationError("Policy has already been cancelled")
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

        if not policy_id and not policy_number:
            raise ValidationError("Either policy ID or policy number must be provided")

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
        # only allow renewals if the policy is nearing expiry
        today = timezone.now().date()
        if policy.effective_from <= today <= policy.effective_through:
            # Allow renewal if the policy is nearing its end or if it's a valid renewal request
            if (
                preferred_policy_start_date
                and preferred_policy_start_date <= policy.effective_through
            ):
                raise ValidationError(
                    "Policy is currently active and within its valid effective period. Renewal is not needed if the renewal period starts before or within the current period."
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


class PolicyMerchantSerializer(serializers.ModelSerializer):
    merchant_id = serializers.UUIDField(source="id")
    merchant_name = serializers.CharField(source="name")
    merchant_code = serializers.CharField(source="short_code")

    class Meta:
        model = Merchant
        fields = ["merchant_id", "merchant_name", "merchant_code"]
        read_only_fields = fields


class PolicyCustomerSerializer(serializers.ModelSerializer):
    customer_id = serializers.UUIDField(source="id")
    customer_name = serializers.SerializerMethodField()
    customer_email = serializers.EmailField(source="email")
    customer_phone = serializers.CharField(source="phone_number")

    class Meta:
        model = Customer
        fields = [
            "customer_id",
            "customer_name",
            "customer_email",
            "customer_phone",
        ]
        read_only_fields = fields

    def get_customer_name(self, instance):
        """Returns the full name of the customer"""
        return f"{instance.first_name} {instance.last_name}"


class PolicyBeneficiarySerializer(serializers.ModelSerializer):
    beneficiary_id = serializers.UUIDField(source="id")
    beneficiary_name = serializers.SerializerMethodField()

    class Meta:
        model = Beneficiary
        fields = ["beneficiary_id", "beneficiary_name"]
        read_only_fields = fields

    def get_beneficiary_name(self, instance):
        """Returns the full name of the beneficiary"""
        return f"{instance.first_name} {instance.last_name}"


class PolicySerializer(ModelSerializer):
    """
    Serializer for the Policy model
    """

    policy_holder = PolicyCustomerSerializer()
    merchant = serializers.CharField(source="merchant.name")
    provider = PolicyProviderSerializer(source="provider_id")
    beneficiaries = serializers.ListSerializer(child=PolicyBeneficiarySerializer())
    policy_type = serializers.SerializerMethodField()

    class Meta:
        model = Policy
        fields = [
            "policy_id",
            "policy_number",
            "effective_from",
            "effective_through",
            "premium",
            "policy_holder",
            "merchant",
            "provider",
            "coverage",
            "policy_type",
            "renewable",
            "renewal_date",
            "inspection_required",
            "cerfication_required",
            "status",
            "cancellation_initiator",
            "cancellation_reason",
            "cancellation_date",
            "beneficiaries",
        ]
        read_only_fields = fields

    def get_policy_type(self, obj):
        """
        Returns the type of the policy
        """
        return obj.product.product_type if obj.product else None


class PolicyUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating policy holder-related information within a policy.
    Only allows updates to the following fields: first_name, last_name, dob, email, and address.
    """

    policy_id = serializers.UUIDField()
    policy_holder = serializers.DictField(child=serializers.CharField(), required=False)
    # policy_holder_first_name = serializers.CharField(
    #     source="policy_holder.first_name", required=False
    # )
    # policy_holder_last_name = serializers.CharField(
    #     source="policy_holder.last_name", required=False
    # )
    # policy_holder_dob = serializers.DateField(
    #     source="policy_holder.dob", required=False
    # )
    # policy_holder_email = serializers.EmailField(
    #     source="policy_holder.email", required=False
    # )
    # policy_holder_address = serializers.CharField(
    #     source="policy_holder.address", required=False
    # )
    #

    class Meta:
        model = Policy
        fields = ["policy_id", "policy_holder"]

    def update(self, instance, validated_data):
        """
        Update policy holder's personal information.
        """
        policy_holder_data = validated_data.get("policy_holder", {})

        with transaction.atomic():
            if policy_holder_data:
                customer = instance.policy_holder

                customer.first_name = policy_holder_data.get(
                    "first_name", customer.first_name
                )
                customer.last_name = policy_holder_data.get(
                    "last_name", customer.last_name
                )
                customer.email = policy_holder_data.get(
                    "customer_email", customer.email
                )
                customer.dob = policy_holder_data.get("dob", customer.dob)
                customer.address = policy_holder_data.get("address", customer.address)

                if "dob" in policy_holder_data:
                    customer.dob = policy_holder_data["dob"]
                customer.save()
            return instance


class ProductDetailsSerializer(serializers.ModelSerializer):
    """
    Quotes 2.0

    Identifies the type of insurance being requested and holds product-specific details.
    """

    product_type = serializers.ChoiceField(
        choices=Product.ProductType.choices,
        help_text="Specifies the type of insurance (e.g Life, Health, Home, Travel, etc)",
    )
    product_name = serializers.CharField(
        required=False,
        help_text="Name of insurance product e.g Driver Pass Insurance",
        trim_whitespace=True,
    )
    additional_information = serializers.JSONField(
        help_text="An object that will hold additional details based on the selected product type.",
        required=False,
    )

    class Meta:
        model = Product
        fields = ["product_type", "product_name", "additional_information"]

    def get_matching_serializer(self, product_type):
        """
        Returns the appropriate serializer class based on the product type.

        using the:
        - product_type

        determines which serializer to use for the additional information
            - ProductType.HEALTH -> HealthInsuranceSerializer
            - ProductType.AUTO -> AutoInsuranceSerializer
            - ProductType.TRAVEL -> TravelInsuranceSerializer
            - ProductType.PERSONAL_ACCIDENT -> PersonalAccidentInsuranceSerializer
            - ProductType.HOME -> HomeInsuranceSerializer

        otherwise, we would not use the additional information field, and only use the
        product_type
        """
        matching_serializers = {
            Product.ProductType.HEALTH: HealthInsuranceSerializer,
            Product.ProductType.AUTO: AutoInsuranceSerializer,
            Product.ProductType.TRAVEL: TravelInsuranceSerializer,
            Product.ProductType.PERSONAL_ACCIDENT: PersonalAccidentInsuranceSerializer,
            Product.ProductType.HOME: HomeInsuranceSerializer,
            Product.ProductType.GADGET: GadgetInsuranceSerializer,
        }
        return matching_serializers.get(product_type)

    def validate(self, attrs):
        product_type = attrs.get("product_type")
        additional_information = attrs.get("additional_information")

        # Only validate additional_information if the product_type matches one of the specified categories
        if product_type in [
            Product.ProductType.HEALTH,
            Product.ProductType.AUTO,
            Product.ProductType.TRAVEL,
            Product.ProductType.PERSONAL_ACCIDENT,
            Product.ProductType.HOME,
            Product.ProductType.GADGET,
        ]:
            if not additional_information:
                raise ValidationError(
                    "Additional information is required for this product type."
                )

            product_serializer_class = self.get_matching_serializer(product_type)
            if not product_serializer_class:
                raise ValidationError("Invalid product type.")

            logger.debug(
                f"Using serializer class: {product_serializer_class} for product type: {product_type}"
            )
            logger.debug(f"Additional Information: {additional_information}")

            product_serializer = product_serializer_class(data=additional_information)
            if not product_serializer.is_valid():
                raise ValidationError(
                    {"additional_information": product_serializer.errors}
                )

            attrs["additional_information"] = product_serializer.validated_data
        return attrs


class CoveragePreferencesSerializer(serializers.Serializer):
    """
    Captures the applicant's desired coverage options

    It captures what type of coverage the applicant is interested in (e.g., comprehensive or liability)
    and their preferred deductible amount. Additional coverages can also be specified here.
    """

    coverage_type = serializers.ListField(
        child=serializers.ChoiceField(
            choices=Coverage.CoverageType.choices,
        ),
        help_text="An array specifying the type of coverage (e.g., Comprehensive, Basic, ThirdParty, etc.",
        required=False,
    )
    coverage_amount = serializers.DecimalField(
        decimal_places=2,
        max_digits=10,
        min_value=Decimal(0),
        help_text="The amount of coverage the applicant is seeking",
        required=False,
    )
    additional_coverages = serializers.ListField(
        child=serializers.CharField(),
        help_text="Any extra coverages the applicant may want (e.g., Critical Illness for Health Insurance)",
        required=False,
    )

    # def get_coverage_type_display(self, value):
    #     """
    #     returns the valid options if an incorrect input is given for a vald coverage type
    #     """
    #     valid_choices = [choice[0] for choice in Coverage.CoverageType.choices]
    #     if value not in valid_choices:
    #         raise serializers.ValidationError(
    #             f"Invalid coverage type. Expected one of {valid_choices}."
    #         )
    #     return value


class QuoteRequestSerializerV2(serializers.Serializer):
    """
    Quotes 2.0

    Revised serializer for handling incoming quote requests for different product tiers and insurance details.
    """

    customer_metadata = CustomerDetailsSerializer(default=False)
    insurance_details = ProductDetailsSerializer(
        help_text="Identifies the type of insurance product being requested"
    )
    coverage_preferences = CoveragePreferencesSerializer(default=False)


class QuoteCoverageSerializer(serializers.Serializer):
    """
    Quote 2.0

    Revised Serializer to format the quote response.
    """

    coverage_name = serializers.CharField(
        help_text="Name of the coverage, e.g., Collision, Medical"
    )
    coverage_description = serializers.CharField(
        help_text="Description of the coverage"
    )
    coverage_type = serializers.CharField(
        help_text="Type of coverage, e.g., Health, Accident"
    )
    coverage_limit = serializers.DecimalField(
        max_digits=12, decimal_places=2, help_text="Maximum limit of the coverage"
    )

    class Meta:
        # model = Coverage
        fields = [
            "coverage_name",
            "coverage_description",
            "coverage_type",
            "coverage_limit",
            "exclusions",
            "benefits",
        ]


class QuoteTermsSerializer(serializers.Serializer):
    """
    Serializer for the terms of the insurance policy related to a quote.
    """

    duration = serializers.CharField(
        help_text="Duration of the policy, e.g., 12 months", required=False
    )
    renewal_options = serializers.CharField(
        help_text="Renewal option for the policy, e.g., Auto-renew; 'Automatic renewal with premium adjustment based on claims history.'",
        required=False,
    )
    cancellation_policy = serializers.CharField(
        help_text="Cancellation policy details, e.g., '30 days notice required for cancellation without penalty.",
        required=False,
    )

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation["duration"] = representation.get("duration", "12 months")
        representation["renewal_options"] = representation.get(
            "renewal_options", "Auto-renewal disabled; policy renewal is not automatic."
        )
        representation["cancellation_policy"] = representation.get(
            "cancellation_policy",
            "30 days notice required for cancellation without penalty.",
        )
        return representation


class QuoteProviderSerializer(serializers.ModelSerializer):
    provider_name = serializers.CharField(
        source="provider.name", help_text="Name of the insurance provider"
    )
    provider_id = serializers.CharField(
        source="provider.id", help_text="Unique identifier for the insurance provider"
    )

    class Meta:
        model = Product
        fields = ["provider_id", "provider_name"]


class QuotePricingSerializer(serializers.Serializer):
    """
    Serializer for the pricing information of a quotation about an insurance product
    """

    currency = serializers.CharField(
        max_length=10, help_text="Currency for the premium"
    )
    base_premium = serializers.DecimalField(
        max_digits=10, decimal_places=2, help_text="Base premium for the product tier"
    )
    discount_amount = serializers.DecimalField(
        max_digits=10, decimal_places=2, help_text="Discount applied to the premium"
    )
    total_amount_for_quotation = serializers.DecimalField(
        max_digits=10, decimal_places=2, help_text="Total premium after adjustments"
    )


class QuoteAdditionalMetadataSerializer(serializers.Serializer):
    """
    Serializer for additional metadata (mostly product information) related to the product tier.
    """

    product_type = serializers.CharField(
        help_text="Type of product, e.g., Health Insurance",
    )
    tier = serializers.CharField(
        help_text="Tier of the product, e.g., Standard", source="tier_name"
    )
    available_tiers = serializers.ListField(
        child=serializers.CharField(),
        help_text="List of available tiers for the product",
    )
    exclusions = serializers.ListField(
        child=serializers.CharField(
            help_text="Exclusions or limitations of the coverage",
            allow_blank=True,
        ),
    )
    benefits = serializers.ListField(
        child=serializers.CharField(
            help_text="Specific benefits included in the coverage",
            allow_blank=True,
        ),
    )
    last_updated = serializers.DateTimeField(
        help_text="Timestamp of the last update to this quote in ISO 8601 format",
        read_only=True,
    )

    class Meta:
        fields = [
            "product_type",
            "tier",
            "available_tiers",
            "exclusions",
            "benefits",
            "last_updated",
        ]

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        last_updated = timezone.now()
        representation["last_updated"] = last_updated.strftime("%Y-%m-%d %H:%M:%S")
        return representation


class QuoteResponseSerializer(serializers.Serializer):
    """
    Serializer to format the quote response in a structured, unified way.
    """

    quote_code = serializers.CharField(help_text="Unique identifier for the quote")
    purchase_id = serializers.CharField(
        help_text="Purchase ID for completing the transaction with an external payment processor"
    )
    provider_information = QuoteProviderSerializer(source="product")
    coverages = QuoteCoverageSerializer(
        source="additional_metadata.coverage_details",
        many=True,
        help_text="List of coverage details",
    )
    additional_metadata = QuoteAdditionalMetadataSerializer(
        help_text="Additional information about the product and product tier",
    )
    policy_terms = QuoteTermsSerializer(
        help_text="Terms and conditions of the insurance policy"
    )

    class Meta:
        fields = [
            "quote_code",
            "purchase_id",
            "provider_information",
            "coverages",
            "additional_metadata",
            "policy_terms",
        ]

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        # Extract the pricing information using Price model ('premium')
        # from the Quote instance
        representation["pricing"] = QuotePricingSerializer(
            {
                "currency": instance.premium.currency,
                "base_premium": instance.premium.amount,
                "discount_amount": instance.premium.discount_amount or 0,
                "total_amount_for_quotation": instance.base_price,
            }
        ).data

        return representation


class QuoteResponseSerializerV2(serializers.ModelSerializer):
    provider = serializers.CharField()
    product = serializers.CharField(source="product.name")
    product_type = serializers.CharField(source="product.product_type")
    premium = serializers.DecimalField(
        source="premium.amount", max_digits=10, decimal_places=2
    )

    class Meta:
        model = Quote
        fields = [
            "quote_code",
            "provider",
            "product",
            "product_type",
            "base_price",
            "premium",
            "purchase_id",
            "additional_metadata",
        ]
