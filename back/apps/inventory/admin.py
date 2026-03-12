from django.contrib import admin

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


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ("name", "sku", "company", "is_sellable", "is_purchasable", "is_active")
    list_filter = ("company", "is_active", "is_sellable", "is_purchasable", "is_serviceitem")
    search_fields = ("name", "sku", "brandname")


admin.site.register(unit)
admin.site.register(unitofmeasure)
admin.site.register(Category)
admin.site.register(Manufacturer)
admin.site.register(ManufacturerBrand)
admin.site.register(VariantType)
admin.site.register(VariantAttribute)
admin.site.register(selling_rules)
admin.site.register(Barcode)
admin.site.register(itemvariant)
admin.site.register(item_pricing_department)
admin.site.register(itemvariantprices)
admin.site.register(ItemLot)
admin.site.register(StockLotCostValuation)
admin.site.register(ItemInventoryLot)
admin.site.register(ItemInventoryLotVariant)
admin.site.register(StockLedgerEntry)
admin.site.register(itemInvJournalEntry)
admin.site.register(ReorderRule)
admin.site.register(StockAlert)
