from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    PurchaseRequisitionViewSet, PurchaseRequisitionLineViewSet,
    RFQViewSet, RFQLineViewSet,
    PurchaseOrderViewSet, PurchaseOrderLineViewSet,
    GoodsReceiptNoteViewSet, GRNLineViewSet,
    VendorContractViewSet, SupplierEvaluationViewSet,
)

app_name = "procurement"

router = DefaultRouter()
router.register("requisitions", PurchaseRequisitionViewSet, basename="requisition")
router.register("requisition-lines", PurchaseRequisitionLineViewSet, basename="requisition-line")
router.register("rfqs", RFQViewSet, basename="rfq")
router.register("rfq-lines", RFQLineViewSet, basename="rfq-line")
router.register("purchase-orders", PurchaseOrderViewSet, basename="purchase-order")
router.register("purchase-order-lines", PurchaseOrderLineViewSet, basename="po-line")
router.register("grns", GoodsReceiptNoteViewSet, basename="grn")
router.register("grn-lines", GRNLineViewSet, basename="grn-line")
router.register("vendor-contracts", VendorContractViewSet, basename="vendor-contract")
router.register("supplier-evaluations", SupplierEvaluationViewSet, basename="supplier-evaluation")

urlpatterns = [path("", include(router.urls))]

