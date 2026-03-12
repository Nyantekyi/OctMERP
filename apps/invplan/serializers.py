"""
apps/invplan/serializers.py
"""
from rest_framework import serializers

from .models import (
    TermsAndCondition, InventoryCondition, Carrier,
    OrderDocument, OrderDocumentAttachment, OrderDocumentDetail,
)


class TermsAndConditionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TermsAndCondition
        fields = [
            "id", "code", "exchangeable", "warranty_included",
            "defective_returns_allowed", "delivery_insurance_provided",
            "cod_allowed", "cancellation_policy_available",
            "free_shipping_available", "return_window_days",
            "is_active", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class InventoryConditionSerializer(serializers.ModelSerializer):
    class Meta:
        model = InventoryCondition
        fields = ["id", "name", "is_active", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class CarrierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Carrier
        fields = ["id", "name", "description", "is_active", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class OrderDocumentAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderDocumentAttachment
        fields = ["id", "order_document", "file_url", "description", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class OrderDocumentDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderDocumentDetail
        fields = [
            "id", "order", "item", "uom",
            "unit_cost_price", "unit_cost_price_currency",
            "qty", "qty_base", "line_total", "line_total_currency",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "qty_base", "line_total", "created_at", "updated_at"]


class OrderDocumentSerializer(serializers.ModelSerializer):
    lines = OrderDocumentDetailSerializer(many=True, read_only=True)
    attachments = OrderDocumentAttachmentSerializer(many=True, read_only=True)

    class Meta:
        model = OrderDocument
        fields = [
            "id", "ordertype", "title", "source_document", "status",
            "branch", "staff", "vendor", "client", "sourcebranch",
            "carrier", "terms",
            "order_amount", "order_amount_currency",
            "expected_delivery_date", "notes",
            "lines", "attachments",
            "is_active", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "title", "created_at", "updated_at"]
