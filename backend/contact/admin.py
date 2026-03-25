from django.contrib import admin

from .models import (
    Address,
    AddressType,
    City,
    Contact,
    Country,
    Email,
    EmailType,
    Phone,
    PhoneType,
    State,
    Website,
    WebsiteType,
)


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ('name', 'iso2', 'iso3', 'currency')
    search_fields = ('name', 'iso2', 'iso3', 'currency', 'currency_name')


@admin.register(State)
class StateAdmin(admin.ModelAdmin):
    list_display = ('name', 'country', 'state_code')
    list_filter = ('country',)
    search_fields = ('name', 'state_code', 'country__name')


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ('name', 'state', 'country_name')
    list_filter = ('state__country', 'state')
    search_fields = ('name', 'state__name', 'state__country__name')

    @admin.display(ordering='state__country__name', description='Country')
    def country_name(self, obj):
        return obj.state.country.name


@admin.register(AddressType)
class AddressTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name',)


@admin.register(PhoneType)
class PhoneTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name',)


@admin.register(EmailType)
class EmailTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name',)


@admin.register(WebsiteType)
class WebsiteTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name',)


@admin.register(Phone)
class PhoneAdmin(admin.ModelAdmin):
    list_display = ('phone', 'phone_type', 'is_whatsapp', 'created_at')
    list_filter = ('phone_type', 'is_whatsapp')
    search_fields = ('phone',)


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ('line', 'city', 'address_type', 'created_at')
    list_filter = ('address_type', 'city__state__country')
    search_fields = ('line', 'line_2', 'postal_code', 'city__name')


@admin.register(Email)
class EmailAdmin(admin.ModelAdmin):
    list_display = ('email', 'email_type', 'created_at')
    list_filter = ('email_type',)
    search_fields = ('email',)


@admin.register(Website)
class WebsiteAdmin(admin.ModelAdmin):
    list_display = ('website', 'website_type', 'created_at')
    list_filter = ('website_type',)
    search_fields = ('website',)


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('content_type', 'contact_id', 'is_verified', 'is_primary', 'created_at')
    list_filter = ('content_type', 'is_verified', 'is_primary')
    search_fields = ('label',)
    filter_horizontal = ('related_contacts',)