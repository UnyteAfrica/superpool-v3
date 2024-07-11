from api.merchants.views import MerchantAPIViewsetV2, MerchantViewList, MerchantViewSet
from django.urls import include, path
from rest_framework.routers import DefaultRouter

router = DefaultRouter()

router.register(r"merchants", MerchantViewSet, basename="merchant")
router.register(r"merchants-v2", MerchantAPIViewsetV2, basename="merchant-v2")


urlpatterns = [
    path(
        "merchants",
        MerchantViewList.as_view({"get": "list"}),
        name="list_merchants",
    ),
    path("", include(router.urls)),
]
