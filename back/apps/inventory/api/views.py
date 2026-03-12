from apps.common.api import build_model_viewset
from apps.inventory.api.serializers import (
    BarcodeSerializer,
    CategorySerializer,
    ItemInvJournalEntrySerializer,
    ItemInventoryLotSerializer,
    ItemInventoryLotVariantSerializer,
    ItemLotSerializer,
    ItemPricingDepartmentSerializer,
    ItemSerializer,
    ItemvariantSerializer,
    ItemvariantpricesSerializer,
    ManufacturerBrandSerializer,
    ManufacturerSerializer,
    ReorderRuleSerializer,
    SellingRulesSerializer,
    StockAlertSerializer,
    StockLedgerEntrySerializer,
    StockLotCostValuationSerializer,
    UnitOfMeasureSerializer,
    UnitSerializer,
    VariantAttributeSerializer,
    VariantTypeSerializer,
)
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

UnitViewSet = build_model_viewset(unit, UnitSerializer, search_fields=("name", "abr"), filterset_fields=("company", "is_active"), soft_delete=True)
UnitOfMeasureViewSet = build_model_viewset(unitofmeasure, UnitOfMeasureSerializer, filterset_fields=("company", "is_active"), soft_delete=True)
CategoryViewSet = build_model_viewset(Category, CategorySerializer, search_fields=("name", "slug"), filterset_fields=("company", "is_active"), soft_delete=True)
ManufacturerViewSet = build_model_viewset(Manufacturer, ManufacturerSerializer, search_fields=("name",), filterset_fields=("company", "is_active"), soft_delete=True)
ManufacturerBrandViewSet = build_model_viewset(ManufacturerBrand, ManufacturerBrandSerializer, search_fields=("name",), filterset_fields=("manufacturer", "is_active"), soft_delete=True)
VariantTypeViewSet = build_model_viewset(VariantType, VariantTypeSerializer, search_fields=("name",), filterset_fields=("company", "is_active"), soft_delete=True)
VariantAttributeViewSet = build_model_viewset(VariantAttribute, VariantAttributeSerializer, search_fields=("name",), filterset_fields=("variant_type", "company", "is_active"), soft_delete=True)
SellingRulesViewSet = build_model_viewset(selling_rules, SellingRulesSerializer, search_fields=("name",), filterset_fields=("department", "is_active"), soft_delete=True)
ItemViewSet = build_model_viewset(
    Item,
    ItemSerializer,
    search_fields=("name", "sku", "brandname"),
    filterset_fields=("company", "category", "manufacturer", "tax", "is_active", "is_sellable", "is_purchasable", "is_serviceitem"),
    prefetch_related_fields=("variants",),
    soft_delete=True,
)
BarcodeViewSet = build_model_viewset(Barcode, BarcodeSerializer, search_fields=("value",), filterset_fields=("item", "barcode_type"))
ItemvariantViewSet = build_model_viewset(itemvariant, ItemvariantSerializer, search_fields=("name",), filterset_fields=("item", "company", "is_active"), soft_delete=True)
ItemPricingDepartmentViewSet = build_model_viewset(item_pricing_department, ItemPricingDepartmentSerializer, filterset_fields=("item", "sale_department", "company", "is_active"), soft_delete=True)
ItemvariantpricesViewSet = build_model_viewset(itemvariantprices, ItemvariantpricesSerializer, filterset_fields=("variant_item", "itempricingdepartment", "is_active"), soft_delete=True)
ItemLotViewSet = build_model_viewset(ItemLot, ItemLotSerializer, search_fields=("lot_number",), filterset_fields=("item", "variant", "is_active"), soft_delete=True)
StockLotCostValuationViewSet = build_model_viewset(StockLotCostValuation, StockLotCostValuationSerializer, filterset_fields=("itemlot", "cost_department"))
ItemInventoryLotViewSet = build_model_viewset(ItemInventoryLot, ItemInventoryLotSerializer, filterset_fields=("itemlot", "location", "inventory_state", "is_active"), soft_delete=True)
ItemInventoryLotVariantViewSet = build_model_viewset(ItemInventoryLotVariant, ItemInventoryLotVariantSerializer, filterset_fields=("lot", "variant"))
StockLedgerEntryViewSet = build_model_viewset(StockLedgerEntry, StockLedgerEntrySerializer, filterset_fields=("branch", "inventorytransacttype"), ordering_fields=("created_at",))
ItemInvJournalEntryViewSet = build_model_viewset(itemInvJournalEntry, ItemInvJournalEntrySerializer, filterset_fields=("itemlot", "location", "inventory_state"), ordering_fields=("created_at",))
ReorderRuleViewSet = build_model_viewset(ReorderRule, ReorderRuleSerializer, filterset_fields=("item", "branch", "is_active"), soft_delete=True)
StockAlertViewSet = build_model_viewset(StockAlert, StockAlertSerializer, filterset_fields=("item", "branch", "alert_type", "is_active"), soft_delete=True)
