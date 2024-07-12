from api.merchants.views import MerchantAPIViewsetV2
from django.urls import include, path
from rest_framework.routers import DefaultRouter

v2_router = DefaultRouter()
v2_router.register(r"merchants", MerchantAPIViewsetV2, basename="merchant-v2")


urlpatterns = [
    path("", include(v2_router.urls)),
]
