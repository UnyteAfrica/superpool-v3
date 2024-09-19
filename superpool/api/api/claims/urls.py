from rest_framework.routers import DefaultRouter

from .views import ClaimsViewSet

router = DefaultRouter()

router.register(r"claims", ClaimsViewSet, basename="claims")

urlpatterns = []
urlpatterns += router.urls
