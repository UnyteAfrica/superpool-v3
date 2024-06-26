from django.contrib.auth import get_user_model
from django.db.models import fields
from django.db.models.functions import FirstValue
from phonenumber_field.serializerfields import PhoneNumberField
from rest_framework import serializers

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """
    This is full serializer is may be used to perform CRUD operations on the User model.

    The User model is a custom model that extends the AbstractUser model.
    """

    class Meta:
        model = User
        exclude = ("password",)
        extra_kwargs = {
            "id": {"read_only": True},
            "password": {"write_only": True},
            "is_staff": {"read_only": True},
            "is_active": {"read_only": True},
            "has_completed_verification": {"read_only": True},
        }


class ScopedUserSerializer(serializers.ModelSerializer):
    """
    Exposes only the necessary fields that can be shared about
    a user to the public.
    """

    class Meta:
        model = User
        fields = ("id", "first_name", "last_name", "email")
        extra_kwargs = {
            "id": {"read_only": True},
        }


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

    name = serializers.CharField(min_length=2, max_length=30)
    email = serializers.EmailField()
    password = serializers.CharField()
