"""apps/pos/views.py"""

from rest_framework.response import Response

from apps.common.api import build_action_route, build_model_viewset
from apps.common.permissions import IsTenantUser
from .models import CashDrawerEvent, POSConfig, POSOrder, POSOrderLine, POSPayment, POSSession
from .serializers import (
    CashDrawerEventSerializer,
    POSConfigSerializer,
    POSOrderLineSerializer,
    POSOrderSerializer,
    POSPaymentSerializer,
    POSSessionSerializer,
)


def _open_session(self, request, *args, **kwargs):
    session = self.get_object()
    session.open()
    return Response({"success": True, "data": POSSessionSerializer(session).data})


def _close_session(self, request, *args, **kwargs):
    session = self.get_object()
    counted = request.data.get("closing_balance", 0)
    currency = request.data.get("closing_balance_currency", "GHS")
    from djmoney.money import Money
    session.close(Money(counted, currency))
    return Response({"success": True, "data": POSSessionSerializer(session).data})


def _complete_order(self, request, *args, **kwargs):
    order = self.get_object()
    order.status = "paid"
    order.compute_change()
    order.save()
    return Response({"success": True, "data": POSOrderSerializer(order).data})


def _cancel_order(self, request, *args, **kwargs):
    order = self.get_object()
    order.status = "cancelled"
    order.save(update_fields=["status", "updated_at"])
    return Response({"success": True, "data": POSOrderSerializer(order).data})


POSConfigViewSet = build_model_viewset(
    POSConfig,
    POSConfigSerializer,
    permission_classes=[IsTenantUser],
    filterset_fields=["branch", "is_active"],
    search_fields=["name"],
    select_related_fields=["branch"],
)

POSSessionViewSet = build_model_viewset(
    POSSession,
    POSSessionSerializer,
    permission_classes=[IsTenantUser],
    filterset_fields=["config", "cashier", "status"],
    ordering_fields=["opened_at"],
    select_related_fields=["config", "cashier"],
    extra_routes={
        "open_session": build_action_route("open_session", _open_session, methods=("post",), detail=True),
        "close_session": build_action_route("close_session", _close_session, methods=("post",), detail=True),
    },
)


POSOrderViewSet = build_model_viewset(
    POSOrder,
    POSOrderSerializer,
    permission_classes=[IsTenantUser],
    filterset_fields=["status", "session", "client"],
    ordering_fields=["order_date"],
    select_related_fields=["session", "client"],
    prefetch_related_fields=["lines", "payments"],
    extra_routes={
        "complete": build_action_route("complete", _complete_order, methods=("post",), detail=True),
        "cancel": build_action_route("cancel", _cancel_order, methods=("post",), detail=True),
    },
)


POSOrderLineViewSet = build_model_viewset(
    POSOrderLine,
    POSOrderLineSerializer,
    permission_classes=[IsTenantUser],
    filterset_fields=["order", "product", "is_returned"],
    select_related_fields=["order", "product"],
)


POSPaymentViewSet = build_model_viewset(
    POSPayment,
    POSPaymentSerializer,
    permission_classes=[IsTenantUser],
    filterset_fields=["order", "payment_method"],
    ordering_fields=["payment_at"],
    select_related_fields=["order"],
)

CashDrawerEventViewSet = build_model_viewset(
    CashDrawerEvent,
    CashDrawerEventSerializer,
    permission_classes=[IsTenantUser],
    filterset_fields=["session", "event_type"],
    ordering_fields=["occurred_at"],
    select_related_fields=["session", "performed_by"],
)
