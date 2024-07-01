from api.merchants.views import MerchantViewList, MerchantViewSet
from django.urls import include, path
from rest_framework.routers import DefaultRouter

router = DefaultRouter()

router.register(r"merchants", MerchantViewSet, basename="merchants")


urlpatterns = [
    path(
        "merchants",
        MerchantViewList.as_view({"get": "list"}),
        name="list_merchants",
    ),
    path("", include(router.urls)),
]
