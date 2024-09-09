from django.urls import include, path
from rest_framework.routers import DefaultRouter
from api.customers.views import CustomerViewSet, MerchantCustomerViewSet


router = DefaultRouter()
router.register(
    r"merchants/(?P<tenant_id>[^/.]+)/customers",
    MerchantCustomerViewSet,
    basename="customers",
)

urlpatterns = []

urlpatterns += router.urls
