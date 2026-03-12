from django.contrib import admin

from apps.sales.models import (
    Delivery,
    PriceList,
    Quotation,
    QuotationLine,
    SalesOrder,
    SalesOrderLine,
    SalesReturn,
    Tender_Repository,
)


@admin.register(SalesOrder)
class SalesOrderAdmin(admin.ModelAdmin):
    list_display = ("order_number", "company", "client", "status", "total")
    list_filter = ("company", "status", "is_active")
    search_fields = ("order_number",)


@admin.register(Quotation)
class QuotationAdmin(admin.ModelAdmin):
    list_display = ("quote_number", "company", "client", "status", "total")
    list_filter = ("company", "status", "is_active")
    search_fields = ("quote_number",)


admin.site.register(PriceList)
admin.site.register(Tender_Repository)
admin.site.register(QuotationLine)
admin.site.register(SalesOrderLine)
admin.site.register(Delivery)
admin.site.register(SalesReturn)
