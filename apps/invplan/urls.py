from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    TermsAndConditionViewSet, InventoryConditionViewSet, CarrierViewSet,
    OrderDocumentViewSet, OrderDocumentAttachmentViewSet, OrderDocumentDetailViewSet,
)

app_name = "invplan"

router = DefaultRouter()
router.register("terms", TermsAndConditionViewSet, basename="terms")
router.register("conditions", InventoryConditionViewSet, basename="condition")
router.register("carriers", CarrierViewSet, basename="carrier")
router.register("order-documents", OrderDocumentViewSet, basename="order-document")
router.register("order-attachments", OrderDocumentAttachmentViewSet, basename="order-attachment")
router.register("order-lines", OrderDocumentDetailViewSet, basename="order-line")

urlpatterns = [path("", include(router.urls))]

