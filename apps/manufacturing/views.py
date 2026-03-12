"""apps/manufacturing/views.py"""

from rest_framework.response import Response

from apps.common.api import build_action_route, build_model_viewset
from apps.common.permissions import IsTenantUser
from .models import (
    BillOfMaterials,
    BOMComponent,
    QualityCheck,
    Routing,
    RoutingStep,
    ScrapRecord,
    WorkCenter,
    WorkOrder,
    WorkOrderLine,
)
from .serializers import (
    BillOfMaterialsSerializer,
    BOMComponentSerializer,
    QualityCheckSerializer,
    RoutingSerializer,
    RoutingStepSerializer,
    ScrapRecordSerializer,
    WorkCenterSerializer,
    WorkOrderLineSerializer,
    WorkOrderSerializer,
)


def _confirm_work_order(self, request, *args, **kwargs):
    wo = self.get_object()
    wo.status = "confirmed"
    wo.save(update_fields=["status", "updated_at"])
    return Response({"success": True, "data": WorkOrderSerializer(wo).data})


def _start_work_order(self, request, *args, **kwargs):
    from django.utils import timezone

    wo = self.get_object()
    wo.status = "in_progress"
    wo.actual_start = timezone.now()
    wo.save(update_fields=["status", "actual_start", "updated_at"])
    return Response({"success": True, "data": WorkOrderSerializer(wo).data})


def _complete_work_order(self, request, *args, **kwargs):
    from django.utils import timezone

    wo = self.get_object()
    qty = request.data.get("quantity_produced", wo.quantity_planned)
    wo.status = "done"
    wo.actual_end = timezone.now()
    wo.quantity_produced = qty
    wo.save(update_fields=["status", "actual_end", "quantity_produced", "updated_at"])
    return Response({"success": True, "data": WorkOrderSerializer(wo).data})


BillOfMaterialsViewSet = build_model_viewset(
    BillOfMaterials,
    BillOfMaterialsSerializer,
    permission_classes=[IsTenantUser],
    filterset_fields=["product", "variant", "bom_type", "branch", "is_default", "is_active"],
    search_fields=["name"],
    ordering_fields=["version"],
    select_related_fields=["product", "variant", "unit", "branch"],
    prefetch_related_fields=["components"],
)
BOMComponentViewSet = build_model_viewset(
    BOMComponent,
    BOMComponentSerializer,
    permission_classes=[IsTenantUser],
    filterset_fields=["bom", "component", "is_optional"],
    select_related_fields=["bom", "component", "unit"],
)
WorkCenterViewSet = build_model_viewset(
    WorkCenter,
    WorkCenterSerializer,
    permission_classes=[IsTenantUser],
    filterset_fields=["branch", "is_active"],
    search_fields=["name"],
    select_related_fields=["branch", "default_operator"],
)
RoutingViewSet = build_model_viewset(
    Routing,
    RoutingSerializer,
    permission_classes=[IsTenantUser],
    filterset_fields=["bom"],
    search_fields=["name"],
    select_related_fields=["bom"],
    prefetch_related_fields=["steps"],
)
RoutingStepViewSet = build_model_viewset(
    RoutingStep,
    RoutingStepSerializer,
    permission_classes=[IsTenantUser],
    filterset_fields=["routing", "work_center"],
    ordering_fields=["sequence"],
    select_related_fields=["routing", "work_center"],
)
WorkOrderViewSet = build_model_viewset(
    WorkOrder,
    WorkOrderSerializer,
    permission_classes=[IsTenantUser],
    filterset_fields=["status", "branch", "responsible"],
    search_fields=["reference"],
    ordering_fields=["scheduled_start", "scheduled_end"],
    select_related_fields=["bom", "routing", "branch", "responsible"],
    prefetch_related_fields=["lines", "quality_checks"],
    extra_routes={
        "confirm": build_action_route("confirm", _confirm_work_order, methods=("post",), detail=True),
        "start": build_action_route("start", _start_work_order, methods=("post",), detail=True),
        "complete": build_action_route("complete", _complete_work_order, methods=("post",), detail=True),
    },
)
WorkOrderLineViewSet = build_model_viewset(
    WorkOrderLine,
    WorkOrderLineSerializer,
    permission_classes=[IsTenantUser],
    filterset_fields=["work_order"],
    select_related_fields=["work_order", "bom_component"],
)
QualityCheckViewSet = build_model_viewset(
    QualityCheck,
    QualityCheckSerializer,
    permission_classes=[IsTenantUser],
    filterset_fields=["work_order", "result"],
    select_related_fields=["work_order", "checked_by"],
)
ScrapRecordViewSet = build_model_viewset(
    ScrapRecord,
    ScrapRecordSerializer,
    permission_classes=[IsTenantUser],
    filterset_fields=["variant", "work_order", "branch", "reason"],
    ordering_fields=["scrap_date"],
    select_related_fields=["variant", "work_order", "branch", "scrapped_by"],
)
