"""
apps/procurement/views.py
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.common.permissions import IsTenantUser, IsManager
from .models import (
    PurchaseRequisition, PurchaseRequisitionLine,
    RFQ, RFQLine,
    PurchaseOrder, PurchaseOrderLine,
    GoodsReceiptNote, GRNLine,
    VendorContract, SupplierEvaluation,
)
from .serializers import (
    PurchaseRequisitionSerializer, PurchaseRequisitionLineSerializer,
    RFQSerializer, RFQLineSerializer,
    PurchaseOrderSerializer, PurchaseOrderLineSerializer,
    GoodsReceiptNoteSerializer, GRNLineSerializer,
    VendorContractSerializer, SupplierEvaluationSerializer,
)


class PurchaseRequisitionViewSet(viewsets.ModelViewSet):
    queryset = PurchaseRequisition.objects.select_related("branch", "department", "requested_by").prefetch_related("lines")
    serializer_class = PurchaseRequisitionSerializer
    permission_classes = [IsTenantUser]
    filterset_fields = ["status", "branch", "department", "requested_by"]
    search_fields = ["reference"]
    ordering_fields = ["request_date"]

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        obj = self.get_object()
        obj.status = "approved"
        obj.approved_by = getattr(request.user, "staff_profile", None)
        obj.save()
        return Response({"success": True, "data": PurchaseRequisitionSerializer(obj).data})

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        obj = self.get_object()
        obj.status = "rejected"
        obj.save()
        return Response({"success": True, "data": PurchaseRequisitionSerializer(obj).data})


class PurchaseRequisitionLineViewSet(viewsets.ModelViewSet):
    queryset = PurchaseRequisitionLine.objects.select_related("requisition", "product")
    serializer_class = PurchaseRequisitionLineSerializer
    permission_classes = [IsTenantUser]
    filterset_fields = ["requisition", "product"]


class RFQViewSet(viewsets.ModelViewSet):
    queryset = RFQ.objects.select_related("requisition", "supplier", "branch").prefetch_related("lines")
    serializer_class = RFQSerializer
    permission_classes = [IsTenantUser]
    filterset_fields = ["status", "supplier", "branch"]
    search_fields = ["reference"]
    ordering_fields = ["issued_date"]


class RFQLineViewSet(viewsets.ModelViewSet):
    queryset = RFQLine.objects.select_related("rfq", "product")
    serializer_class = RFQLineSerializer
    permission_classes = [IsTenantUser]
    filterset_fields = ["rfq", "product"]


class PurchaseOrderViewSet(viewsets.ModelViewSet):
    queryset = PurchaseOrder.objects.select_related("rfq", "requisition", "supplier", "branch").prefetch_related("lines")
    serializer_class = PurchaseOrderSerializer
    permission_classes = [IsTenantUser]
    filterset_fields = ["status", "supplier", "branch"]
    search_fields = ["reference"]
    ordering_fields = ["order_date"]

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        obj = self.get_object()
        obj.status = "approved"
        obj.approved_by = getattr(request.user, "staff_profile", None)
        obj.save()
        return Response({"success": True, "data": PurchaseOrderSerializer(obj).data})

    @action(detail=True, methods=["post"])
    def send_to_supplier(self, request, pk=None):
        obj = self.get_object()
        obj.status = "sent"
        obj.save()
        return Response({"success": True, "data": PurchaseOrderSerializer(obj).data})


class PurchaseOrderLineViewSet(viewsets.ModelViewSet):
    queryset = PurchaseOrderLine.objects.select_related("order", "product")
    serializer_class = PurchaseOrderLineSerializer
    permission_classes = [IsTenantUser]
    filterset_fields = ["order", "product"]


class GoodsReceiptNoteViewSet(viewsets.ModelViewSet):
    queryset = GoodsReceiptNote.objects.select_related("purchase_order", "received_by").prefetch_related("lines")
    serializer_class = GoodsReceiptNoteSerializer
    permission_classes = [IsTenantUser]
    filterset_fields = ["status", "purchase_order"]
    search_fields = ["reference"]
    ordering_fields = ["received_date"]

    @action(detail=True, methods=["post"])
    def validate(self, request, pk=None):
        grn = self.get_object()
        grn.status = "validated"
        grn.save()
        return Response({"success": True, "data": GoodsReceiptNoteSerializer(grn).data})


class GRNLineViewSet(viewsets.ModelViewSet):
    queryset = GRNLine.objects.select_related("grn", "po_line")
    serializer_class = GRNLineSerializer
    permission_classes = [IsTenantUser]
    filterset_fields = ["grn"]


class VendorContractViewSet(viewsets.ModelViewSet):
    queryset = VendorContract.objects.select_related("supplier", "department")
    serializer_class = VendorContractSerializer
    permission_classes = [IsTenantUser]
    filterset_fields = ["status", "supplier", "department"]
    search_fields = ["reference"]
    ordering_fields = ["start_date", "end_date"]


class SupplierEvaluationViewSet(viewsets.ModelViewSet):
    queryset = SupplierEvaluation.objects.select_related("supplier", "evaluated_by", "purchase_order")
    serializer_class = SupplierEvaluationSerializer
    permission_classes = [IsTenantUser]
    filterset_fields = ["supplier", "evaluated_by"]
    ordering_fields = ["evaluation_date"]
