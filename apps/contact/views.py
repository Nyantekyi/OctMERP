"""apps/contact/views.py"""

from rest_framework.permissions import AllowAny

from apps.common.api import build_model_viewset, build_readonly_model_viewset
from apps.common.permissions import IsTenantUser
from .models import Address, AddressType, City, Contact, Country, Document, DocumentType, Email, EmailType, Phone, PhoneType, State, WebType, Website
from .serializers import AddressSerializer, AddressTypeSerializer, CitySerializer, ContactSerializer, CountrySerializer, DocumentSerializer, DocumentTypeSerializer, EmailSerializer, EmailTypeSerializer, PhoneSerializer, PhoneTypeSerializer, StateSerializer, WebTypeSerializer, WebsiteSerializer


CountryViewSet = build_readonly_model_viewset(
    Country,
    CountrySerializer,
    permission_classes=[AllowAny],
    search_fields=["name", "iso2", "iso3"],
    ordering_fields=["name"],
    tenant_scoped=False,
)


StateViewSet = build_readonly_model_viewset(
    State,
    StateSerializer,
    permission_classes=[AllowAny],
    filterset_fields=["country"],
    search_fields=["name"],
    select_related_fields=["country"],
    tenant_scoped=False,
)


CityViewSet = build_readonly_model_viewset(
    City,
    CitySerializer,
    permission_classes=[AllowAny],
    filterset_fields=["state", "state__country"],
    search_fields=["name"],
    select_related_fields=["state", "state__country"],
    tenant_scoped=False,
)


AddressTypeViewSet = build_model_viewset(
    AddressType,
    AddressTypeSerializer,
    permission_classes=[IsTenantUser],
    search_fields=["name"],
)


PhoneTypeViewSet = build_model_viewset(PhoneType, PhoneTypeSerializer, permission_classes=[IsTenantUser])


EmailTypeViewSet = build_model_viewset(EmailType, EmailTypeSerializer, permission_classes=[IsTenantUser])


WebTypeViewSet = build_model_viewset(WebType, WebTypeSerializer, permission_classes=[IsTenantUser])


PhoneViewSet = build_model_viewset(
    Phone,
    PhoneSerializer,
    permission_classes=[IsTenantUser],
    filterset_fields=["phonetype", "is_whatsapp"],
    select_related_fields=["phonetype"],
)


AddressViewSet = build_model_viewset(
    Address,
    AddressSerializer,
    permission_classes=[IsTenantUser],
    filterset_fields=["addresstype", "city"],
    search_fields=["line", "city__name"],
    select_related_fields=["addresstype", "city"],
)


EmailViewSet = build_model_viewset(
    Email,
    EmailSerializer,
    permission_classes=[IsTenantUser],
    search_fields=["email"],
)


WebsiteViewSet = build_model_viewset(Website, WebsiteSerializer, permission_classes=[IsTenantUser])


ContactViewSet = build_model_viewset(
    Contact,
    ContactSerializer,
    permission_classes=[IsTenantUser],
    filterset_fields=["is_verified"],
)


DocumentTypeViewSet = build_model_viewset(
    DocumentType,
    DocumentTypeSerializer,
    permission_classes=[IsTenantUser],
    search_fields=["name"],
)


DocumentViewSet = build_model_viewset(
    Document,
    DocumentSerializer,
    permission_classes=[IsTenantUser],
    filterset_fields=["document_type"],
    select_related_fields=["document_type"],
)
