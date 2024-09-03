from django.urls import URLPattern, URLResolver, include, path
from rest_framework.routers import DefaultRouter

from .applications.views import (
    ApplicationView,
    create_application_view,
    ApplicationViewSetV2,
)
from .merchants.views import MerchantViewList, MerchantViewSet
from .user import urls as user_route
from .user.views import MerchantLoginView
from .views import (
    MerchantSetPasswordView,
    VerificationAPIView,
    InsurerAPIView,
    InsuranceProviderDetailView,
    InsuranceProviderSearchView,
    PasswordResetView,
    PasswordResetConfirmView,
)

router = DefaultRouter()
router.register(r"sandbox", ApplicationViewSetV2, basename="application")
# router.register(r"merchants", MerchantViewSet, basename="merchant")

urlpatterns = [
    # path("", user_route),
    # path("", include(user_route), name="user"),
    path("internal/auth/", include(user_route), name="auth"),
    path("auth/merchant/login/", MerchantLoginView.as_view(), name="merchant_login"),
    path(
        "auth/merchant/registration/",
        MerchantSetPasswordView.as_view(),
        name="complete_merchant_registration",
    ),
    path(
        "auth/merchant/forgot-password/",
        PasswordResetView.as_view(),
        name="password-reset",
    ),
    path(
        "auth/merchant/reset-password/<str:tenant_id_b64>/<str:token>/",
        PasswordResetConfirmView.as_view(),
        name="password-reset-confirm",
    ),
    # path("sandbox/", ApplicationView.as_view(), name="sandbox_application"),
    # path("sandbox/create/", create_application_view, name="sandbox_create_application"),
    path(
        "merchants",
        MerchantViewList.as_view({"get": "list"}),
        name="list_merchants",
    ),
    path(
        "merchants/<str:short_code>/verify/",
        VerificationAPIView.as_view(),
        name="verify_merchant",
    ),
    # path("", include("api.merchants.urls"), name="merchants"),
    # path("merchants", MerchantViewSet.as_view({"get": "list"}), name="merchants"),  # noqa
    path("", include("api.catalog.urls"), name="catalog"),
    path("", include("api.claims.urls"), name="claims"),
    path("insurers/", InsurerAPIView.as_view(), name="insurers"),
    path(
        "insurers/<str:name>/",
        InsuranceProviderDetailView.as_view(),
        name="insurer-detail",
    ),
    path(
        "providers/search/",
        InsuranceProviderSearchView.as_view(),
        name="insurance-providers-search",
    ),
    # TODO: path('insurers/<str:name>/products/', InsurerAPIView.as_view(), name='insurer_products'),
]

urlpatterns += router.urls
