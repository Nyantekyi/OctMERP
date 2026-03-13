from django.urls import include, path

urlpatterns = [
    path("", include("config.tenant_urls")),
]
