import typing

from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    PolicyAPIViewSet,
    PolicyCancellationView,
    PolicyPurchaseView,
    ProductListView,
    ProductRetrieveView,
    QuoteAPIViewSet,
    QuoteDetailView,
    QuoteListView,
    RequestQuoteView,
    ProductCoverageListView,
    ProductCoverageRetrieveView,
    ProductCoverageSearchView,
)

router = DefaultRouter()

router.register(r"policies", PolicyAPIViewSet, basename="policy")

if typing.TYPE_CHECKING:
    from django.urls import URLPattern, URLResolver

urlpatterns: typing.List[typing.Union["URLPattern", "URLResolver"]] = [
    path("products", ProductListView.as_view(), name="product-list"),
    path(
        "products/<uuid:pk>/",
        ProductRetrieveView.as_view(),
        name="product-detail-by-id",
    ),
    path(
        "products/<str:product_name>/",
        ProductRetrieveView.as_view(),
        name="product-detail-by-name",
    ),
    path(
        "products/<uuid:product_id>/coverages/",
        ProductCoverageListView.as_view(),
        name="product-coverages-list",
    ),
    path(
        "products/<uuid:product_id>/coverages/<str:coverage_id>/",
        ProductCoverageRetrieveView.as_view(),
        name="product-coverages-detail",
    ),
    path(
        "coverages/search/",
        ProductCoverageSearchView.as_view(),
        name="product-coverages-search",
    ),
    path("policies", PolicyPurchaseView.as_view(), name="purchase-policy"),
    path("policies/cancel", PolicyCancellationView.as_view(), name="policy-cancel"),
    path("quotes", RequestQuoteView.as_view(), name="request-quote"),
    path("quotes/<str:quote_code>/", QuoteDetailView.as_view(), name="quote-detail"),
]

urlpatterns += router.urls
