"""
apps/manufacturing/serializers.py
"""
from rest_framework import serializers

from .models import (
    BillOfMaterials, BOMComponent, WorkCenter, Routing, RoutingStep,
    WorkOrder, WorkOrderLine, QualityCheck, ScrapRecord,
)


class BOMComponentSerializer(serializers.ModelSerializer):
    quantity_with_scrap = serializers.SerializerMethodField()

    class Meta:
        model = BOMComponent
        fields = [
            "id", "bom", "component", "quantity", "unit", "scrap_percent",
            "is_optional", "notes", "quantity_with_scrap", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_quantity_with_scrap(self, obj):
        return str(obj.quantity_with_scrap)


class BillOfMaterialsSerializer(serializers.ModelSerializer):
    components = BOMComponentSerializer(many=True, read_only=True)

    class Meta:
        model = BillOfMaterials
        fields = [
            "id", "name", "product", "variant", "quantity", "unit",
            "bom_type", "branch", "version", "is_default", "notes",
            "components", "is_active", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class WorkCenterSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkCenter
        fields = [
            "id", "name", "branch", "capacity_per_hour",
            "cost_per_hour", "cost_per_hour_currency",
            "default_operator", "notes", "is_active", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class RoutingStepSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoutingStep
        fields = ["id", "routing", "name", "work_center", "sequence", "duration_minutes", "instructions", "is_active", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class RoutingSerializer(serializers.ModelSerializer):
    steps = RoutingStepSerializer(many=True, read_only=True)

    class Meta:
        model = Routing
        fields = ["id", "name", "bom", "steps", "is_active", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class WorkOrderLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkOrderLine
        fields = ["id", "work_order", "bom_component", "quantity_required", "quantity_consumed", "lot", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class QualityCheckSerializer(serializers.ModelSerializer):
    class Meta:
        model = QualityCheck
        fields = ["id", "work_order", "check_name", "description", "result", "checked_by", "checked_at", "notes", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class WorkOrderSerializer(serializers.ModelSerializer):
    lines = WorkOrderLineSerializer(many=True, read_only=True)
    quality_checks = QualityCheckSerializer(many=True, read_only=True)

    class Meta:
        model = WorkOrder
        fields = [
            "id", "reference", "bom", "routing",
            "quantity_planned", "quantity_produced", "unit",
            "branch", "scheduled_start", "scheduled_end",
            "actual_start", "actual_end", "status",
            "responsible", "sales_order", "notes",
            "lines", "quality_checks", "is_active", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class ScrapRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScrapRecord
        fields = [
            "id", "variant", "lot", "work_order", "branch",
            "quantity", "unit", "scrap_date", "reason", "detail",
            "scrapped_by", "transaction_doc", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
