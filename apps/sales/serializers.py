"""apps/sales/serializers.py"""

from apps.common.api import build_model_serializer

from .models import (
    CommissionRecord,
    CommissionRule,
    Delivery,
    DeliveryLine,
    SalesOrder,
    SalesOrderLine,
    SalesQuotation,
    SalesQuotationLine,
    SalesReturn,
    SalesReturnLine,
)


def _sales_order_line_to_representation(serializer, instance, representation):
    representation["quantity_remaining"] = str(instance.quantity_remaining)
    return representation


SalesQuotationLineSerializer = build_model_serializer(
    SalesQuotationLine,
    fields=[
        "id", "quotation", "product", "variant", "quantity", "unit",
        "item_pricing", "unit_price", "unit_price_currency",
        "discount_percent", "tax", "line_total", "line_total_currency",
        "description", "created_at", "updated_at",
    ],
    read_only_fields=("line_total",),
)

SalesQuotationSerializer = build_model_serializer(
    SalesQuotation,
    fields=[
        "id", "reference", "client", "branch", "issued_by",
        "issue_date", "expiry_date", "status", "pricing_department",
        "subtotal", "subtotal_currency",
        "discount_amount", "discount_amount_currency",
        "tax_amount", "tax_amount_currency",
        "total_amount", "total_amount_currency",
        "notes", "terms", "lines", "is_active", "created_at", "updated_at",
    ],
    nested_serializers={"lines": {"serializer": SalesQuotationLineSerializer, "many": True, "read_only": True, "required": False}},
)

SalesOrderLineSerializer = build_model_serializer(
    SalesOrderLine,
    fields=[
        "id", "order", "product", "variant",
        "quantity_ordered", "quantity_delivered",
        "unit", "item_pricing",
        "unit_price", "unit_price_currency",
        "discount_percent", "tax",
        "line_total", "line_total_currency",
        "lot", "quantity_remaining",
        "created_at", "updated_at",
    ],
    read_only_fields=("line_total",),
    to_representation_handler=_sales_order_line_to_representation,
)

SalesOrderSerializer = build_model_serializer(
    SalesOrder,
    fields=[
        "id", "reference", "quotation", "client", "branch", "processed_by",
        "order_date", "requested_delivery_date", "status", "pricing_department",
        "shipping_address_line1", "shipping_address_line2", "shipping_city",
        "subtotal", "subtotal_currency",
        "discount_amount", "discount_amount_currency",
        "tax_amount", "tax_amount_currency",
        "total_amount", "total_amount_currency",
        "invoice", "notes", "lines", "is_active", "created_at", "updated_at",
    ],
    nested_serializers={"lines": {"serializer": SalesOrderLineSerializer, "many": True, "read_only": True, "required": False}},
)

DeliveryLineSerializer = build_model_serializer(
    DeliveryLine,
    fields=["id", "delivery", "so_line", "quantity_dispatched", "lot", "created_at", "updated_at"],
)

DeliverySerializer = build_model_serializer(
    Delivery,
    fields=[
        "id", "reference", "sales_order", "branch", "carrier",
        "scheduled_date", "actual_date", "status",
        "driver", "tracking_number", "notes",
        "lines", "is_active", "created_at", "updated_at",
    ],
    nested_serializers={"lines": {"serializer": DeliveryLineSerializer, "many": True, "read_only": True, "required": False}},
)

SalesReturnLineSerializer = build_model_serializer(
    SalesReturnLine,
    fields=["id", "sales_return", "so_line", "quantity_returned", "condition", "created_at", "updated_at"],
)

SalesReturnSerializer = build_model_serializer(
    SalesReturn,
    fields=[
        "id", "reference", "sales_order", "client", "return_date",
        "reason", "reason_detail", "status",
        "refund_amount", "refund_amount_currency",
        "credit_note", "transaction_doc",
        "lines", "is_active", "created_at", "updated_at",
    ],
    nested_serializers={"lines": {"serializer": SalesReturnLineSerializer, "many": True, "read_only": True, "required": False}},
)

CommissionRuleSerializer = build_model_serializer(
    CommissionRule,
    fields=[
        "id", "name", "commission_rate_percent", "applies_to",
        "team", "staff", "is_active", "created_at", "updated_at",
    ],
)

CommissionRecordSerializer = build_model_serializer(
    CommissionRecord,
    fields=[
        "id", "rule", "staff", "sales_order",
        "base_amount", "base_amount_currency",
        "commission_amount", "commission_amount_currency",
        "status", "period", "created_at", "updated_at",
    ],
)
