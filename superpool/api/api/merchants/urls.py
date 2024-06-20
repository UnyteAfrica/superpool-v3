from django.urls import URLPattern, URLResolver, include, path

from .views import create_application_view

urlpatterns: URLPattern | URLResolver = []

merchant_urlpatterns = [
    path("create-application", create_application_view, name="create-application")
]

urlpatterns += merchant_urlpatterns
