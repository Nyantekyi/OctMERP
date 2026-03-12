"""apps/procurement/serializers.py"""

from apps.common.api import build_model_serializer

from .models import (
    GoodsReceiptNote,
    GRNLine,
    PurchaseOrder,
    PurchaseOrderLine,
    PurchaseRequisition,
    PurchaseRequisitionLine,
    RFQ,
    RFQLine,
    SupplierEvaluation,
    VendorContract,
)


def _purchase_order_line_to_representation(serializer, instance, representation):
    representation["quantity_pending"] = str(instance.quantity_pending)
    return representation


def _supplier_evaluation_to_representation(serializer, instance, representation):
    representation["overall_score"] = instance.overall_score
    return representation


PurchaseRequisitionLineSerializer = build_model_serializer(
    PurchaseRequisitionLine,
    fields=[
        "id", "requisition", "product", "variant", "quantity", "unit",
        "estimated_unit_price", "estimated_unit_price_currency",
        "preferred_supplier", "description", "created_at", "updated_at",
    ],
)

PurchaseRequisitionSerializer = build_model_serializer(
    PurchaseRequisition,
    fields=[
        "id", "reference", "branch", "department",
        "requested_by", "request_date", "required_by_date",
        "status", "approved_by", "approval_date", "notes",
        "budget_request", "lines", "is_active", "created_at", "updated_at",
    ],
    read_only_fields=("approval_date",),
    nested_serializers={"lines": {"serializer": PurchaseRequisitionLineSerializer, "many": True, "read_only": True, "required": False}},
)

RFQLineSerializer = build_model_serializer(
    RFQLine,
    fields=[
        "id", "rfq", "product", "variant", "quantity", "unit",
        "quoted_unit_price", "quoted_unit_price_currency",
        "lead_time_days", "remarks", "created_at", "updated_at",
    ],
)

RFQSerializer = build_model_serializer(
    RFQ,
    fields=[
        "id", "reference", "requisition", "supplier", "branch",
        "issued_date", "response_deadline", "status", "notes",
        "lines", "is_active", "created_at", "updated_at",
    ],
    nested_serializers={"lines": {"serializer": RFQLineSerializer, "many": True, "read_only": True, "required": False}},
)

PurchaseOrderLineSerializer = build_model_serializer(
    PurchaseOrderLine,
    fields=[
        "id", "order", "product", "variant", "quantity_ordered", "quantity_received",
        "unit", "unit_price", "unit_price_currency",
        "tax", "line_total", "line_total_currency",
        "shelf", "quantity_pending", "created_at", "updated_at",
    ],
    read_only_fields=("line_total",),
    to_representation_handler=_purchase_order_line_to_representation,
)

PurchaseOrderSerializer = build_model_serializer(
    PurchaseOrder,
    fields=[
        "id", "reference", "rfq", "requisition", "supplier", "branch",
        "order_date", "expected_delivery_date", "status",
        "approved_by", "terms_and_conditions", "currency",
        "subtotal", "subtotal_currency",
        "tax_amount", "tax_amount_currency",
        "total_amount", "total_amount_currency",
        "bill", "lines", "is_active", "created_at", "updated_at",
    ],
    nested_serializers={"lines": {"serializer": PurchaseOrderLineSerializer, "many": True, "read_only": True, "required": False}},
)

GRNLineSerializer = build_model_serializer(
    GRNLine,
    fields=["id", "grn", "po_line", "quantity_received", "quantity_rejected", "lot", "shelf", "remarks", "created_at", "updated_at"],
)

VendorContractSerializer = build_model_serializer(
    VendorContract,
    fields=[
        "id", "reference", "supplier", "department",
        "start_date", "end_date",
        "value", "value_currency",
        "status", "terms", "payment_terms_days", "document_url",
        "is_active", "created_at", "updated_at",
    ],
)

SupplierEvaluationSerializer = build_model_serializer(
    SupplierEvaluation,
    fields=[
        "id", "supplier", "evaluated_by", "evaluation_date", "purchase_order",
        "quality_score", "delivery_score", "price_score", "communication_score",
        "overall_score", "comments", "created_at", "updated_at",
    ],
    to_representation_handler=_supplier_evaluation_to_representation,
)

GoodsReceiptNoteSerializer = build_model_serializer(
    GoodsReceiptNote,
    fields=[
        "id", "reference", "purchase_order", "received_by",
        "received_date", "supplier_delivery_note", "status", "notes",
        "lines", "is_active", "created_at", "updated_at",
    ],
    nested_serializers={"lines": {"serializer": GRNLineSerializer, "many": True, "read_only": True, "required": False}},
)
