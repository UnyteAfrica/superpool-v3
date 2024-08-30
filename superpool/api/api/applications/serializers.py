from core.models import Application
from rest_framework import serializers


class ApplicationSerializer(serializers.ModelSerializer):
    """
    Serializes the information of an application environment
    """

    hashed_key = serializers.ReadOnlyField(source="api_key_hash")
    environment_name = serializers.CharField(source="name")

    class Meta:
        model = Application
        fields = ["application_id", "environment_name", "hashed_key", "test_mode"]
        read_only_fields = [
            "application_id",
        ]


class CreateApplicationSerializer(serializers.Serializer):
    """
    Serializer for creating a new application

    e.g:
        {
            "merchant_id": 1,
            "name": "My Application",
        }
    """

    merchant_id = serializers.CharField()
    name = serializers.CharField()
