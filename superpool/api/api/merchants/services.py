import abc
from collections.abc import Callable, Mapping, MutableMapping
from typing import Optional

from api.merchants.serializers import CreateMerchantSerializer, MerchantSerializer
from core.merchants.errors import (
    MerchantAlreadyExists,
    MerchantObjectDoesNotExist,
    MerchantUpdateError,
)
from core.merchants.models import Merchant
from rest_framework.serializers import Serializer, ValidationError


class IMerchantRegistry(abc.ABC):
    @abc.abstractmethod
    def register_merchant(
        self,
        data: dict,
        *kwargs: dict,
    ) -> Merchant:
        """
        Interface method to register a new merchant
        """
        pass

    @abc.abstractmethod
    def deactivate(self, merchant_id: str):
        """
        Interface to deactivate a given merchant
        """
        pass

    @abc.abstractmethod
    def retrieve_merchant(self, merchant_id: str) -> Optional[Merchant]:
        """
        Interface to retrieve a merchant details
        """
        pass

    @abc.abstractmethod
    def update_merchant(self, merchant_id: str, data: dict) -> Merchant:
        """
        Interface to update a merchant details
        """
        pass


class MerchantService(IMerchantRegistry):
    def register_merchant(self, data: dict, **kwargs: dict) -> Merchant:
        """
        Registers a new merchant on the platform
        """
        from core.utils import generate_verification_token, send_verification_email

        serializer_class = kwargs.pop("serializer_class", CreateMerchantSerializer)
        serializer = serializer_class(data=data)
        if serializer.is_valid():
            if Merchant.objects.filter(business_email=data["business_email"]).exists():
                raise MerchantAlreadyExists

            merchant = serializer.save()
            verification_token = generate_verification_token()
            send_verification_email(
                merchant.business_email, verification_token, merchant.short_code
            )

            return merchant
        raise ValidationError(serializer.errors)

    def update_merchant(self, merchant_id: str, data: MutableMapping) -> Merchant:
        """
        Updates a merchant profile with the given data
        """
        try:
            # grab the merchant instance
            merchant = Merchant.objects.get(pk=merchant_id)
        except Merchant.DoesNotExist:
            raise MerchantObjectDoesNotExist

        serializer_class = MerchantSerializer
        serializer = serializer_class(merchant, data=data, partial=True)
        if serializer.is_valid():
            return serializer.save()
        raise MerchantUpdateError(serializer.errors)

    def deactivate(self, merchant_id: Merchant):
        """
        Deactivates a given merchant
        """
        try:
            merchant = Merchant.objects.get(pk=merchant_id)
            merchant.is_active = False
            merchant.save()
            return merchant
        except Merchant.DoesNotExist:
            raise MerchantObjectDoesNotExist

    def retrieve_merchant(self, merchant_id: str) -> Optional[Merchant]:
        """
        Retrieves a merchant details
        """
        try:
            return Merchant.objects.filter(pk=merchant_id)
        except Merchant.DoesNotExist:
            raise MerchantObjectDoesNotExist
