from core.models import Application
from rest_framework import serializers


class ApplicationSerializer(serializers.ModelSerializer):
    """
    Serializer for the Application model

    e.g:

        {
            "merchant_id": 1,
            "name": "My Application",
            "test_mode": false,
        }
    """

    class Meta:
        model = Application
        exclude = ["pk"]
        read_only_fields = ["pk"]


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
