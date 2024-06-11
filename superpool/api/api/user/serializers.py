from core.user.models import UserProfile
from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """
    This is full serializer is may be used to perform CRUD operations on the User model.

    The User model is a custom model that extends the AbstractUser model.
    """

    class Meta:
        model = User
        fields = (
            "id",
            "first_name",
            "last_name",
            "email",
            "phone_number",
            "username",
            "date_joined",
            "is_staff",
            "is_active",
        )

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
