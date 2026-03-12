from apps.common.api import build_model_viewset
from apps.contact.api.serializers import AddressSerializer, AddressTypeSerializer, CitySerializer, ContactSerializer, CountrySerializer, DocumentSerializer, DocumentTypeSerializer, EmailSerializer, EmailTypeSerializer, PhoneSerializer, PhoneTypeSerializer, StateSerializer, WebsiteSerializer, WebTypeSerializer
from apps.contact.models import Address, AddressType, City, Contact, Country, Document, DocumentType, Email, EmailType, Phone, PhoneType, State, Website, webType

CountryViewSet = build_model_viewset(Country, CountrySerializer, search_fields=("name", "iso2", "iso3"), ordering_fields=("name",))
StateViewSet = build_model_viewset(State, StateSerializer, search_fields=("name",), filterset_fields=("country",))
CityViewSet = build_model_viewset(City, CitySerializer, search_fields=("name",), filterset_fields=("state",))
AddressTypeViewSet = build_model_viewset(AddressType, AddressTypeSerializer, search_fields=("name",))
PhoneTypeViewSet = build_model_viewset(PhoneType, PhoneTypeSerializer, search_fields=("name",))
EmailTypeViewSet = build_model_viewset(EmailType, EmailTypeSerializer, search_fields=("name",))
WebTypeViewSet = build_model_viewset(webType, WebTypeSerializer, search_fields=("name",))
PhoneViewSet = build_model_viewset(Phone, PhoneSerializer, search_fields=("phone",), filterset_fields=("phonetype", "is_whatsapp"))
AddressViewSet = build_model_viewset(Address, AddressSerializer, search_fields=("line", "postal_code", "landmark"), filterset_fields=("addresstype", "city"))
EmailViewSet = build_model_viewset(Email, EmailSerializer, search_fields=("email",), filterset_fields=("emailType",))
WebsiteViewSet = build_model_viewset(Website, WebsiteSerializer, search_fields=("website",), filterset_fields=("webtype",))
ContactViewSet = build_model_viewset(Contact, ContactSerializer, filterset_fields=("content_type",))
DocumentTypeViewSet = build_model_viewset(DocumentType, DocumentTypeSerializer, search_fields=("name",))
DocumentViewSet = build_model_viewset(Document, DocumentSerializer, search_fields=("document_url",), filterset_fields=("document_type",))
