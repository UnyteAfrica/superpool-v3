import abc
from collections.abc import Mapping, MutableMapping

from api.merchants.serializers import CreateMerchantSerializer, MerchantSerializer
from core.merchants.errors import (
    MerchantAlreadyExists,
    MerchantObjectDoesNotExist,
    MerchantUpdateError,
)
from core.merchants.models import Merchant
from core.utils import generate_verification_token, send_verification_email
from rest_framework.serializers import Serializer


class IMerchantRegistry(abc.ABC):
    @abc.abstractmethod
    def register(self, data: dict, *kwargs: Mapping) -> Merchant:
        """
        Interface method to register a new merchant
        """
        pass

    def deactivate(self, merchant_id: Merchant):
        """
        Interface to deactivate a given merchant
        """
        pass

    def update_profile(self, merchant_id: str, data: MutableMapping) -> Merchant:
        """
        Interface to update a merchant details
        """
        pass


class MerchantService(IMerchantRegistry):
    def register(
        self, data: dict, **kwargs: Mapping
    ) -> Merchant | tuple[Merchant, dict]:
        """
        Registers a new merchant on the platform
        """
        serializer_class = kwargs.pop("serializer_class", CreateMerchantSerializer)
        serializer = serializer_class(data=data)
        if serializer.is_valid():
            merchant = serializer.save()
            verification_token = generate_verification_token(merchant)
            send_verification_email(merchant, verification_token)

            return merchant, {"message": "Merchant registered successfully"}
        return MerchantAlreadyExists, serializer.errors

    def update_profile(
        self, merchant_id: str, data: MutableMapping
    ) -> Merchant | tuple[Merchant, dict]:
        """
        Updates a merchant profile with the given data
        """
        try:
            # grab the merchant instance
            merchant = Merchant.objects.get(id=merchant_id)
        except Merchant.DoesNotExist:
            raise MerchantObjectDoesNotExist

        serializer_class = MerchantSerializer
        serializer = serializer_class(merchant, data=data, partial=True)
        if serializer.is_valid():
            updated_merchant = serializer.save()
            return updated_merchant
        return MerchantUpdateError, serializer.errors

    def deactivate(self, merchant_id: Merchant):
        """
        Deactivates a given merchant
        """
        try:
            merchant = Merchant.objects.get(id=merchant_id)
            merchant.is_active = False
        except Merchant.DoesNotExist:
            raise MerchantObjectDoesNotExist
        merchant.save()
        return merchant
