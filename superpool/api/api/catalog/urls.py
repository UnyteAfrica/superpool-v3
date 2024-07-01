import typing

from django.urls import path

from .views import PolicyListView, ProductListView

if typing.TYPE_CHECKING:
    from django.urls import URLPattern, URLResolver

urlpatterns: typing.List[typing.Union["URLPattern", "URLResolver"]] = [
    path("products", ProductListView.as_view(), name="product-list"),
    path("policies", PolicyListView.as_view(), name="policy-list"),
]
