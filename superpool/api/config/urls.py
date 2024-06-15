from typing import Union

from django.contrib import admin
from django.urls import URLPattern, URLResolver, include, path
from drf_spectacular.views import (SpectacularAPIView, SpectacularRedocView,
                                   SpectacularSwaggerView)
from rest_framework_simplejwt.views import (TokenObtainPairView,
                                            TokenRefreshView, TokenVerifyView)

ROUTE_PREFIX = "api"
DOCS_PREFIX = "docs"

urlpatterns: list[Union[URLPattern, URLResolver]] = [
    path("admin/", admin.site.urls),
    path(
        f"{ROUTE_PREFIX}/token/",
        TokenObtainPairView.as_view(),
        name="token_obtain_pair",
    ),
    path(
        f"{ROUTE_PREFIX}/token/refresh/",
        TokenRefreshView.as_view(),
        name="token_refresh",
    ),
    path(
        f"{ROUTE_PREFIX}/token/verify/",
        TokenVerifyView.as_view(),
        name="token_verify",
    ),
]

api_v1_urlpatterns = [
    path(f"{ROUTE_PREFIX}/v1/users/", include("api.urls")),
]


urlpatterns += api_v1_urlpatterns

swagger_urlpatterns = [
    path(
        f"{ROUTE_PREFIX}/{DOCS_PREFIX}/schema/",
        SpectacularAPIView.as_view(),
        name="schema",
    ),
    path(
        f"{ROUTE_PREFIX}/{DOCS_PREFIX}/swagger/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger",
    ),
    path(
        f"{ROUTE_PREFIX}/{DOCS_PREFIX}/redoc/",
        SpectacularRedocView.as_view(),
        name="redoc",
    ),
]

urlpatterns += swagger_urlpatterns
