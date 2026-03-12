from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.company.api.views import BusinessTypeViewSet, CompanyViewSet, DomainViewSet, IndustryViewSet, PaymentClassViewSet

router = DefaultRouter()
router.register("industries", IndustryViewSet, basename="industry")
router.register("payment-classes", PaymentClassViewSet, basename="payment-class")
router.register("business-types", BusinessTypeViewSet, basename="business-type")
router.register("companies", CompanyViewSet, basename="company")
router.register("domains", DomainViewSet, basename="domain")

urlpatterns = [path("", include(router.urls))]
