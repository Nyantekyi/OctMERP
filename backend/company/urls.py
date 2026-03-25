from rest_framework.routers import DefaultRouter

from .views import (
    BusinessTypeViewSet,
    CompanyViewSet,
    IndustryViewSet,
    PaymentClassViewSet,
)

router = DefaultRouter()
router.register('industries', IndustryViewSet, basename='industry')
router.register('payment-classes', PaymentClassViewSet, basename='payment-class')
router.register('business-types', BusinessTypeViewSet, basename='business-type')
router.register('companies', CompanyViewSet, basename='company')

urlpatterns = router.urls