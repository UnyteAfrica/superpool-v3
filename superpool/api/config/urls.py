from django.contrib import admin
from django.urls import path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

ROUTE_PREFIX = "api"
DOCS_PREFIX = "docs"

urlpatterns = [
    path("admin/", admin.site.urls),
]

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
]

urlpatterns += swagger_urlpatterns
