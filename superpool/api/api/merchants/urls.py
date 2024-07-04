from api.merchants.views import MerchantViewList, MerchantViewSet
from django.urls import include, path
from rest_framework.routers import DefaultRouter

router = DefaultRouter()

router.register(r"", MerchantViewSet, basename="merchants")


urlpatterns = [
    path(
        "",
        MerchantViewList.as_view({"get": "list"}),
        name="list_merchants",
    ),
    path("", include(router.urls)),
]
