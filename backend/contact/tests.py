import tempfile
from pathlib import Path

from django.core.management import call_command
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.test import TestCase
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


class LoadLocationDataCommandTests(TestCase):
    def test_command_imports_location_data_idempotently(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            data_dir = Path(temp_dir)
            (data_dir / 'countries.csv').write_text(
                '\n'.join(
                    [
                        'id,name,iso3,iso2,numeric_code,phone_code,capital,currency,currency_name,currency_symbol,tld,native,region,region_id,subregion,subregion_id,nationality,timezones,latitude,longitude,emoji,emojiU',
                        '1,Ghana,GHA,GH,288,233,Accra,GHS,Ghanaian cedi,Cedi,.gh,Ghana,Africa,1,Western Africa,3,Ghanaian,[],7.94652700,-1.02319400,,',
                        '2,Togo,TGO,TG,768,228,Lome,XOF,CFA Franc,CFA,.tg,Togo,Africa,1,Western Africa,3,Togolese,[],8.61954300,0.82478200,,',
                    ]
                ),
                encoding='utf-8',
            )
            (data_dir / 'states.csv').write_text(
                '\n'.join(
                    [
                        'id,name,country_id,country_code,country_name,state_code,type,latitude,longitude',
                        '10,Greater Accra,1,GH,Ghana,GA,,5.81428360,-0.07467670',
                        '20,Maritime,2,TG,Togo,M,,6.49135000,1.28910360',
                    ]
                ),
                encoding='utf-8',
            )
            (data_dir / 'cities.csv').write_text(
                '\n'.join(
                    [
                        'id,name,state_id,state_code,state_name,country_id,country_code,country_name,latitude,longitude,wikiDataId',
                        '100,Accra,10,GA,Greater Accra,1,GH,Ghana,5.55602000,-0.19690000,Q3761',
                        '200,Lome,20,M,Maritime,2,TG,Togo,6.13748000,1.21227000,Q3792',
                    ]
                ),
                encoding='utf-8',
            )

            call_command('load_location_data', data_dir=str(data_dir), country_code=['GH'])
            call_command('load_location_data', data_dir=str(data_dir), country_code=['GH'])

        self.assertEqual(Country.objects.count(), 1)
        self.assertEqual(State.objects.count(), 1)
        self.assertEqual(City.objects.count(), 1)
        self.assertEqual(Country.objects.get(iso2='GH').currency, 'GHS')

    def test_command_prunes_non_selected_countries(self):
        ghana = Country.objects.create(name='Ghana', iso2='GH', iso3='GHA', numeric_code='288')
        togo = Country.objects.create(name='Togo', iso2='TG', iso3='TGO', numeric_code='768')
        gh_state = State.objects.create(country=ghana, name='Greater Accra', state_code='GA')
        tg_state = State.objects.create(country=togo, name='Maritime', state_code='M')
        City.objects.create(state=gh_state, name='Accra')
        City.objects.create(state=tg_state, name='Lome')

        with tempfile.TemporaryDirectory() as temp_dir:
            data_dir = Path(temp_dir)
            (data_dir / 'countries.csv').write_text(
                '\n'.join(
                    [
                        'id,name,iso3,iso2,numeric_code,phone_code,capital,currency,currency_name,currency_symbol,tld,native,region,region_id,subregion,subregion_id,nationality,timezones,latitude,longitude,emoji,emojiU',
                        '1,Ghana,GHA,GH,288,233,Accra,GHS,Ghanaian cedi,Cedi,.gh,Ghana,Africa,1,Western Africa,3,Ghanaian,[],7.94652700,-1.02319400,,',
                    ]
                ),
                encoding='utf-8',
            )
            (data_dir / 'states.csv').write_text(
                '\n'.join(
                    [
                        'id,name,country_id,country_code,country_name,state_code,type,latitude,longitude',
                        '10,Greater Accra,1,GH,Ghana,GA,,5.81428360,-0.07467670',
                    ]
                ),
                encoding='utf-8',
            )
            (data_dir / 'cities.csv').write_text(
                '\n'.join(
                    [
                        'id,name,state_id,state_code,state_name,country_id,country_code,country_name,latitude,longitude,wikiDataId',
                        '100,Accra,10,GA,Greater Accra,1,GH,Ghana,5.55602000,-0.19690000,Q3761',
                    ]
                ),
                encoding='utf-8',
            )

            call_command('load_location_data', data_dir=str(data_dir), country_code=['GH'], prune=True)

        self.assertTrue(Country.objects.filter(iso2='GH').exists())
        self.assertFalse(Country.objects.filter(iso2='TG').exists())
        self.assertEqual(State.objects.count(), 1)
        self.assertEqual(City.objects.count(), 1)