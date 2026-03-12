"""
apps/contact/serializers.py
"""

from rest_framework import serializers
from .models import (
    Country, State, City,
    AddressType, PhoneType, EmailType, WebType,
    Phone, Address, Email, Website, Contact,
    DocumentType, Document,
)


class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = ["id", "name", "iso3", "iso2", "numeric_code", "phone_code", "currency", "currency_name", "lat", "lon"]


class StateSerializer(serializers.ModelSerializer):
    country_name = serializers.CharField(source="country.name", read_only=True)

    class Meta:
        model = State
        fields = ["id", "name", "state_code", "country", "country_name", "lat", "lon"]


class CitySerializer(serializers.ModelSerializer):
    state_name = serializers.CharField(source="state.name", read_only=True)
    country_name = serializers.CharField(source="state.country.name", read_only=True)

    class Meta:
        model = City
        fields = ["id", "name", "state", "state_name", "country_name", "lat", "lon"]


class AddressTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AddressType
        fields = ["id", "name", "is_active", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class PhoneTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PhoneType
        fields = ["id", "name", "is_active", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class EmailTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailType
        fields = ["id", "name", "is_active", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class WebTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = WebType
        fields = ["id", "name", "is_active", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class PhoneSerializer(serializers.ModelSerializer):
    phonetype_name = serializers.CharField(source="phonetype.name", read_only=True)

    class Meta:
        model = Phone
        fields = ["id", "phonetype", "phonetype_name", "phone", "is_whatsapp", "is_active", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class AddressSerializer(serializers.ModelSerializer):
    city_name = serializers.CharField(source="city.name", read_only=True)
    addresstype_name = serializers.CharField(source="addresstype.name", read_only=True)

    class Meta:
        model = Address
        fields = ["id", "addresstype", "addresstype_name", "line", "city", "city_name", "postal_code", "landmark", "lat", "lon", "is_active", "created_at", "updated_at"]
        read_only_fields = ["id", "city_name", "addresstype_name", "created_at", "updated_at"]


class EmailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Email
        fields = ["id", "email", "email_type", "is_active", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class WebsiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Website
        fields = ["id", "website", "webtype", "is_active", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = ["id", "content_type", "contact_id", "is_verified", "related_contacts", "is_active", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class DocumentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentType
        fields = ["id", "name", "is_active", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ["id", "document_type", "document_url", "description", "custom_fields", "is_active", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]
