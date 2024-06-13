from django.urls import path

from .views import SignInView, SignUpView

urlpatterns = [
    path("register/", SignUpView.as_view(), name="signup"),
    path("signin/", SignInView.as_view(), name="signin"),
]
