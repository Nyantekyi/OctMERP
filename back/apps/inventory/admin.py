from django.contrib import admin

from apps.inventory.models import (
    Barcode,
    Brand,
    Category,
    Form,
    ItemInventoryLot,
    ItemLot,
    ItemPricingDepartment,
    Manufacturer,
    ManufacturerBrand,
    PackSize,
    Product,
    ProductVariant,
    ReorderRule,
    StockAlert,
    StockMove,
    UnitOfMeasure,
    Warehouse,
    WarehouseLocation,
)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "sku", "company", "sale_price", "is_active")
    list_filter = ("company", "is_active", "is_sellable", "is_purchasable")
    search_fields = ("name", "sku")


admin.site.register(Category)
admin.site.register(Manufacturer)
admin.site.register(ManufacturerBrand)
admin.site.register(Brand)
admin.site.register(UnitOfMeasure)
admin.site.register(Form)
admin.site.register(PackSize)
admin.site.register(Barcode)
admin.site.register(ProductVariant)
admin.site.register(ItemPricingDepartment)
admin.site.register(Warehouse)
admin.site.register(WarehouseLocation)
admin.site.register(ItemLot)
admin.site.register(ItemInventoryLot)
admin.site.register(StockMove)
admin.site.register(ReorderRule)
admin.site.register(StockAlert)
