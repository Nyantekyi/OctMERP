"""
apps/procurement/serializers.py
"""
from rest_framework import serializers

from .models import (
    PurchaseRequisition, PurchaseRequisitionLine,
    RFQ, RFQLine,
    PurchaseOrder, PurchaseOrderLine,
    GoodsReceiptNote, GRNLine,
    VendorContract, SupplierEvaluation,
)


class PurchaseRequisitionLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchaseRequisitionLine
        fields = [
            "id", "requisition", "product", "variant", "quantity", "unit",
            "estimated_unit_price", "estimated_unit_price_currency",
            "preferred_supplier", "description", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class PurchaseRequisitionSerializer(serializers.ModelSerializer):
    lines = PurchaseRequisitionLineSerializer(many=True, read_only=True)

    class Meta:
        model = PurchaseRequisition
        fields = [
            "id", "reference", "branch", "department",
            "requested_by", "request_date", "required_by_date",
            "status", "approved_by", "approval_date", "notes",
            "budget_request", "lines", "is_active", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "approval_date", "created_at", "updated_at"]


class RFQLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = RFQLine
        fields = [
            "id", "rfq", "product", "variant", "quantity", "unit",
            "quoted_unit_price", "quoted_unit_price_currency",
            "lead_time_days", "remarks", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class RFQSerializer(serializers.ModelSerializer):
    lines = RFQLineSerializer(many=True, read_only=True)

    class Meta:
        model = RFQ
        fields = [
            "id", "reference", "requisition", "supplier", "branch",
            "issued_date", "response_deadline", "status", "notes",
            "lines", "is_active", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class PurchaseOrderLineSerializer(serializers.ModelSerializer):
    quantity_pending = serializers.SerializerMethodField()

    class Meta:
        model = PurchaseOrderLine
        fields = [
            "id", "order", "product", "variant", "quantity_ordered", "quantity_received",
            "unit", "unit_price", "unit_price_currency",
            "tax", "line_total", "line_total_currency",
            "shelf", "quantity_pending", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "line_total", "created_at", "updated_at"]

    def get_quantity_pending(self, obj):
        return str(obj.quantity_pending)


class PurchaseOrderSerializer(serializers.ModelSerializer):
    lines = PurchaseOrderLineSerializer(many=True, read_only=True)

    class Meta:
        model = PurchaseOrder
        fields = [
            "id", "reference", "rfq", "requisition", "supplier", "branch",
            "order_date", "expected_delivery_date", "status",
            "approved_by", "terms_and_conditions", "currency",
            "subtotal", "subtotal_currency",
            "tax_amount", "tax_amount_currency",
            "total_amount", "total_amount_currency",
            "bill", "lines", "is_active", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class GRNLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = GRNLine
        fields = ["id", "grn", "po_line", "quantity_received", "quantity_rejected", "lot", "shelf", "remarks", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class VendorContractSerializer(serializers.ModelSerializer):
    class Meta:
        model = VendorContract
        fields = [
            "id", "reference", "supplier", "department",
            "start_date", "end_date",
            "value", "value_currency",
            "status", "terms", "payment_terms_days", "document_url",
            "is_active", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class SupplierEvaluationSerializer(serializers.ModelSerializer):
    overall_score = serializers.SerializerMethodField()

    class Meta:
        model = SupplierEvaluation
        fields = [
            "id", "supplier", "evaluated_by", "evaluation_date", "purchase_order",
            "quality_score", "delivery_score", "price_score", "communication_score",
            "overall_score", "comments", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_overall_score(self, obj):
        return obj.overall_score


class GoodsReceiptNoteSerializer(serializers.ModelSerializer):
    lines = GRNLineSerializer(many=True, read_only=True)

    class Meta:
        model = GoodsReceiptNote
        fields = [
            "id", "reference", "purchase_order", "received_by",
            "received_date", "supplier_delivery_note", "status", "notes",
            "lines", "is_active", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
