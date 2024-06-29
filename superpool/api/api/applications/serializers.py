from core.models import Application
from rest_framework import serializers


class ApplicationSerializer(serializers.ModelSerializer):
    """
    Serializer for Application model

    e.g:

        {
            "merchant_id": 1,
            "name": "My Application",
            "test_mode": false,
        }
    """

    class Meta:
        model = Application
        fields = "__all__"


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
