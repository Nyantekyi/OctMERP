"""apps/invplan/serializers.py"""

from apps.common.api import build_model_serializer

from .models import (
    Carrier,
    InventoryCondition,
    OrderDocument,
    OrderDocumentAttachment,
    OrderDocumentDetail,
    TermsAndCondition,
)


TermsAndConditionSerializer = build_model_serializer(TermsAndCondition)
InventoryConditionSerializer = build_model_serializer(InventoryCondition)
CarrierSerializer = build_model_serializer(Carrier)
OrderDocumentAttachmentSerializer = build_model_serializer(OrderDocumentAttachment)
OrderDocumentDetailSerializer = build_model_serializer(
    OrderDocumentDetail,
    read_only_fields=("qty_base", "line_total"),
)
OrderDocumentSerializer = build_model_serializer(
    OrderDocument,
    read_only_fields=("title",),
    nested_serializers={
        "lines": {
            "serializer": OrderDocumentDetailSerializer,
            "many": True,
            "required": False,
            "read_only": True,
        },
        "attachments": {
            "serializer": OrderDocumentAttachmentSerializer,
            "many": True,
            "required": False,
            "read_only": True,
        },
    },
)
