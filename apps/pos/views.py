"""
apps/pos/views.py
"""
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.common.permissions import IsTenantUser, IsManager
from .models import POSConfig, POSSession, POSOrder, POSOrderLine, POSPayment, CashDrawerEvent
from .serializers import (
    POSConfigSerializer, POSSessionSerializer, POSOrderSerializer,
    POSOrderLineSerializer, POSPaymentSerializer, CashDrawerEventSerializer,
)


class POSConfigViewSet(viewsets.ModelViewSet):
    queryset = POSConfig.objects.select_related("branch")
    serializer_class = POSConfigSerializer
    permission_classes = [IsTenantUser]
    filterset_fields = ["branch", "is_active"]
    search_fields = ["name"]


class POSSessionViewSet(viewsets.ModelViewSet):
    queryset = POSSession.objects.select_related("config", "cashier")
    serializer_class = POSSessionSerializer
    permission_classes = [IsTenantUser]
    filterset_fields = ["config", "cashier", "status"]
    ordering_fields = ["opened_at"]

    @action(detail=True, methods=["post"])
    def open_session(self, request, pk=None):
        session = self.get_object()
        session.open()
        return Response({"success": True, "data": POSSessionSerializer(session).data})

    @action(detail=True, methods=["post"])
    def close_session(self, request, pk=None):
        session = self.get_object()
        counted = request.data.get("closing_balance", 0)
        currency = request.data.get("closing_balance_currency", "GHS")
        from djmoney.money import Money
        session.close(Money(counted, currency))
        return Response({"success": True, "data": POSSessionSerializer(session).data})


class POSOrderViewSet(viewsets.ModelViewSet):
    queryset = POSOrder.objects.select_related("session", "client").prefetch_related("lines", "payments")
    serializer_class = POSOrderSerializer
    permission_classes = [IsTenantUser]
    filterset_fields = ["status", "session", "client"]
    ordering_fields = ["order_date"]

    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        order = self.get_object()
        order.status = "paid"
        order.compute_change()
        order.save()
        return Response({"success": True, "data": POSOrderSerializer(order).data})

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        order = self.get_object()
        order.status = "cancelled"
        order.save()
        return Response({"success": True, "data": POSOrderSerializer(order).data})


class POSOrderLineViewSet(viewsets.ModelViewSet):
    queryset = POSOrderLine.objects.select_related("order", "product")
    serializer_class = POSOrderLineSerializer
    permission_classes = [IsTenantUser]
    filterset_fields = ["order", "product", "is_returned"]


class POSPaymentViewSet(viewsets.ModelViewSet):
    queryset = POSPayment.objects.select_related("order")
    serializer_class = POSPaymentSerializer
    permission_classes = [IsTenantUser]
    filterset_fields = ["order", "payment_method"]
    ordering_fields = ["payment_at"]


class CashDrawerEventViewSet(viewsets.ModelViewSet):
    queryset = CashDrawerEvent.objects.select_related("session", "performed_by")
    serializer_class = CashDrawerEventSerializer
    permission_classes = [IsTenantUser]
    filterset_fields = ["session", "event_type"]
    ordering_fields = ["occurred_at"]
