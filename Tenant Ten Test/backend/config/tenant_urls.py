from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.accounting.views import AccountingEntryViewSet
from apps.crm.views import LeadViewSet
from apps.customers.views import TenantFeatureAPIView
from apps.manufacturing.views import WorkOrderViewSet

router = DefaultRouter()
router.register("accounting/entries", AccountingEntryViewSet, basename="accounting-entry")
router.register("crm/leads", LeadViewSet, basename="crm-lead")
router.register("manufacturing/work-orders", WorkOrderViewSet, basename="manufacturing-work-order")

urlpatterns = [
    path("api/tenant/features/", TenantFeatureAPIView.as_view(), name="tenant-features"),
    path("api/", include(router.urls)),
]
