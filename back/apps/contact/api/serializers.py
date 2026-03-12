from apps.common.api import build_model_serializer
from apps.contact.models import Address, AddressType, City, Contact, Country, Document, DocumentType, Email, EmailType, Phone, PhoneType, State, Website, webType

CountrySerializer = build_model_serializer(Country)
StateSerializer = build_model_serializer(State)
CitySerializer = build_model_serializer(City)
AddressTypeSerializer = build_model_serializer(AddressType)
PhoneTypeSerializer = build_model_serializer(PhoneType)
EmailTypeSerializer = build_model_serializer(EmailType)
WebTypeSerializer = build_model_serializer(webType)
PhoneSerializer = build_model_serializer(Phone)
AddressSerializer = build_model_serializer(Address)
EmailSerializer = build_model_serializer(Email)
WebsiteSerializer = build_model_serializer(Website)
ContactSerializer = build_model_serializer(Contact)
DocumentTypeSerializer = build_model_serializer(DocumentType)
DocumentSerializer = build_model_serializer(Document)
