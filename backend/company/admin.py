from django.contrib import admin

from .models import (
    BusinessType,
    Company,
    Domain,
    Industry,
    PaymentClass,
)


@admin.register(Industry)
class IndustryAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name',)


@admin.register(PaymentClass)
class PaymentClassAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name',)


@admin.register(BusinessType)
class BusinessTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name',)


class DomainInline(admin.TabularInline):
    model = Domain
    extra = 0


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'schema_name', 'default_currency', 'is_active', 'created_at')
    list_filter = ('is_active', 'default_currency', 'trade_country')
    search_fields = ('name', 'trade_name', 'schema_name', 'slug')
    inlines = [DomainInline]
    filter_horizontal = ('contacts',)
