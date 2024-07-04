import pytest
from api.merchants.services import MerchantService
from core.merchants.errors import MerchantAlreadyExists as MerchantAlreadyExistError

from .factories import MerchantFactory


@pytest.mark.django_db
class TestMerchantService:
    def test_register_merchant(self):
        test_data = {
            "name": "Test Merchant",
            "short_code": "TST-001",
            "business_email": "",
        }
        merchant = MerchantFactory.build(**test_data)
        service = MerchantService()
        merchant, response_data = service.register(merchant)

        assert merchant is not None
        assert (
            merchant.short_code is not None
            and merchant.short_code == test_data["short_code"]
        )
        assert merchant.name == test_data["name"]
        assert merchant.business_email == test_data["business_email"]
        assert response_data["message"] == "Merchant created successfully"

    def merchant_already_exist_raises_error(self):
        merchant = MerchantFactory()
        service = MerchantService()

        with pytest.raises(MerchantAlreadyExistError) as error:
            service.register(merchant)

        # assert error.value.message == "Merchant already exist"
