from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.tenancy.api.views import TenantDomainViewSet, TenantViewSet

router = DefaultRouter()
router.register("tenants", TenantViewSet, basename="tenant")
router.register("domains", TenantDomainViewSet, basename="tenant-domain")

urlpatterns = [path("", include(router.urls))]
