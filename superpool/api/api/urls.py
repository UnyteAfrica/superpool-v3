from django.urls import URLPattern, URLResolver, include, path
from rest_framework.routers import DefaultRouter

from .applications.views import ApplicationView, create_application_view
from .merchants.views import MerchantViewList, MerchantViewSet
from .user import urls as user_route

router = DefaultRouter()
router.register(r"merchants", MerchantViewSet, basename="merchant")

urlpatterns = [
    # path("", user_route),
    path("", include(user_route), name="user"),
    path("sandbox/", ApplicationView.as_view(), name="sandbox_application"),
    path("sandbox/create/", create_application_view, name="sandbox_create_application"),
    path(
        "merchants",
        MerchantViewList.as_view({"get": "list"}),
        name="list_merchants",
    ),
    # path("", include("api.merchants.urls"), name="merchants"),
    path("", include("api.catalog.urls"), name="catalog"),
]

urlpatterns += router.urls
