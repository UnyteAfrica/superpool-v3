from api.merchants.views import MerchantViewList, MerchantViewset
from django.urls import include, path
from rest_framework.routers import DefaultRouter

router = DefaultRouter()

router.register("", MerchantViewset, basename="merchants")


urlpatterns = [
    path(
        "list-merchants/",
        MerchantViewList.as_view({"get": "list"}),
        name="list_merchants",
    ),
    path("", include(router.urls)),
]
