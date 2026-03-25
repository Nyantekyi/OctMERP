from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, permissions, viewsets

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
from .serializers import (
    AddressSerializer,
    AddressTypeSerializer,
    CitySerializer,
    ContactSerializer,
    CountrySerializer,
    EmailSerializer,
    EmailTypeSerializer,
    PhoneSerializer,
    PhoneTypeSerializer,
    StateSerializer,
    WebsiteSerializer,
    WebsiteTypeSerializer,
)


class BaseContactViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]


class CountryViewSet(BaseContactViewSet):
    queryset = Country.objects.all()
    serializer_class = CountrySerializer
    search_fields = ['name', 'iso2', 'iso3', 'currency', 'currency_name']
    ordering_fields = ['name', 'created_at']


class StateViewSet(BaseContactViewSet):
    queryset = State.objects.select_related('country').all()
    serializer_class = StateSerializer
    filterset_fields = ['country']
    search_fields = ['name', 'state_code', 'country__name']
    ordering_fields = ['name', 'created_at']


class CityViewSet(BaseContactViewSet):
    queryset = City.objects.select_related('state', 'state__country').all()
    serializer_class = CitySerializer
    filterset_fields = ['state', 'state__country']
    search_fields = ['name', 'state__name', 'state__country__name']
    ordering_fields = ['name', 'created_at']


class AddressTypeViewSet(BaseContactViewSet):
    queryset = AddressType.objects.all()
    serializer_class = AddressTypeSerializer
    search_fields = ['name']
    ordering_fields = ['name', 'created_at']


class PhoneTypeViewSet(BaseContactViewSet):
    queryset = PhoneType.objects.all()
    serializer_class = PhoneTypeSerializer
    search_fields = ['name']
    ordering_fields = ['name', 'created_at']


class EmailTypeViewSet(BaseContactViewSet):
    queryset = EmailType.objects.all()
    serializer_class = EmailTypeSerializer
    search_fields = ['name']
    ordering_fields = ['name', 'created_at']


class WebsiteTypeViewSet(BaseContactViewSet):
    queryset = WebsiteType.objects.all()
    serializer_class = WebsiteTypeSerializer
    search_fields = ['name']
    ordering_fields = ['name', 'created_at']


class PhoneViewSet(BaseContactViewSet):
    queryset = Phone.objects.select_related('phone_type').all()
    serializer_class = PhoneSerializer
    filterset_fields = ['phone_type', 'is_whatsapp']
    search_fields = ['phone']
    ordering_fields = ['phone', 'created_at']


class AddressViewSet(BaseContactViewSet):
    queryset = Address.objects.select_related('address_type', 'city', 'city__state', 'city__state__country').all()
    serializer_class = AddressSerializer
    filterset_fields = ['address_type', 'city', 'city__state', 'city__state__country']
    search_fields = ['line', 'line_2', 'postal_code', 'city__name']
    ordering_fields = ['line', 'created_at']


class EmailViewSet(BaseContactViewSet):
    queryset = Email.objects.select_related('email_type').all()
    serializer_class = EmailSerializer
    filterset_fields = ['email_type']
    search_fields = ['email']
    ordering_fields = ['email', 'created_at']


class WebsiteViewSet(BaseContactViewSet):
    queryset = Website.objects.select_related('website_type').all()
    serializer_class = WebsiteSerializer
    filterset_fields = ['website_type']
    search_fields = ['website']
    ordering_fields = ['website', 'created_at']


class ContactViewSet(BaseContactViewSet):
    queryset = Contact.objects.select_related('content_type').prefetch_related('related_contacts').all()
    serializer_class = ContactSerializer
    filterset_fields = ['content_type', 'is_verified', 'is_primary']
    search_fields = ['label', 'content_type__model']
    ordering_fields = ['created_at', 'updated_at']