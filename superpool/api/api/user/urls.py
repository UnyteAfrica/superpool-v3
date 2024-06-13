from django.urls import path

from .views import SignInView, SignUpView

urlpatterns = [
    path("auth/register/", SignUpView.as_view(), name="signup"),
    path("auth/signin/", SignInView.as_view(), name="signin"),
]
