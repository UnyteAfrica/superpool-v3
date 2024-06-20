from django.urls import URLPattern, URLResolver, include, path

urlpatterns: URLPattern | URLResolver = []

merchant_urlpatterns = []

urlpatterns += merchant_urlpatterns
