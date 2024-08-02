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
    # path("", include(router.urls)),
    path("policies", PolicyPurchaseView.as_view(), name="purchase-policy"),
    path("policies/cancel", PolicyCancellationView.as_view(), name="policy-cancel"),
    # path(
    #     "policies/<uuid:pk>/",
    #     PolicyAPIViewSet.as_view({"get": "retrieve"}),
    #     name="policy-detail",
    # ),
    # path(
    #     "policies/search/",
    #     PolicyAPIViewSet.as_view({"get": "search"}),
    #     name="policy-search",
    # ),
    path("quotes", RequestQuoteView.as_view(), name="request-quote"),
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

urlpatterns += router.urls
