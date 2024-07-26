import typing

from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    PolicyAPIViewSet,
    ProductListView,
    ProductView,
    QuoteAPIViewSet,
    QuoteDetailView,
    QuoteListView,
)

router = DefaultRouter()

router.register(r"policies", PolicyAPIViewSet, basename="policy")
router.register(r"quotations", QuoteAPIViewSet, basename="quotation")

if typing.TYPE_CHECKING:
    from django.urls import URLPattern, URLResolver

urlpatterns: typing.List[typing.Union["URLPattern", "URLResolver"]] = [
    path("products", ProductListView.as_view(), name="product-list"),
    path(
        "products/<uuid:product_id>",
        ProductView.as_view(),
        name="product-detail",
    ),
    # path("", include(router.urls)),
    path(
        "policies/<uuid:pk>/",
        PolicyAPIViewSet.as_view({"get": "retrieve"}),
        name="policy-detail",
    ),
    path(
        "policies/search/",
        PolicyAPIViewSet.as_view({"get": "search"}),
        name="policy-search",
    ),
    path(
        "quotes/request/<str:product_name>/", QuoteListView.as_view(), name="quote-list"
    ),
    path("quotes/<str:quote_code>/", QuoteDetailView.as_view(), name="quote-detail"),
    # path(
    #     "policies/purchase/",
    #     PolicyAPIViewSet.as_view({"post": "purchase"}),
    #     name="policy-purchase",
    # ),
    # path(
    #     "policies/renew/",
    #     PolicyAPIViewSet.as_view({"post": "renew"}),
    #     name="policy-renew",
    # ),
]
