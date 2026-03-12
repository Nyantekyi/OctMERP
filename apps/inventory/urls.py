from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    UnitCategoryViewSet, UnitViewSet, UnitOfMeasureViewSet,
    ManufacturerViewSet, ProductCategoryViewSet, VariantTypeViewSet, VariantValueViewSet,
    ProductViewSet, ProductVariantViewSet, BarcodeViewSet,
    SellingRulesViewSet, ItemPricingDepartmentViewSet, ItemVariantPricesViewSet,
    ItemLotViewSet, StockMoveViewSet, StockAdjustmentViewSet,
    StockAdjustmentLineViewSet, ReorderRuleViewSet,
)

app_name = "inventory"

router = DefaultRouter()
router.register("unit-categories", UnitCategoryViewSet, basename="unit-category")
router.register("units", UnitViewSet, basename="unit")
router.register("units-of-measure", UnitOfMeasureViewSet, basename="uom")
router.register("manufacturers", ManufacturerViewSet, basename="manufacturer")
router.register("product-categories", ProductCategoryViewSet, basename="product-category")
router.register("variant-types", VariantTypeViewSet, basename="variant-type")
router.register("variant-values", VariantValueViewSet, basename="variant-value")
router.register("products", ProductViewSet, basename="product")
router.register("product-variants", ProductVariantViewSet, basename="product-variant")
router.register("barcodes", BarcodeViewSet, basename="barcode")
router.register("selling-rules", SellingRulesViewSet, basename="selling-rules")
router.register("item-pricing", ItemPricingDepartmentViewSet, basename="item-pricing")
router.register("variant-prices", ItemVariantPricesViewSet, basename="variant-prices")
router.register("lots", ItemLotViewSet, basename="item-lot")
router.register("stock-moves", StockMoveViewSet, basename="stock-move")
router.register("stock-adjustments", StockAdjustmentViewSet, basename="stock-adjustment")
router.register("stock-adjustment-lines", StockAdjustmentLineViewSet, basename="stock-adjustment-line")
router.register("reorder-rules", ReorderRuleViewSet, basename="reorder-rule")

urlpatterns = [path("", include(router.urls))]

