"""apps/pos/serializers.py"""

from apps.common.api import build_model_serializer

from .models import (
    CashDrawerEvent,
    POSConfig,
    POSOrder,
    POSOrderLine,
    POSPayment,
    POSSession,
)


POSConfigSerializer = build_model_serializer(
    POSConfig,
    fields=[
        "id", "name", "branch", "allowed_payment_methods",
        "allow_discount", "max_discount_percent", "require_customer",
        "allow_negative_stock", "opening_float", "opening_float_currency",
        "receipt_header", "receipt_footer", "printer_ip",
        "is_active", "created_at", "updated_at",
    ],
)


POSSessionSerializer = build_model_serializer(
    POSSession,
    fields=[
        "id", "config", "cashier", "opened_at", "closed_at", "status",
        "opening_balance", "opening_balance_currency",
        "closing_balance", "closing_balance_currency",
        "expected_balance", "expected_balance_currency",
        "difference", "difference_currency",
        "notes", "cash_account", "is_active", "created_at", "updated_at",
    ],
    read_only_fields=("expected_balance", "difference", "cash_account"),
)


POSOrderLineSerializer = build_model_serializer(
    POSOrderLine,
    fields=[
        "id", "order", "product", "variant", "quantity", "unit",
        "item_pricing", "unit_price", "unit_price_currency",
        "discount_percent", "tax", "line_total", "line_total_currency",
        "lot", "is_returned", "created_at", "updated_at",
    ],
    read_only_fields=("line_total",),
)


POSPaymentSerializer = build_model_serializer(
    POSPayment,
    fields=[
        "id", "order", "payment_method", "amount", "amount_currency",
        "reference", "payment_at", "bank_account",
        "created_at", "updated_at",
    ],
)


POSOrderSerializer = build_model_serializer(
    POSOrder,
    fields=[
        "id", "session", "client", "order_date", "status",
        "subtotal", "subtotal_currency",
        "discount_amount", "discount_amount_currency",
        "tax_amount", "tax_amount_currency",
        "total_amount", "total_amount_currency",
        "amount_tendered", "amount_tendered_currency",
        "change_due", "change_due_currency",
        "invoice", "transaction_doc", "receipt_printed", "notes",
        "lines", "payments", "is_active", "created_at", "updated_at",
    ],
    read_only_fields=("change_due",),
    nested_serializers={
        "lines": {"serializer": POSOrderLineSerializer, "many": True, "read_only": True, "required": False},
        "payments": {"serializer": POSPaymentSerializer, "many": True, "read_only": True, "required": False},
    },
)


CashDrawerEventSerializer = build_model_serializer(
    CashDrawerEvent,
    fields=["id", "session", "event_type", "amount", "amount_currency", "reason", "performed_by", "occurred_at", "created_at", "updated_at"],
)
