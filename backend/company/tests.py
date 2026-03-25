from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.management import call_command
from rest_framework.test import APITestCase

from company.models import Company, PaymentClass


class CompanyModelTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.payment_class = PaymentClass.objects.create(name='Retail')

    def test_company_generates_schema_name(self):
        company = Company.objects.create(name='Acme Holdings', payment_class=self.payment_class)
        self.assertEqual(company.schema_name, 'acme_holdings')

    def test_company_default_currency_is_immutable(self):
        company = Company.objects.create(name='Immutable Currency Co', payment_class=self.payment_class)
        company.default_currency = 'USD'
        with self.assertRaises(ValidationError):
            company.full_clean()


class CompanyApiAndAuthTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('bootstrap_tenant', name='ERP Test', schema_name='public', domains='localhost,127.0.0.1')
        cls.user = get_user_model().objects.create_user(username='tester', password='secret123')

    def setUp(self):
        self.client.defaults['HTTP_HOST'] = 'localhost'

    def test_login_returns_knox_token(self):
        response = self.client.post(
            '/api/auth/login/',
            {'username': 'tester', 'password': 'secret123'},
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('token', response.data)
        self.assertEqual(response.data['user']['username'], 'tester')

    def test_companies_endpoint_requires_auth_and_returns_bootstrap_tenant(self):
        login_response = self.client.post(
            '/api/auth/login/',
            {'username': 'tester', 'password': 'secret123'},
            format='json',
        )
        token = login_response.data['token']
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}', HTTP_HOST='localhost')
        response = self.client.get('/api/company/companies/')
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(response.data), 1)