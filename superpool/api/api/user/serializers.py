from django.contrib.auth import get_user_model
from django.db.models import fields
from django.db.models.functions import FirstValue
from phonenumber_field.serializerfields import PhoneNumberField
from rest_framework import serializers
from core.user.models import CustomerSupport, Admin
from django.db import transaction

User = get_user_model()


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
