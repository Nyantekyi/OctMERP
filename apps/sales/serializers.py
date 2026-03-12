"""
apps/sales/serializers.py
"""
from rest_framework import serializers

from .models import (
    SalesQuotation, SalesQuotationLine,
    SalesOrder, SalesOrderLine,
    Delivery, DeliveryLine,
    SalesReturn, SalesReturnLine,
    CommissionRule, CommissionRecord,
)


class SalesQuotationLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalesQuotationLine
        fields = [
            "id", "quotation", "product", "variant", "quantity", "unit",
            "item_pricing", "unit_price", "unit_price_currency",
            "discount_percent", "tax", "line_total", "line_total_currency",
            "description", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "line_total", "created_at", "updated_at"]


class SalesQuotationSerializer(serializers.ModelSerializer):
    lines = SalesQuotationLineSerializer(many=True, read_only=True)

    class Meta:
        model = SalesQuotation
        fields = [
            "id", "reference", "client", "branch", "issued_by",
            "issue_date", "expiry_date", "status", "pricing_department",
            "subtotal", "subtotal_currency",
            "discount_amount", "discount_amount_currency",
            "tax_amount", "tax_amount_currency",
            "total_amount", "total_amount_currency",
            "notes", "terms", "lines", "is_active", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class SalesOrderLineSerializer(serializers.ModelSerializer):
    quantity_remaining = serializers.SerializerMethodField()

    class Meta:
        model = SalesOrderLine
        fields = [
            "id", "order", "product", "variant",
            "quantity_ordered", "quantity_delivered",
            "unit", "item_pricing",
            "unit_price", "unit_price_currency",
            "discount_percent", "tax",
            "line_total", "line_total_currency",
            "lot", "quantity_remaining",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "line_total", "created_at", "updated_at"]

    def get_quantity_remaining(self, obj):
        return str(obj.quantity_remaining)


class SalesOrderSerializer(serializers.ModelSerializer):
    lines = SalesOrderLineSerializer(many=True, read_only=True)

    class Meta:
        model = SalesOrder
        fields = [
            "id", "reference", "quotation", "client", "branch", "processed_by",
            "order_date", "requested_delivery_date", "status", "pricing_department",
            "shipping_address_line1", "shipping_address_line2", "shipping_city",
            "subtotal", "subtotal_currency",
            "discount_amount", "discount_amount_currency",
            "tax_amount", "tax_amount_currency",
            "total_amount", "total_amount_currency",
            "invoice", "notes", "lines", "is_active", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class DeliveryLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeliveryLine
        fields = ["id", "delivery", "so_line", "quantity_dispatched", "lot", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class DeliverySerializer(serializers.ModelSerializer):
    lines = DeliveryLineSerializer(many=True, read_only=True)

    class Meta:
        model = Delivery
        fields = [
            "id", "reference", "sales_order", "branch", "carrier",
            "scheduled_date", "actual_date", "status",
            "driver", "tracking_number", "notes",
            "lines", "is_active", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class SalesReturnLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalesReturnLine
        fields = ["id", "sales_return", "so_line", "quantity_returned", "condition", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class SalesReturnSerializer(serializers.ModelSerializer):
    lines = SalesReturnLineSerializer(many=True, read_only=True)

    class Meta:
        model = SalesReturn
        fields = [
            "id", "reference", "sales_order", "client", "return_date",
            "reason", "reason_detail", "status",
            "refund_amount", "refund_amount_currency",
            "credit_note", "transaction_doc",
            "lines", "is_active", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class CommissionRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommissionRule
        fields = [
            "id", "name", "commission_rate_percent", "applies_to",
            "team", "staff", "is_active", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class CommissionRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommissionRecord
        fields = [
            "id", "rule", "staff", "sales_order",
            "base_amount", "base_amount_currency",
            "commission_amount", "commission_amount_currency",
            "status", "period", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
