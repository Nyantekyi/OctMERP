"""
apps/invplan/views.py
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.common.permissions import IsTenantUser, IsManager
from .models import (
    TermsAndCondition, InventoryCondition, Carrier,
    OrderDocument, OrderDocumentAttachment, OrderDocumentDetail,
)
from .serializers import (
    TermsAndConditionSerializer, InventoryConditionSerializer, CarrierSerializer,
    OrderDocumentSerializer, OrderDocumentAttachmentSerializer, OrderDocumentDetailSerializer,
)


class TermsAndConditionViewSet(viewsets.ModelViewSet):
    queryset = TermsAndCondition.objects.all()
    serializer_class = TermsAndConditionSerializer
    permission_classes = [IsTenantUser]
    search_fields = ["code"]
    filterset_fields = ["is_active"]


class InventoryConditionViewSet(viewsets.ModelViewSet):
    queryset = InventoryCondition.objects.all()
    serializer_class = InventoryConditionSerializer
    permission_classes = [IsTenantUser]
    search_fields = ["name"]


class CarrierViewSet(viewsets.ModelViewSet):
    queryset = Carrier.objects.all()
    serializer_class = CarrierSerializer
    permission_classes = [IsTenantUser]
    search_fields = ["name"]
    filterset_fields = ["is_active"]


class OrderDocumentViewSet(viewsets.ModelViewSet):
    queryset = OrderDocument.objects.select_related(
        "branch", "staff", "vendor", "client", "sourcebranch", "carrier", "terms"
    ).prefetch_related("lines", "attachments")
    serializer_class = OrderDocumentSerializer
    permission_classes = [IsTenantUser]
    filterset_fields = ["ordertype", "status", "branch", "vendor", "client"]
    search_fields = ["title"]
    ordering_fields = ["created_at", "expected_delivery_date"]

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        doc = self.get_object()
        doc.status = "approved"
        doc.save()
        return Response({"success": True, "data": OrderDocumentSerializer(doc).data})

    @action(detail=True, methods=["post"])
    def fulfill(self, request, pk=None):
        doc = self.get_object()
        doc.status = "fulfilled"
        doc.save()
        return Response({"success": True, "data": OrderDocumentSerializer(doc).data})

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        doc = self.get_object()
        doc.status = "canceled"
        doc.save()
        return Response({"success": True, "data": OrderDocumentSerializer(doc).data})


class OrderDocumentAttachmentViewSet(viewsets.ModelViewSet):
    queryset = OrderDocumentAttachment.objects.select_related("order_document")
    serializer_class = OrderDocumentAttachmentSerializer
    permission_classes = [IsTenantUser]
    filterset_fields = ["order_document"]


class OrderDocumentDetailViewSet(viewsets.ModelViewSet):
    queryset = OrderDocumentDetail.objects.select_related("order", "item", "uom")
    serializer_class = OrderDocumentDetailSerializer
    permission_classes = [IsTenantUser]
    filterset_fields = ["order", "item"]
