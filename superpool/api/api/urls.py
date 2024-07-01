from django.urls import URLPattern, URLResolver, include, path

from .applications.views import ApplicationView, create_application_view
from .user import urls as user_route

urlpatterns = [
    # path("", user_route),
    path("", include(user_route), name="user"),
    path("sandbox/", ApplicationView.as_view(), name="sandbox_application"),
    path("sandbox/create/", create_application_view, name="sandbox_create_application"),
    path("merchants/", include("api.merchants.urls"), name="merchants"),
    path("", include("api.catalog.urls"), name="catalog"),
]
