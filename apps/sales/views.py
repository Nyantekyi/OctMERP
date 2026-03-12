"""
apps/sales/views.py
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.common.permissions import IsTenantUser, IsManager
from .models import (
    SalesQuotation, SalesQuotationLine,
    SalesOrder, SalesOrderLine,
    Delivery, DeliveryLine,
    SalesReturn, SalesReturnLine,
    CommissionRule, CommissionRecord,
)
from .serializers import (
    SalesQuotationSerializer, SalesQuotationLineSerializer,
    SalesOrderSerializer, SalesOrderLineSerializer,
    DeliverySerializer, DeliveryLineSerializer,
    SalesReturnSerializer, SalesReturnLineSerializer,
    CommissionRuleSerializer, CommissionRecordSerializer,
)


class SalesQuotationViewSet(viewsets.ModelViewSet):
    queryset = SalesQuotation.objects.select_related("client", "branch", "issued_by").prefetch_related("lines")
    serializer_class = SalesQuotationSerializer
    permission_classes = [IsTenantUser]
    filterset_fields = ["status", "client", "branch"]
    search_fields = ["reference"]
    ordering_fields = ["issue_date", "expiry_date"]

    @action(detail=True, methods=["post"])
    def accept(self, request, pk=None):
        obj = self.get_object()
        obj.status = "accepted"
        obj.save()
        return Response({"success": True, "data": SalesQuotationSerializer(obj).data})

    @action(detail=True, methods=["post"])
    def send(self, request, pk=None):
        obj = self.get_object()
        obj.status = "sent"
        obj.save()
        return Response({"success": True, "data": SalesQuotationSerializer(obj).data})


class SalesQuotationLineViewSet(viewsets.ModelViewSet):
    queryset = SalesQuotationLine.objects.select_related("quotation", "product")
    serializer_class = SalesQuotationLineSerializer
    permission_classes = [IsTenantUser]
    filterset_fields = ["quotation", "product"]


class SalesOrderViewSet(viewsets.ModelViewSet):
    queryset = SalesOrder.objects.select_related("client", "branch", "processed_by").prefetch_related("lines")
    serializer_class = SalesOrderSerializer
    permission_classes = [IsTenantUser]
    filterset_fields = ["status", "client", "branch"]
    search_fields = ["reference"]
    ordering_fields = ["order_date"]

    @action(detail=True, methods=["post"])
    def confirm(self, request, pk=None):
        obj = self.get_object()
        obj.status = "confirmed"
        obj.save()
        return Response({"success": True, "data": SalesOrderSerializer(obj).data})

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        obj = self.get_object()
        obj.status = "cancelled"
        obj.save()
        return Response({"success": True, "data": SalesOrderSerializer(obj).data})


class SalesOrderLineViewSet(viewsets.ModelViewSet):
    queryset = SalesOrderLine.objects.select_related("order", "product")
    serializer_class = SalesOrderLineSerializer
    permission_classes = [IsTenantUser]
    filterset_fields = ["order", "product"]


class DeliveryViewSet(viewsets.ModelViewSet):
    queryset = Delivery.objects.select_related("sales_order", "branch", "carrier", "driver").prefetch_related("lines")
    serializer_class = DeliverySerializer
    permission_classes = [IsTenantUser]
    filterset_fields = ["status", "sales_order", "branch", "carrier"]
    search_fields = ["reference", "tracking_number"]
    ordering_fields = ["scheduled_date", "actual_date"]

    @action(detail=True, methods=["post"])
    def dispatch(self, request, pk=None):
        obj = self.get_object()
        obj.status = "dispatched"
        obj.save()
        return Response({"success": True, "data": DeliverySerializer(obj).data})

    @action(detail=True, methods=["post"])
    def mark_delivered(self, request, pk=None):
        from django.utils import timezone
        obj = self.get_object()
        obj.status = "delivered"
        obj.actual_date = timezone.now()
        obj.save()
        return Response({"success": True, "data": DeliverySerializer(obj).data})


class DeliveryLineViewSet(viewsets.ModelViewSet):
    queryset = DeliveryLine.objects.select_related("delivery", "so_line")
    serializer_class = DeliveryLineSerializer
    permission_classes = [IsTenantUser]
    filterset_fields = ["delivery"]


class SalesReturnViewSet(viewsets.ModelViewSet):
    queryset = SalesReturn.objects.select_related("sales_order", "client").prefetch_related("lines")
    serializer_class = SalesReturnSerializer
    permission_classes = [IsTenantUser]
    filterset_fields = ["status", "client", "reason"]
    search_fields = ["reference"]
    ordering_fields = ["return_date"]

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        obj = self.get_object()
        obj.status = "approved"
        obj.save()
        return Response({"success": True, "data": SalesReturnSerializer(obj).data})


class SalesReturnLineViewSet(viewsets.ModelViewSet):
    queryset = SalesReturnLine.objects.select_related("sales_return", "so_line")
    serializer_class = SalesReturnLineSerializer
    permission_classes = [IsTenantUser]
    filterset_fields = ["sales_return"]


class CommissionRuleViewSet(viewsets.ModelViewSet):
    queryset = CommissionRule.objects.select_related("team", "staff")
    serializer_class = CommissionRuleSerializer
    permission_classes = [IsTenantUser]
    filterset_fields = ["applies_to", "staff", "team"]
    search_fields = ["name"]


class CommissionRecordViewSet(viewsets.ModelViewSet):
    queryset = CommissionRecord.objects.select_related("rule", "staff", "sales_order")
    serializer_class = CommissionRecordSerializer
    permission_classes = [IsTenantUser]
    filterset_fields = ["status", "staff", "sales_order"]
    ordering_fields = ["period"]
