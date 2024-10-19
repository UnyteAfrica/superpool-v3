from rest_framework import serializers

from core.models import Application


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
            "hashed_key",
        ]

    def validate(self, attrs: dict) -> dict:
        merchant = self.context["request"].user.merchant
        test_mode = attrs.get("test_mode")

        # Check for existing applications
        existing_applications = Application.objects.filter(merchant=merchant)
        if test_mode and existing_applications.filter(test_mode=True).exists():
            raise serializers.ValidationError(
                "A sandbox environment already exists for this merchant."
            )
        if not test_mode and existing_applications.filter(test_mode=False).exists():
            raise serializers.ValidationError(
                "A production environment already exists for this merchant."
            )
        return attrs

    def create(self, validated_data: dict) -> Application:
        application = Application.objects.create(**validated_data)
        application.generate_api_key()
        return application


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
