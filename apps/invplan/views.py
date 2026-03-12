"""apps/invplan/views.py"""

from rest_framework.response import Response

from apps.common.api import build_action_route, build_model_viewset
from apps.common.permissions import IsTenantUser
from .models import (
    Carrier,
    InventoryCondition,
    OrderDocument,
    OrderDocumentAttachment,
    OrderDocumentDetail,
    TermsAndCondition,
)
from .serializers import (
    CarrierSerializer,
    InventoryConditionSerializer,
    OrderDocumentAttachmentSerializer,
    OrderDocumentDetailSerializer,
    OrderDocumentSerializer,
    TermsAndConditionSerializer,
)


def _set_doc_status(self, request, status_value):
    doc = self.get_object()
    doc.status = status_value
    doc.save(update_fields=["status", "updated_at"])
    return Response({"success": True, "data": OrderDocumentSerializer(doc).data})


def _approve_document(self, request, *args, **kwargs):
    return _set_doc_status(self, request, "approved")


def _fulfill_document(self, request, *args, **kwargs):
    return _set_doc_status(self, request, "fulfilled")


def _cancel_document(self, request, *args, **kwargs):
    return _set_doc_status(self, request, "canceled")


TermsAndConditionViewSet = build_model_viewset(
    TermsAndCondition,
    TermsAndConditionSerializer,
    permission_classes=[IsTenantUser],
    search_fields=["code"],
    filterset_fields=["is_active"],
)

InventoryConditionViewSet = build_model_viewset(
    InventoryCondition,
    InventoryConditionSerializer,
    permission_classes=[IsTenantUser],
    search_fields=["name"],
)


CarrierViewSet = build_model_viewset(
    Carrier,
    CarrierSerializer,
    permission_classes=[IsTenantUser],
    search_fields=["name"],
    filterset_fields=["is_active"],
)


OrderDocumentViewSet = build_model_viewset(
    OrderDocument,
    OrderDocumentSerializer,
    permission_classes=[IsTenantUser],
    filterset_fields=["ordertype", "status", "branch", "vendor", "client"],
    search_fields=["title"],
    ordering_fields=["created_at", "expected_delivery_date"],
    select_related_fields=["branch", "staff", "vendor", "client", "sourcebranch", "carrier", "terms"],
    prefetch_related_fields=["lines", "attachments"],
    extra_routes={
        "approve": build_action_route("approve", _approve_document, methods=("post",), detail=True),
        "fulfill": build_action_route("fulfill", _fulfill_document, methods=("post",), detail=True),
        "cancel": build_action_route("cancel", _cancel_document, methods=("post",), detail=True),
    },
)

OrderDocumentAttachmentViewSet = build_model_viewset(
    OrderDocumentAttachment,
    OrderDocumentAttachmentSerializer,
    permission_classes=[IsTenantUser],
    filterset_fields=["order_document"],
    select_related_fields=["order_document"],
)

OrderDocumentDetailViewSet = build_model_viewset(
    OrderDocumentDetail,
    OrderDocumentDetailSerializer,
    permission_classes=[IsTenantUser],
    filterset_fields=["order", "item"],
    select_related_fields=["order", "item", "uom"],
)
