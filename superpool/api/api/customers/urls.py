from django.urls import include, path
from rest_framework.routers import DefaultRouter
from api.customers.views import CustomerViewSet, MerchantCustomerViewSet


router = DefaultRouter(trailing_slash=False)
router.register(
    r"merchants/(?P<str:tenant_id>[^/.]+)/customers",
    MerchantCustomerViewSet,
    basename="customers",
)

urlpatterns = []

urlpatterns += router.urls
