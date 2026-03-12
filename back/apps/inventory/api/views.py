from apps.common.api import build_model_viewset
from apps.inventory.api.serializers import (
	BarcodeSerializer, BrandSerializer, CategorySerializer, FormSerializer,
	ItemInventoryLotSerializer, ItemLotSerializer, ItemPricingDepartmentSerializer,
	ManufacturerBrandSerializer, ManufacturerSerializer, PackSizeSerializer,
	ProductSerializer, ProductVariantSerializer, ReorderRuleSerializer,
	StockAlertSerializer, StockMoveSerializer, UnitOfMeasureSerializer,
	WarehouseLocationSerializer, WarehouseSerializer,
)
from apps.inventory.models import (
	Barcode, Brand, Category, Form, ItemInventoryLot, ItemLot,
	ItemPricingDepartment, Manufacturer, ManufacturerBrand, PackSize,
	Product, ProductVariant, ReorderRule, StockAlert, StockMove,
	UnitOfMeasure, Warehouse, WarehouseLocation,
)

CategoryViewSet = build_model_viewset(Category, CategorySerializer, search_fields=("name", "slug"), filterset_fields=("company", "is_active"), soft_delete=True)
ManufacturerViewSet = build_model_viewset(Manufacturer, ManufacturerSerializer, search_fields=("name",), filterset_fields=("company", "is_active"), soft_delete=True)
ManufacturerBrandViewSet = build_model_viewset(ManufacturerBrand, ManufacturerBrandSerializer, search_fields=("name",), filterset_fields=("manufacturer", "is_active"), soft_delete=True)
BrandViewSet = build_model_viewset(Brand, BrandSerializer, search_fields=("name",), filterset_fields=("company", "is_active"), soft_delete=True)
UnitOfMeasureViewSet = build_model_viewset(UnitOfMeasure, UnitOfMeasureSerializer, search_fields=("name", "abbreviation"), filterset_fields=("company", "is_active"), soft_delete=True)
FormViewSet = build_model_viewset(Form, FormSerializer, search_fields=("name",), filterset_fields=("company", "is_active"), soft_delete=True)
PackSizeViewSet = build_model_viewset(PackSize, PackSizeSerializer, search_fields=("name",), filterset_fields=("company", "uom", "is_active"), soft_delete=True)
ProductViewSet = build_model_viewset(
	Product, ProductSerializer,
	search_fields=("name", "sku"),
	filterset_fields=("company", "category", "brand", "manufacturer", "form", "pack_size", "tax", "is_active", "is_sellable", "is_purchasable"),
	prefetch_related_fields=("variants", "barcodes"),
	soft_delete=True,
)
BarcodeViewSet = build_model_viewset(Barcode, BarcodeSerializer, search_fields=("value",), filterset_fields=("product", "barcode_type"))
ProductVariantViewSet = build_model_viewset(ProductVariant, ProductVariantSerializer, search_fields=("code",), filterset_fields=("product", "company", "is_active"), soft_delete=True)
ItemPricingDepartmentViewSet = build_model_viewset(ItemPricingDepartment, ItemPricingDepartmentSerializer, filterset_fields=("product", "variant", "branch", "department", "company", "is_active"), soft_delete=True)
WarehouseViewSet = build_model_viewset(Warehouse, WarehouseSerializer, search_fields=("name", "code"), filterset_fields=("company", "branch", "is_active"), soft_delete=True)
WarehouseLocationViewSet = build_model_viewset(WarehouseLocation, WarehouseLocationSerializer, search_fields=("code", "name"), filterset_fields=("warehouse", "is_active"), soft_delete=True)
ItemLotViewSet = build_model_viewset(ItemLot, ItemLotSerializer, search_fields=("lot_number",), filterset_fields=("product", "variant", "expiry_date", "is_active"), soft_delete=True)
ItemInventoryLotViewSet = build_model_viewset(ItemInventoryLot, ItemInventoryLotSerializer, filterset_fields=("lot", "warehouse", "location", "is_active"), soft_delete=True)
StockMoveViewSet = build_model_viewset(StockMove, StockMoveSerializer, filterset_fields=("product", "warehouse", "move_type"), ordering_fields=("created_at",))
ReorderRuleViewSet = build_model_viewset(ReorderRule, ReorderRuleSerializer, filterset_fields=("product", "warehouse", "is_active"), soft_delete=True)
StockAlertViewSet = build_model_viewset(StockAlert, StockAlertSerializer, filterset_fields=("product", "warehouse", "alert_type", "is_active"), soft_delete=True)
