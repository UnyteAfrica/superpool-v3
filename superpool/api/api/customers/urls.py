from rest_framework.routers import DefaultRouter

from api.customers.views import CustomerViewSet, MerchantCustomerViewSet

router = DefaultRouter()
router.register(
    r"merchants/(?P<tenant_id>[^/.]+)/customers",
    MerchantCustomerViewSet,
    basename="customers",
)
router.register("customers", CustomerViewSet, basename="base-customer")

urlpatterns = [
    # path(
    #     "customers",
    #     CustomerViewSet.as_view({"list": "get"}),
    #     name="admin-customers-list",
    # ),
]

urlpatterns += router.urls
