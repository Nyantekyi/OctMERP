"""apps/sales/views.py"""

from rest_framework.response import Response

from apps.common.api import build_action_route, build_model_viewset
from apps.common.permissions import IsTenantUser
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
from .serializers import (
    CommissionRecordSerializer,
    CommissionRuleSerializer,
    DeliveryLineSerializer,
    DeliverySerializer,
    SalesOrderLineSerializer,
    SalesOrderSerializer,
    SalesQuotationLineSerializer,
    SalesQuotationSerializer,
    SalesReturnLineSerializer,
    SalesReturnSerializer,
)


def _accept_sales_quotation(self, request, *args, **kwargs):
    obj = self.get_object()
    obj.status = "accepted"
    obj.save(update_fields=["status", "updated_at"])
    return Response({"success": True, "data": SalesQuotationSerializer(obj).data})


def _send_sales_quotation(self, request, *args, **kwargs):
    obj = self.get_object()
    obj.status = "sent"
    obj.save(update_fields=["status", "updated_at"])
    return Response({"success": True, "data": SalesQuotationSerializer(obj).data})


def _confirm_sales_order(self, request, *args, **kwargs):
    obj = self.get_object()
    obj.status = "confirmed"
    obj.save(update_fields=["status", "updated_at"])
    return Response({"success": True, "data": SalesOrderSerializer(obj).data})


def _cancel_sales_order(self, request, *args, **kwargs):
    obj = self.get_object()
    obj.status = "cancelled"
    obj.save(update_fields=["status", "updated_at"])
    return Response({"success": True, "data": SalesOrderSerializer(obj).data})


def _dispatch_delivery(self, request, *args, **kwargs):
    obj = self.get_object()
    obj.status = "dispatched"
    obj.save(update_fields=["status", "updated_at"])
    return Response({"success": True, "data": DeliverySerializer(obj).data})


def _mark_delivery_delivered(self, request, *args, **kwargs):
    from django.utils import timezone

    obj = self.get_object()
    obj.status = "delivered"
    obj.actual_date = timezone.now()
    obj.save(update_fields=["status", "actual_date", "updated_at"])
    return Response({"success": True, "data": DeliverySerializer(obj).data})


def _approve_sales_return(self, request, *args, **kwargs):
    obj = self.get_object()
    obj.status = "approved"
    obj.save(update_fields=["status", "updated_at"])
    return Response({"success": True, "data": SalesReturnSerializer(obj).data})


SalesQuotationViewSet = build_model_viewset(
    SalesQuotation,
    SalesQuotationSerializer,
    permission_classes=[IsTenantUser],
    filterset_fields=["status", "client", "branch"],
    search_fields=["reference"],
    ordering_fields=["issue_date", "expiry_date"],
    select_related_fields=["client", "branch", "issued_by"],
    prefetch_related_fields=["lines"],
    extra_routes={
        "accept": build_action_route("accept", _accept_sales_quotation, methods=("post",), detail=True),
        "send": build_action_route("send", _send_sales_quotation, methods=("post",), detail=True),
    },
)

SalesQuotationLineViewSet = build_model_viewset(
    SalesQuotationLine,
    SalesQuotationLineSerializer,
    permission_classes=[IsTenantUser],
    filterset_fields=["quotation", "product"],
    select_related_fields=["quotation", "product"],
)

SalesOrderViewSet = build_model_viewset(
    SalesOrder,
    SalesOrderSerializer,
    permission_classes=[IsTenantUser],
    filterset_fields=["status", "client", "branch"],
    search_fields=["reference"],
    ordering_fields=["order_date"],
    select_related_fields=["client", "branch", "processed_by"],
    prefetch_related_fields=["lines"],
    extra_routes={
        "confirm": build_action_route("confirm", _confirm_sales_order, methods=("post",), detail=True),
        "cancel": build_action_route("cancel", _cancel_sales_order, methods=("post",), detail=True),
    },
)

SalesOrderLineViewSet = build_model_viewset(
    SalesOrderLine,
    SalesOrderLineSerializer,
    permission_classes=[IsTenantUser],
    filterset_fields=["order", "product"],
    select_related_fields=["order", "product"],
)

DeliveryViewSet = build_model_viewset(
    Delivery,
    DeliverySerializer,
    permission_classes=[IsTenantUser],
    filterset_fields=["status", "sales_order", "branch", "carrier"],
    search_fields=["reference", "tracking_number"],
    ordering_fields=["scheduled_date", "actual_date"],
    select_related_fields=["sales_order", "branch", "carrier", "driver"],
    prefetch_related_fields=["lines"],
    extra_routes={
        "dispatch": build_action_route("dispatch", _dispatch_delivery, methods=("post",), detail=True),
        "mark_delivered": build_action_route("mark_delivered", _mark_delivery_delivered, methods=("post",), detail=True),
    },
)

DeliveryLineViewSet = build_model_viewset(
    DeliveryLine,
    DeliveryLineSerializer,
    permission_classes=[IsTenantUser],
    filterset_fields=["delivery"],
    select_related_fields=["delivery", "so_line"],
)

SalesReturnViewSet = build_model_viewset(
    SalesReturn,
    SalesReturnSerializer,
    permission_classes=[IsTenantUser],
    filterset_fields=["status", "client", "reason"],
    search_fields=["reference"],
    ordering_fields=["return_date"],
    select_related_fields=["sales_order", "client"],
    prefetch_related_fields=["lines"],
    extra_routes={
        "approve": build_action_route("approve", _approve_sales_return, methods=("post",), detail=True),
    },
)

SalesReturnLineViewSet = build_model_viewset(
    SalesReturnLine,
    SalesReturnLineSerializer,
    permission_classes=[IsTenantUser],
    filterset_fields=["sales_return"],
    select_related_fields=["sales_return", "so_line"],
)

CommissionRuleViewSet = build_model_viewset(
    CommissionRule,
    CommissionRuleSerializer,
    permission_classes=[IsTenantUser],
    filterset_fields=["applies_to", "staff", "team"],
    search_fields=["name"],
    select_related_fields=["team", "staff"],
)

CommissionRecordViewSet = build_model_viewset(
    CommissionRecord,
    CommissionRecordSerializer,
    permission_classes=[IsTenantUser],
    filterset_fields=["status", "staff", "sales_order"],
    ordering_fields=["period"],
    select_related_fields=["rule", "staff", "sales_order"],
)
