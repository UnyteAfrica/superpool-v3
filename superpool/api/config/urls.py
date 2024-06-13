from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

ROUTE_PREFIX = "api"
DOCS_PREFIX = "docs"

urlpatterns = [
    path("admin/", admin.site.urls),
]

api_v1_urlpatterns = [
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
    path(f"{ROUTE_PREFIX}/v1/users/", include("user.urls")),
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
        name="v1-swagger-ui",
    ),
    path(
        f"{ROUTE_PREFIX}/{DOCS_PREFIX}/redoc/",
        SpectacularSwaggerView.as_view(),
        name="redoc",
    ),
]

urlpatterns += swagger_urlpatterns
