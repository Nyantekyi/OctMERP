"""
apps/pos/serializers.py
"""
from rest_framework import serializers

from .models import (
    POSConfig, POSSession, POSOrder, POSOrderLine, POSPayment, CashDrawerEvent,
)


class POSConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = POSConfig
        fields = [
            "id", "name", "branch", "allowed_payment_methods",
            "allow_discount", "max_discount_percent", "require_customer",
            "allow_negative_stock", "opening_float", "opening_float_currency",
            "receipt_header", "receipt_footer", "printer_ip",
            "is_active", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class POSSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = POSSession
        fields = [
            "id", "config", "cashier", "opened_at", "closed_at", "status",
            "opening_balance", "opening_balance_currency",
            "closing_balance", "closing_balance_currency",
            "expected_balance", "expected_balance_currency",
            "difference", "difference_currency",
            "notes", "cash_account", "is_active", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "expected_balance", "difference", "cash_account", "created_at", "updated_at"]


class POSOrderLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = POSOrderLine
        fields = [
            "id", "order", "product", "variant", "quantity", "unit",
            "item_pricing", "unit_price", "unit_price_currency",
            "discount_percent", "tax", "line_total", "line_total_currency",
            "lot", "is_returned", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "line_total", "created_at", "updated_at"]


class POSPaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = POSPayment
        fields = [
            "id", "order", "payment_method", "amount", "amount_currency",
            "reference", "payment_at", "bank_account",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class POSOrderSerializer(serializers.ModelSerializer):
    lines = POSOrderLineSerializer(many=True, read_only=True)
    payments = POSPaymentSerializer(many=True, read_only=True)

    class Meta:
        model = POSOrder
        fields = [
            "id", "session", "client", "order_date", "status",
            "subtotal", "subtotal_currency",
            "discount_amount", "discount_amount_currency",
            "tax_amount", "tax_amount_currency",
            "total_amount", "total_amount_currency",
            "amount_tendered", "amount_tendered_currency",
            "change_due", "change_due_currency",
            "invoice", "transaction_doc", "receipt_printed", "notes",
            "lines", "payments", "is_active", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "change_due", "created_at", "updated_at"]


class CashDrawerEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = CashDrawerEvent
        fields = ["id", "session", "event_type", "amount", "amount_currency", "reason", "performed_by", "occurred_at", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]
