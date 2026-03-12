from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    BillOfMaterialsViewSet, BOMComponentViewSet,
    WorkCenterViewSet, RoutingViewSet, RoutingStepViewSet,
    WorkOrderViewSet, WorkOrderLineViewSet,
    QualityCheckViewSet, ScrapRecordViewSet,
)

app_name = "manufacturing"

router = DefaultRouter()
router.register("boms", BillOfMaterialsViewSet, basename="bom")
router.register("bom-components", BOMComponentViewSet, basename="bom-component")
router.register("work-centers", WorkCenterViewSet, basename="work-center")
router.register("routings", RoutingViewSet, basename="routing")
router.register("routing-steps", RoutingStepViewSet, basename="routing-step")
router.register("work-orders", WorkOrderViewSet, basename="work-order")
router.register("work-order-lines", WorkOrderLineViewSet, basename="work-order-line")
router.register("quality-checks", QualityCheckViewSet, basename="quality-check")
router.register("scrap-records", ScrapRecordViewSet, basename="scrap-record")

urlpatterns = [path("", include(router.urls))]

