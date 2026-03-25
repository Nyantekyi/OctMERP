from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from rest_framework.test import APITestCase

from .models import Address, AddressType, City, Contact, Country, Email, Phone, PhoneType, State, Website


class ContactModelTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.country = Country.objects.create(name='Ghana', iso2='GH', iso3='GHA', numeric_code='288')
        cls.state = State.objects.create(country=cls.country, name='Greater Accra', state_code='GA')
        cls.city = City.objects.create(state=cls.state, name='Accra')
        cls.phone_type, _ = PhoneType.objects.get_or_create(name='Mobile')
        cls.address_type, _ = AddressType.objects.get_or_create(name='Office')

    def test_phone_creates_contact_record(self):
        phone = Phone.objects.create(phone_type=self.phone_type, phone='+233555000111')
        contact = Contact.objects.get(contact_id=phone.id)
        self.assertEqual(contact.content_type, ContentType.objects.get_for_model(Phone))

    def test_contact_rejects_invalid_content_type(self):
        address = Address.objects.create(address_type=self.address_type, line='1 Main Street', city=self.city)
        contact = Contact(
            content_type=ContentType.objects.get_for_model(Country),
            contact_id=address.id,
        )
        with self.assertRaises(ValidationError):
            contact.full_clean()

    def test_address_string_representation(self):
        address = Address.objects.create(address_type=self.address_type, line='1 Main Street', city=self.city)
        self.assertIn('Accra', str(address))