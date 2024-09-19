import pytest
from django.contrib.auth.models import Group

from core.merchants.models import Merchant
from core.user.models import Admin, CustomerSupport

from .factories import UserFactory


@pytest.fixture
def support_group():
    return Group.objects.create(name="CustomerSupport")


@pytest.fixture
def merchant_group():
    return Group.objects.create(name="Merchant")


@pytest.fixture
def admin_group():
    return Group.objects.create(name="Admin")


@pytest.mark.django_db
def test_assign_permissions_to_support_group(support_group):
    user = UserFactory()
    support = CustomerSupport.objects.create(user=user)

    assert support.user.groups.filter(name="CustomerSupport").exists()


@pytest.mark.django_db
def test_assign_permissions_to_merchant_group(merchant_group):
    user = UserFactory()
    merchant = Merchant.objects.create(user=user)

    assert merchant.user.groups.filter(name="Merchant").exists()


@pytest.mark.django_db
def test_assign_permissions_to_admin_group(admin_group):
    user = UserFactory()
    admin = Admin.objects.create(user=user)

    assert admin.user.groups.filter(name="Admin").exists()
