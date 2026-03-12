"""apps/procurement/views.py"""

from rest_framework.response import Response

from apps.common.api import build_action_route, build_model_viewset
from apps.common.permissions import IsTenantUser
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
from .serializers import (
    GoodsReceiptNoteSerializer,
    GRNLineSerializer,
    PurchaseOrderLineSerializer,
    PurchaseOrderSerializer,
    PurchaseRequisitionLineSerializer,
    PurchaseRequisitionSerializer,
    RFQLineSerializer,
    RFQSerializer,
    SupplierEvaluationSerializer,
    VendorContractSerializer,
)


def _approve_purchase_requisition(self, request, *args, **kwargs):
    obj = self.get_object()
    obj.status = "approved"
    obj.approved_by = getattr(request.user, "staff_profile", None)
    obj.save(update_fields=["status", "approved_by", "updated_at"])
    return Response({"success": True, "data": PurchaseRequisitionSerializer(obj).data})


def _reject_purchase_requisition(self, request, *args, **kwargs):
    obj = self.get_object()
    obj.status = "rejected"
    obj.save(update_fields=["status", "updated_at"])
    return Response({"success": True, "data": PurchaseRequisitionSerializer(obj).data})


def _approve_purchase_order(self, request, *args, **kwargs):
    obj = self.get_object()
    obj.status = "approved"
    obj.approved_by = getattr(request.user, "staff_profile", None)
    obj.save(update_fields=["status", "approved_by", "updated_at"])
    return Response({"success": True, "data": PurchaseOrderSerializer(obj).data})


def _send_purchase_order(self, request, *args, **kwargs):
    obj = self.get_object()
    obj.status = "sent"
    obj.save(update_fields=["status", "updated_at"])
    return Response({"success": True, "data": PurchaseOrderSerializer(obj).data})


def _validate_grn(self, request, *args, **kwargs):
    grn = self.get_object()
    grn.status = "validated"
    grn.save(update_fields=["status", "updated_at"])
    return Response({"success": True, "data": GoodsReceiptNoteSerializer(grn).data})


PurchaseRequisitionViewSet = build_model_viewset(
    PurchaseRequisition,
    PurchaseRequisitionSerializer,
    permission_classes=[IsTenantUser],
    filterset_fields=["status", "branch", "department", "requested_by"],
    search_fields=["reference"],
    ordering_fields=["request_date"],
    select_related_fields=["branch", "department", "requested_by"],
    prefetch_related_fields=["lines"],
    extra_routes={
        "approve": build_action_route("approve", _approve_purchase_requisition, methods=("post",), detail=True),
        "reject": build_action_route("reject", _reject_purchase_requisition, methods=("post",), detail=True),
    },
)

PurchaseRequisitionLineViewSet = build_model_viewset(
    PurchaseRequisitionLine,
    PurchaseRequisitionLineSerializer,
    permission_classes=[IsTenantUser],
    filterset_fields=["requisition", "product"],
    select_related_fields=["requisition", "product"],
)

RFQViewSet = build_model_viewset(
    RFQ,
    RFQSerializer,
    permission_classes=[IsTenantUser],
    filterset_fields=["status", "supplier", "branch"],
    search_fields=["reference"],
    ordering_fields=["issued_date"],
    select_related_fields=["requisition", "supplier", "branch"],
    prefetch_related_fields=["lines"],
)

RFQLineViewSet = build_model_viewset(
    RFQLine,
    RFQLineSerializer,
    permission_classes=[IsTenantUser],
    filterset_fields=["rfq", "product"],
    select_related_fields=["rfq", "product"],
)

PurchaseOrderViewSet = build_model_viewset(
    PurchaseOrder,
    PurchaseOrderSerializer,
    permission_classes=[IsTenantUser],
    filterset_fields=["status", "supplier", "branch"],
    search_fields=["reference"],
    ordering_fields=["order_date"],
    select_related_fields=["rfq", "requisition", "supplier", "branch"],
    prefetch_related_fields=["lines"],
    extra_routes={
        "approve": build_action_route("approve", _approve_purchase_order, methods=("post",), detail=True),
        "send_to_supplier": build_action_route("send_to_supplier", _send_purchase_order, methods=("post",), detail=True),
    },
)

PurchaseOrderLineViewSet = build_model_viewset(
    PurchaseOrderLine,
    PurchaseOrderLineSerializer,
    permission_classes=[IsTenantUser],
    filterset_fields=["order", "product"],
    select_related_fields=["order", "product"],
)

GoodsReceiptNoteViewSet = build_model_viewset(
    GoodsReceiptNote,
    GoodsReceiptNoteSerializer,
    permission_classes=[IsTenantUser],
    filterset_fields=["status", "purchase_order"],
    search_fields=["reference"],
    ordering_fields=["received_date"],
    select_related_fields=["purchase_order", "received_by"],
    prefetch_related_fields=["lines"],
    extra_routes={
        "validate": build_action_route("validate", _validate_grn, methods=("post",), detail=True),
    },
)

GRNLineViewSet = build_model_viewset(
    GRNLine,
    GRNLineSerializer,
    permission_classes=[IsTenantUser],
    filterset_fields=["grn"],
    select_related_fields=["grn", "po_line"],
)

VendorContractViewSet = build_model_viewset(
    VendorContract,
    VendorContractSerializer,
    permission_classes=[IsTenantUser],
    filterset_fields=["status", "supplier", "department"],
    search_fields=["reference"],
    ordering_fields=["start_date", "end_date"],
    select_related_fields=["supplier", "department"],
)

SupplierEvaluationViewSet = build_model_viewset(
    SupplierEvaluation,
    SupplierEvaluationSerializer,
    permission_classes=[IsTenantUser],
    filterset_fields=["supplier", "evaluated_by"],
    ordering_fields=["evaluation_date"],
    select_related_fields=["supplier", "evaluated_by", "purchase_order"],
)
