import logging
from django.contrib.auth import get_user_model
from django.db.models import fields
from django.db.models.functions import FirstValue
from phonenumber_field.serializerfields import PhoneNumberField
from rest_framework import serializers
from core.user.models import CustomerSupport, Admin
from django.db import IntegrityError, transaction

User = get_user_model()

logger = logging.getLogger(__name__)


class UserSerializer(serializers.ModelSerializer):
    """
    This is full serializer is may be used to perform CRUD operations on the User model.

    The User model is a custom model that extends the AbstractUser model.
    """

    class Meta:
        model = User
        fields = (
            "first_name",
            "last_name",
            "email",
            "password",
            "role",
        )
        extra_kwargs = {
            "password": {"write_only": True},
            "first_name": {"required": True},
            "last_name": {"required": True},
            "email": {"required": True},
            "role": {"required": True},
        }

    def validate(self, attrs):
        """
        This method is used to validate the data sent by the user.
        """
        email = attrs.get("email")
        role = attrs.get("role")

        if role not in User.USER_TYPES.values:
            raise serializers.ValidationError({"role": "Invalid role"})

        # Check if the email already exists
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError(
                {"username": "This username is already taken."}
            )

        return attrs

    def create(self, validated_data):
        role = validated_data.get("role")

        try:
            with transaction.atomic():
                user = User(
                    email=validated_data["email"],
                    first_name=validated_data["first_name"],
                    last_name=validated_data["last_name"],
                    role=role,
                )
                user.set_password(validated_data["password"])
                user.save()

                # Create related profiles
                if role == User.USER_TYPES.SUPPORT:
                    CustomerSupport.objects.create(user=user)
                elif role == User.USER_TYPES.ADMIN:
                    Admin.objects.create(user=user)
        except IntegrityError as err:
            logger.error(f"IntegrityError: {str(e)}")
            raise serializers.ValidationError({"detail": "Integrity error occurred."})
        except Exception as e:
            logger.error(f"Exception: {str(e)}")
            raise serializers.ValidationError({"detail": str(e)})

        return user


class AdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = Admin
        fields = ("is_admin", "is_superuser")


class CustomerSupportSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerSupport
        fields = ("is_staff",)


class ScopedUserSerializer(serializers.ModelSerializer):
    """
    Exposes only the necessary fields that can be shared about
    a user to the public.
    """

    admin_profile = AdminSerializer(source="admin_user", read_only=True)
    support_profile = CustomerSupportSerializer(source="support_user", read_only=True)

    class Meta:
        model = User
        fields = (
            "first_name",
            "last_name",
            "email",
            "role",
            "admin_profile",
            "support_profile",
        )


class UserSignupSerializer(serializers.Serializer):
    """
    This serializer is used to validate the data sent by the user when signing up.
    """

    first_name = serializers.CharField(
        min_length=2, max_length=40, help_text="First name or given name of the user"
    )
    last_name = serializers.CharField(
        min_length=2, max_length=40, help_text="Surname or Family name of the user"
    )
    email = serializers.EmailField(
        help_text="By default, email address is going to be the username"
    )

    has_read_terms = serializers.BooleanField(
        help_text="User must agree to the terms and conditions, and privacy policy"
    )


class UserAccountSerializer(serializers.Serializer):
    """
    This serializer is used to validate the user data displayed on the user account page.

    Note: THis should be kept in sync with `UserSerializer`
    """

    first_name = serializers.CharField(
        min_length=2, max_length=40, help_text="First name of the user"
    )

    has_completed_verification = serializers.BooleanField(
        help_text="User must complete KYC verification, before they can access the platform"
    )

    phone_number = PhoneNumberField(region="NG", help_text="Phone number of the user")


class UserAuthSerializer(serializers.Serializer):
    """
    Authentication Serializer that should only be used for authentication purposes only
    """

    email = serializers.EmailField()
    password = serializers.CharField()


class MerchantAuthSerializer(serializers.Serializer):
    """
    Authentication serializer for merchants
    """

    tenant_id = serializers.UUIDField()
    password = serializers.CharField(write_only=True)


class CustomerInformationSerializer(serializers.ModelSerializer):
    """
    Formats the full information displayed about a merchant's customer
    """

    customer_id = serializers.PrimaryKeyRelatedField()
    full_name = serializers.CharField(source="full_name")
    customer_email = serializers.EmailField(source="email")
    customer_phone = serializers.CharField(source="phone_number")
    date_of_birth = serializers.DateField(format="%Y-%m-%D", source="dob")
    purchased_policies = serializers.SerializerMethodField()
    active_policies = serializers.SerializerMethodField()
    active_claims = serializers.SerializerMethodField()

    class Meta:
        model = Customer
        fields = [
            "customer_id",
            "full_name",
            "customer_email",
            "customer_phone",
            "date_of_birth",
            "address",
            "purchased_policies",
            "active_policies",
            "active_claims",
        ]
        read_only_fields = fields

    def get_active_claims(self, obj) -> dict:
        claims = obj.claims.filter(status="active")
        return CustomerClaimSerializer(claims, many=True).data

    def get_active_policies(self, obj) -> dict:
        active_policies = obj.policies.filter(status="active")
        return CustomerPolicySerializer(active_policies, many=True).data

    def get_purchase_policies(self, obj) -> dict:
        policies = obj.policies.all()
        return CustomerPolicySerializer(policies, many=True).data


class CustomerPolicySerializer(serializers.ModelSerializer):
    start_date = serializers.DateField(source="effective_from", format="%Y-%m-%d")
    end_date = serializers.DateField(source="effective_through", format="%Y-%m-%d")
    policy_type = serializers.CharField(source="product.product_type")
    premium_amount = serializers.DecimalField(
        source="premium", max_digits=10, decimal_places=2
    )

    class Meta:
        model = Policy
        fields = [
            "policy_id",
            "policy_type",
            "status",
            "start_date",
            "end_date",
            "premium_amount",
        ]


class CustomerClaimSerializer(serializers.ModelSerializer):
    claim_id = serializers.PrimaryKeyRelatedField(source="id")
    policy_id = serializers.UUIDField(source="policy.policy_id")
    claim_status = serializers.CharField(source="status")
    claim_amount = serializers.DecimalField(
        source="amount", max_digits=10, decimal_places=2, min_value=Decimal(0.00)
    )
    date_filed = serializers.DateField(format="%Y-%m-%d", source="claim_date")
    date_resolved = serializers.DateField(format="%Y-%m-%d")

    class Meta:
        model = Claim
        fields = [
            "claim_id",
            "policy_id",
            "claim_status",
            "claim_amount",
            "date_filed",
            "date_resolved",
        ]
        read_only_fields = fields


class CustomerSummarySerializer(serializers.ModelSerializer):
    """
    Basic information serializer about a customer

    Effective use-case: Listing of customers
    """

    customer_id = serializers.PrimaryKeyRelatedField(read_only=True)
    full_name = serializers.CharField()
    customer_email = serializers.EmailField()
    customer_phone = serializers.CharField(source="phone_number")

    class Meta:
        model = Customer
        fields = ["customer_id", "full_name", "customer_email", "customer_phone"]
        read_only_fields = fields
