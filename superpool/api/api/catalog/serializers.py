from core.catalog.models import Policy, Product
from django.db.models import fields
from rest_framework import serializers
from rest_framework.serializers import ModelSerializer


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

    purchase_link = serializers.URLField(source="get_purchase_link", read_only=True)

    class Meta:
        model = Policy
        fields = [
            "policy_id",
            "product",
            "policy_holder",
            "effective_from",
            "effective_through",
            "premium",
            "coverage",
            "merchant_id",
            "provider_id",
            "renewable",
            "inspection_required",
            "cerfication_required",
            "purchase_link",
        ]
        extra_kwargs = {
            "policy_id": {"read_only": True},
            "merchant_id": {"read_only": True},
            "provider_id": {"read_only": True},
        }

        def get_purchase_link(self, obj):
            # This method is used to get the purchase link for the policy
            # TODO: generate a purchase link for the policy based on the policy ID
            pass


class CreatePolicySerializer(ModelSerializer):
    """
    Serializer for creating a Policy model

    This serializer is used to create a new policy

    """

    class Meta:
        model = Policy
        fields = (
            "name",
            "policy_holder",
            "premium",
            "coverage",
            "merchant_id",
            "provider_id",
            "renewable",
        )
        exclude = ("cerfication_required", "inspection_required")
