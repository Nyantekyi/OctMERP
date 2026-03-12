"""apps/manufacturing/serializers.py"""

from apps.common.api import build_model_serializer

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


def _bom_component_to_representation(serializer, instance, representation):
    representation["quantity_with_scrap"] = str(instance.quantity_with_scrap)
    return representation


BOMComponentSerializer = build_model_serializer(
    BOMComponent,
    fields=[
        "id", "bom", "component", "quantity", "unit", "scrap_percent",
        "is_optional", "notes", "quantity_with_scrap", "created_at", "updated_at",
    ],
    to_representation_handler=_bom_component_to_representation,
)
BillOfMaterialsSerializer = build_model_serializer(
    BillOfMaterials,
    fields=[
        "id", "name", "product", "variant", "quantity", "unit",
        "bom_type", "branch", "version", "is_default", "notes",
        "components", "is_active", "created_at", "updated_at",
    ],
    nested_serializers={"components": {"serializer": BOMComponentSerializer, "many": True, "read_only": True, "required": False}},
)
WorkCenterSerializer = build_model_serializer(
    WorkCenter,
    fields=[
        "id", "name", "branch", "capacity_per_hour",
        "cost_per_hour", "cost_per_hour_currency",
        "default_operator", "notes", "is_active", "created_at", "updated_at",
    ],
)
RoutingStepSerializer = build_model_serializer(
    RoutingStep,
    fields=["id", "routing", "name", "work_center", "sequence", "duration_minutes", "instructions", "is_active", "created_at", "updated_at"],
)
RoutingSerializer = build_model_serializer(
    Routing,
    fields=["id", "name", "bom", "steps", "is_active", "created_at", "updated_at"],
    nested_serializers={"steps": {"serializer": RoutingStepSerializer, "many": True, "read_only": True, "required": False}},
)
WorkOrderLineSerializer = build_model_serializer(
    WorkOrderLine,
    fields=["id", "work_order", "bom_component", "quantity_required", "quantity_consumed", "lot", "created_at", "updated_at"],
)
QualityCheckSerializer = build_model_serializer(
    QualityCheck,
    fields=["id", "work_order", "check_name", "description", "result", "checked_by", "checked_at", "notes", "created_at", "updated_at"],
)
WorkOrderSerializer = build_model_serializer(
    WorkOrder,
    fields=[
        "id", "reference", "bom", "routing",
        "quantity_planned", "quantity_produced", "unit",
        "branch", "scheduled_start", "scheduled_end",
        "actual_start", "actual_end", "status",
        "responsible", "sales_order", "notes",
        "lines", "quality_checks", "is_active", "created_at", "updated_at",
    ],
    nested_serializers={
        "lines": {"serializer": WorkOrderLineSerializer, "many": True, "read_only": True, "required": False},
        "quality_checks": {"serializer": QualityCheckSerializer, "many": True, "read_only": True, "required": False},
    },
)
ScrapRecordSerializer = build_model_serializer(
    ScrapRecord,
    fields=[
        "id", "variant", "lot", "work_order", "branch",
        "quantity", "unit", "scrap_date", "reason", "detail",
        "scrapped_by", "transaction_doc", "created_at", "updated_at",
    ],
)
