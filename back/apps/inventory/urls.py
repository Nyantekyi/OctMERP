from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.inventory.api.views import (
    BarcodeViewSet,
    CategoryViewSet,
    ItemInvJournalEntryViewSet,
    ItemInventoryLotVariantViewSet,
    ItemInventoryLotViewSet,
    ItemLotViewSet,
    ItemPricingDepartmentViewSet,
    ItemViewSet,
    ItemvariantViewSet,
    ItemvariantpricesViewSet,
    ManufacturerBrandViewSet,
    ManufacturerViewSet,
    ReorderRuleViewSet,
    SellingRulesViewSet,
    StockAlertViewSet,
    StockLedgerEntryViewSet,
    StockLotCostValuationViewSet,
    UnitOfMeasureViewSet,
    UnitViewSet,
    VariantAttributeViewSet,
    VariantTypeViewSet,
)

router = DefaultRouter()
router.register("units", UnitViewSet, basename="inventory-unit")
router.register("uom", UnitOfMeasureViewSet, basename="inventory-uom")
router.register("categories", CategoryViewSet, basename="inventory-category")
router.register("manufacturers", ManufacturerViewSet, basename="inventory-manufacturer")
router.register("manufacturer-brands", ManufacturerBrandViewSet, basename="inventory-manufacturer-brand")
router.register("variant-types", VariantTypeViewSet, basename="inventory-variant-type")
router.register("variant-attributes", VariantAttributeViewSet, basename="inventory-variant-attribute")
router.register("selling-rules", SellingRulesViewSet, basename="inventory-selling-rules")
router.register("items", ItemViewSet, basename="inventory-item")
router.register("barcodes", BarcodeViewSet, basename="inventory-barcode")
router.register("item-variants", ItemvariantViewSet, basename="inventory-item-variant")
router.register("pricing", ItemPricingDepartmentViewSet, basename="inventory-pricing")
router.register("variant-prices", ItemvariantpricesViewSet, basename="inventory-variant-prices")
router.register("lots", ItemLotViewSet, basename="inventory-lot")
router.register("lot-cost-valuations", StockLotCostValuationViewSet, basename="inventory-lot-cost")
router.register("lot-stock", ItemInventoryLotViewSet, basename="inventory-lot-stock")
router.register("lot-variant-stock", ItemInventoryLotVariantViewSet, basename="inventory-lot-variant-stock")
router.register("ledger", StockLedgerEntryViewSet, basename="inventory-ledger")
router.register("journal", ItemInvJournalEntryViewSet, basename="inventory-journal")
router.register("reorder-rules", ReorderRuleViewSet, basename="inventory-reorder-rule")
router.register("alerts", StockAlertViewSet, basename="inventory-alert")

urlpatterns = [path("", include(router.urls))]
