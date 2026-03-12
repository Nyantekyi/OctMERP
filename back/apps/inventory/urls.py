from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.inventory.api.views import (
	BarcodeViewSet, BrandViewSet, CategoryViewSet, FormViewSet,
	ItemInventoryLotViewSet, ItemLotViewSet, ItemPricingDepartmentViewSet,
	ManufacturerBrandViewSet, ManufacturerViewSet, PackSizeViewSet,
	ProductVariantViewSet, ProductViewSet, ReorderRuleViewSet,
	StockAlertViewSet, StockMoveViewSet, UnitOfMeasureViewSet,
	WarehouseLocationViewSet, WarehouseViewSet,
)

router = DefaultRouter()
router.register("categories", CategoryViewSet, basename="inventory-category")
router.register("manufacturers", ManufacturerViewSet, basename="inventory-manufacturer")
router.register("manufacturer-brands", ManufacturerBrandViewSet, basename="inventory-manufacturer-brand")
router.register("brands", BrandViewSet, basename="inventory-brand")
router.register("units", UnitOfMeasureViewSet, basename="inventory-uom")
router.register("forms", FormViewSet, basename="inventory-form")
router.register("pack-sizes", PackSizeViewSet, basename="inventory-pack-size")
router.register("products", ProductViewSet, basename="inventory-product")
router.register("barcodes", BarcodeViewSet, basename="inventory-barcode")
router.register("variants", ProductVariantViewSet, basename="inventory-variant")
router.register("pricing", ItemPricingDepartmentViewSet, basename="inventory-pricing")
router.register("warehouses", WarehouseViewSet, basename="inventory-warehouse")
router.register("locations", WarehouseLocationViewSet, basename="inventory-location")
router.register("lots", ItemLotViewSet, basename="inventory-lot")
router.register("lot-stock", ItemInventoryLotViewSet, basename="inventory-lot-stock")
router.register("moves", StockMoveViewSet, basename="inventory-move")
router.register("reorder-rules", ReorderRuleViewSet, basename="inventory-reorder-rule")
router.register("alerts", StockAlertViewSet, basename="inventory-alert")

urlpatterns = [path("", include(router.urls))]
