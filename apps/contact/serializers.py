"""apps/contact/serializers.py"""

from apps.common.api import build_model_serializer

from .models import (
    Address,
    AddressType,
    City,
    Contact,
    Country,
    Document,
    DocumentType,
    Email,
    EmailType,
    Phone,
    PhoneType,
    State,
    WebType,
    Website,
)


def _state_to_representation(serializer, instance, representation):
    representation["country_name"] = getattr(getattr(instance, "country", None), "name", None)
    return representation


def _city_to_representation(serializer, instance, representation):
    state = getattr(instance, "state", None)
    representation["state_name"] = getattr(state, "name", None)
    representation["country_name"] = getattr(getattr(state, "country", None), "name", None)
    return representation


def _phone_to_representation(serializer, instance, representation):
    representation["phonetype_name"] = getattr(getattr(instance, "phonetype", None), "name", None)
    return representation


def _address_to_representation(serializer, instance, representation):
    representation["city_name"] = getattr(getattr(instance, "city", None), "name", None)
    representation["addresstype_name"] = getattr(getattr(instance, "addresstype", None), "name", None)
    return representation


CountrySerializer = build_model_serializer(
    Country,
    fields=["id", "name", "iso3", "iso2", "numeric_code", "phone_code", "currency", "currency_name", "lat", "lon"],
    read_only_fields=("id",),
)
StateSerializer = build_model_serializer(
    State,
    fields=["id", "name", "state_code", "country", "country_name", "lat", "lon"],
    read_only_fields=("id",),
    to_representation_handler=_state_to_representation,
)
CitySerializer = build_model_serializer(
    City,
    fields=["id", "name", "state", "state_name", "country_name", "lat", "lon"],
    read_only_fields=("id",),
    to_representation_handler=_city_to_representation,
)
AddressTypeSerializer = build_model_serializer(
    AddressType,
    fields=["id", "name", "is_active", "created_at", "updated_at"],
)
PhoneTypeSerializer = build_model_serializer(
    PhoneType,
    fields=["id", "name", "is_active", "created_at", "updated_at"],
)
EmailTypeSerializer = build_model_serializer(
    EmailType,
    fields=["id", "name", "is_active", "created_at", "updated_at"],
)
WebTypeSerializer = build_model_serializer(
    WebType,
    fields=["id", "name", "is_active", "created_at", "updated_at"],
)
PhoneSerializer = build_model_serializer(
    Phone,
    fields=["id", "phonetype", "phonetype_name", "phone", "is_whatsapp", "is_active", "created_at", "updated_at"],
    to_representation_handler=_phone_to_representation,
)
AddressSerializer = build_model_serializer(
    Address,
    fields=["id", "addresstype", "addresstype_name", "line", "city", "city_name", "postal_code", "landmark", "lat", "lon", "is_active", "created_at", "updated_at"],
    read_only_fields=("city_name", "addresstype_name"),
    to_representation_handler=_address_to_representation,
)
EmailSerializer = build_model_serializer(
    Email,
    fields=["id", "email", "email_type", "is_active", "created_at", "updated_at"],
)
WebsiteSerializer = build_model_serializer(
    Website,
    fields=["id", "website", "webtype", "is_active", "created_at", "updated_at"],
)
ContactSerializer = build_model_serializer(
    Contact,
    fields=["id", "content_type", "contact_id", "is_verified", "related_contacts", "is_active", "created_at", "updated_at"],
)
DocumentTypeSerializer = build_model_serializer(
    DocumentType,
    fields=["id", "name", "is_active", "created_at", "updated_at"],
)
DocumentSerializer = build_model_serializer(
    Document,
    fields=["id", "document_type", "document_url", "description", "custom_fields", "is_active", "created_at", "updated_at"],
)
