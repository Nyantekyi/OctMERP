"""
apps/manufacturing/views.py
"""
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.common.permissions import IsTenantUser, IsManager
from .models import (
    BillOfMaterials, BOMComponent, WorkCenter, Routing, RoutingStep,
    WorkOrder, WorkOrderLine, QualityCheck, ScrapRecord,
)
from .serializers import (
    BillOfMaterialsSerializer, BOMComponentSerializer,
    WorkCenterSerializer, RoutingSerializer, RoutingStepSerializer,
    WorkOrderSerializer, WorkOrderLineSerializer,
    QualityCheckSerializer, ScrapRecordSerializer,
)


class BillOfMaterialsViewSet(viewsets.ModelViewSet):
    queryset = BillOfMaterials.objects.select_related("product", "variant", "unit", "branch").prefetch_related("components")
    serializer_class = BillOfMaterialsSerializer
    permission_classes = [IsTenantUser]
    filterset_fields = ["product", "variant", "bom_type", "branch", "is_default", "is_active"]
    search_fields = ["name"]
    ordering_fields = ["version"]


class BOMComponentViewSet(viewsets.ModelViewSet):
    queryset = BOMComponent.objects.select_related("bom", "component", "unit")
    serializer_class = BOMComponentSerializer
    permission_classes = [IsTenantUser]
    filterset_fields = ["bom", "component", "is_optional"]


class WorkCenterViewSet(viewsets.ModelViewSet):
    queryset = WorkCenter.objects.select_related("branch", "default_operator")
    serializer_class = WorkCenterSerializer
    permission_classes = [IsTenantUser]
    filterset_fields = ["branch", "is_active"]
    search_fields = ["name"]


class RoutingViewSet(viewsets.ModelViewSet):
    queryset = Routing.objects.select_related("bom").prefetch_related("steps")
    serializer_class = RoutingSerializer
    permission_classes = [IsTenantUser]
    filterset_fields = ["bom"]
    search_fields = ["name"]


class RoutingStepViewSet(viewsets.ModelViewSet):
    queryset = RoutingStep.objects.select_related("routing", "work_center")
    serializer_class = RoutingStepSerializer
    permission_classes = [IsTenantUser]
    filterset_fields = ["routing", "work_center"]
    ordering_fields = ["sequence"]


class WorkOrderViewSet(viewsets.ModelViewSet):
    queryset = WorkOrder.objects.select_related("bom", "routing", "branch", "responsible").prefetch_related("lines", "quality_checks")
    serializer_class = WorkOrderSerializer
    permission_classes = [IsTenantUser]
    filterset_fields = ["status", "branch", "responsible"]
    search_fields = ["reference"]
    ordering_fields = ["scheduled_start", "scheduled_end"]

    @action(detail=True, methods=["post"])
    def confirm(self, request, pk=None):
        wo = self.get_object()
        wo.status = "confirmed"
        wo.save()
        return Response({"success": True, "data": WorkOrderSerializer(wo).data})

    @action(detail=True, methods=["post"])
    def start(self, request, pk=None):
        wo = self.get_object()
        wo.status = "in_progress"
        wo.actual_start = timezone.now()
        wo.save()
        return Response({"success": True, "data": WorkOrderSerializer(wo).data})

    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        wo = self.get_object()
        qty = request.data.get("quantity_produced", wo.quantity_planned)
        wo.status = "done"
        wo.actual_end = timezone.now()
        wo.quantity_produced = qty
        wo.save()
        return Response({"success": True, "data": WorkOrderSerializer(wo).data})


class WorkOrderLineViewSet(viewsets.ModelViewSet):
    queryset = WorkOrderLine.objects.select_related("work_order", "bom_component")
    serializer_class = WorkOrderLineSerializer
    permission_classes = [IsTenantUser]
    filterset_fields = ["work_order"]


class QualityCheckViewSet(viewsets.ModelViewSet):
    queryset = QualityCheck.objects.select_related("work_order", "checked_by")
    serializer_class = QualityCheckSerializer
    permission_classes = [IsTenantUser]
    filterset_fields = ["work_order", "result"]


class ScrapRecordViewSet(viewsets.ModelViewSet):
    queryset = ScrapRecord.objects.select_related("variant", "work_order", "branch", "scrapped_by")
    serializer_class = ScrapRecordSerializer
    permission_classes = [IsTenantUser]
    filterset_fields = ["variant", "work_order", "branch", "reason"]
    ordering_fields = ["scrap_date"]
