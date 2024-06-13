from django.urls import include, path

from .user import urls as user_route

urlpatterns = [
    path("", user_route),
]
