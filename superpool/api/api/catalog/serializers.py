from core.catalog.models import Policy, Price, Product, Quote
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

    class Meta:
        model = Policy
        depth = 1
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
        ]
        extra_kwargs = {
            "policy_id": {"read_only": True},
            "merchant_id": {"read_only": True},
            "provider_id": {"read_only": True},
        }


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


class PriceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Price
        exclude = ["id"]


class QuoteSerializer(serializers.ModelSerializer):
    price = PriceSerializer(source="premium")
    product = ProductSerializer()
    quote_expiry_date = serializers.DateTimeField(source="expires_in", read_only=True)

    class Meta:
        model = Quote
        fields = ["quote_code", "base_price", "product", "quote_expiry_date", "price"]
        extra_kwargs = {"quote_code": {"read_only": True}}

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


class PolicyPurchaseSerializer(serializers.Serializer):
    """
    Issues a new policy based on CustomerDetails and some
    other metadata
    """

    customer_details = serializers.JSONField()
    category = serializers.CharField()
    product_id = serializers.UUIDField()
    coverage_id = serializers.UUIDField()
    merchant_id = serializers.UUIDField()
    provider_id = serializers.UUIDField()
    renewable = serializers.BooleanField(required=False)
    inspection_required = serializers.BooleanField(required=False)
    certification_required = serializers.BooleanField(required=False)
