from apps.common.api import build_model_serializer
from apps.inventory.models import (
    Barcode, Brand, Category, Form, ItemInventoryLot, ItemLot,
    ItemPricingDepartment, ManufacturerBrand, Manufacturer, PackSize,
    Product, ProductVariant, ReorderRule, StockAlert, StockMove,
    UnitOfMeasure, Warehouse, WarehouseLocation,
)

CategorySerializer = build_model_serializer(Category)
ManufacturerSerializer = build_model_serializer(Manufacturer)
ManufacturerBrandSerializer = build_model_serializer(ManufacturerBrand)
BrandSerializer = build_model_serializer(Brand)
UnitOfMeasureSerializer = build_model_serializer(UnitOfMeasure)
FormSerializer = build_model_serializer(Form)
PackSizeSerializer = build_model_serializer(PackSize)
BarcodeSerializer = build_model_serializer(Barcode)
ProductVariantSerializer = build_model_serializer(ProductVariant)

ProductSerializer = build_model_serializer(
    Product,
    nested_serializers={
        "variants": {
            "serializer": ProductVariantSerializer,
            "many": True,
            "required": False,
        }
    },
)

WarehouseSerializer = build_model_serializer(Warehouse)
WarehouseLocationSerializer = build_model_serializer(WarehouseLocation)
ItemPricingDepartmentSerializer = build_model_serializer(ItemPricingDepartment)
ItemLotSerializer = build_model_serializer(ItemLot)
ItemInventoryLotSerializer = build_model_serializer(ItemInventoryLot)
StockMoveSerializer = build_model_serializer(StockMove)
ReorderRuleSerializer = build_model_serializer(ReorderRule)
StockAlertSerializer = build_model_serializer(StockAlert)
