"""
apps/contact/views.py
"""

from rest_framework import viewsets
from rest_framework.permissions import AllowAny

from apps.common.permissions import IsTenantUser
from .models import Country, State, City, AddressType, PhoneType, EmailType, WebType, Phone, Address, Email, Website, Contact, DocumentType, Document
from .serializers import CountrySerializer, StateSerializer, CitySerializer, AddressTypeSerializer, PhoneTypeSerializer, EmailTypeSerializer, WebTypeSerializer, PhoneSerializer, AddressSerializer, EmailSerializer, WebsiteSerializer, ContactSerializer, DocumentTypeSerializer, DocumentSerializer


class CountryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Country.objects.all()
    serializer_class = CountrySerializer
    permission_classes = [AllowAny]
    search_fields = ["name", "iso2", "iso3"]
    ordering_fields = ["name"]


class StateViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = State.objects.select_related("country")
    serializer_class = StateSerializer
    permission_classes = [AllowAny]
    filterset_fields = ["country"]
    search_fields = ["name"]


class CityViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = City.objects.select_related("state__country")
    serializer_class = CitySerializer
    permission_classes = [AllowAny]
    filterset_fields = ["state", "state__country"]
    search_fields = ["name"]


class AddressTypeViewSet(viewsets.ModelViewSet):
    queryset = AddressType.objects.all()
    serializer_class = AddressTypeSerializer
    permission_classes = [IsTenantUser]
    search_fields = ["name"]


class PhoneTypeViewSet(viewsets.ModelViewSet):
    queryset = PhoneType.objects.all()
    serializer_class = PhoneTypeSerializer
    permission_classes = [IsTenantUser]


class EmailTypeViewSet(viewsets.ModelViewSet):
    queryset = EmailType.objects.all()
    serializer_class = EmailTypeSerializer
    permission_classes = [IsTenantUser]


class WebTypeViewSet(viewsets.ModelViewSet):
    queryset = WebType.objects.all()
    serializer_class = WebTypeSerializer
    permission_classes = [IsTenantUser]


class PhoneViewSet(viewsets.ModelViewSet):
    queryset = Phone.objects.select_related("phonetype")
    serializer_class = PhoneSerializer
    permission_classes = [IsTenantUser]
    filterset_fields = ["phonetype", "is_whatsapp"]


class AddressViewSet(viewsets.ModelViewSet):
    queryset = Address.objects.select_related("addresstype", "city")
    serializer_class = AddressSerializer
    permission_classes = [IsTenantUser]
    filterset_fields = ["addresstype", "city"]
    search_fields = ["line", "city__name"]


class EmailViewSet(viewsets.ModelViewSet):
    queryset = Email.objects.all()
    serializer_class = EmailSerializer
    permission_classes = [IsTenantUser]
    search_fields = ["email"]


class WebsiteViewSet(viewsets.ModelViewSet):
    queryset = Website.objects.all()
    serializer_class = WebsiteSerializer
    permission_classes = [IsTenantUser]


class ContactViewSet(viewsets.ModelViewSet):
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer
    permission_classes = [IsTenantUser]
    filterset_fields = ["is_verified"]


class DocumentTypeViewSet(viewsets.ModelViewSet):
    queryset = DocumentType.objects.all()
    serializer_class = DocumentTypeSerializer
    permission_classes = [IsTenantUser]
    search_fields = ["name"]


class DocumentViewSet(viewsets.ModelViewSet):
    queryset = Document.objects.select_related("document_type")
    serializer_class = DocumentSerializer
    permission_classes = [IsTenantUser]
    filterset_fields = ["document_type"]
