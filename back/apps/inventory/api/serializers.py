from apps.common.api import build_model_serializer
from apps.inventory.models import (
    Barcode,
    Category,
    Item,
    ItemInventoryLot,
    ItemInventoryLotVariant,
    ItemLot,
    Manufacturer,
    ManufacturerBrand,
    ReorderRule,
    StockAlert,
    StockLedgerEntry,
    StockLotCostValuation,
    VariantAttribute,
    VariantType,
    item_pricing_department,
    itemInvJournalEntry,
    itemvariant,
    itemvariantprices,
    selling_rules,
    unit,
    unitofmeasure,
)

UnitSerializer = build_model_serializer(unit)
UnitOfMeasureSerializer = build_model_serializer(unitofmeasure)
CategorySerializer = build_model_serializer(Category)
ManufacturerSerializer = build_model_serializer(Manufacturer)
ManufacturerBrandSerializer = build_model_serializer(ManufacturerBrand)
VariantTypeSerializer = build_model_serializer(VariantType)
VariantAttributeSerializer = build_model_serializer(VariantAttribute)
SellingRulesSerializer = build_model_serializer(selling_rules)
BarcodeSerializer = build_model_serializer(Barcode)

ItemvariantSerializer = build_model_serializer(itemvariant)

ItemSerializer = build_model_serializer(
    Item,
    nested_serializers={
        "variants": {
            "serializer": ItemvariantSerializer,
            "many": True,
            "required": False,
        }
    },
)

ItemPricingDepartmentSerializer = build_model_serializer(item_pricing_department)
ItemvariantpricesSerializer = build_model_serializer(itemvariantprices)
ItemLotSerializer = build_model_serializer(ItemLot)
StockLotCostValuationSerializer = build_model_serializer(StockLotCostValuation)
ItemInventoryLotSerializer = build_model_serializer(ItemInventoryLot)
ItemInventoryLotVariantSerializer = build_model_serializer(ItemInventoryLotVariant)
StockLedgerEntrySerializer = build_model_serializer(StockLedgerEntry)
ItemInvJournalEntrySerializer = build_model_serializer(itemInvJournalEntry)
ReorderRuleSerializer = build_model_serializer(ReorderRule)
StockAlertSerializer = build_model_serializer(StockAlert)
