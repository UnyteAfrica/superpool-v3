from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api.merchants.views import MerchantAPIViewsetV2, MerchantUpdateView

v2_router = DefaultRouter()
v2_router.register(r"merchants", MerchantAPIViewsetV2, basename="merchant-v2")


urlpatterns = [
    path(
        "merchants/<uuid:tenant_id>/",
        MerchantUpdateView.as_view(),
        name="merchant-info-update",
    ),
    path("", include(v2_router.urls)),
]
