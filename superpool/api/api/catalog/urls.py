import typing

from django.urls import include, path

from .views import PolicyListView, ProductListView, ProductView

if typing.TYPE_CHECKING:
    from django.urls import URLPattern, URLResolver

urlpatterns: typing.List[typing.Union["URLPattern", "URLResolver"]] = [
    path("products", ProductListView.as_view(), name="product-list"),
    path(
        "products/<uuid:product_id>",
        ProductView.as_view(),
        name="product-detail",
    ),
    path("policies", PolicyListView.as_view(), name="policy-list"),
]
