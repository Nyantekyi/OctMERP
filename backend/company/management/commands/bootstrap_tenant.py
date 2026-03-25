import os

from django.core.management.base import BaseCommand

from company.models import BusinessType, Company, Domain, PaymentClass


class Command(BaseCommand):
    help = 'Create or update the default tenant and its domains from environment variables.'

    def add_arguments(self, parser):
        parser.add_argument('--name', default=os.getenv('DEFAULT_TENANT_NAME', 'ERP Public'))
        parser.add_argument('--schema-name', default=os.getenv('DEFAULT_TENANT_SCHEMA', 'public'))
        parser.add_argument('--domains', default=os.getenv('DEFAULT_TENANT_DOMAINS', 'localhost,127.0.0.1'))
        parser.add_argument('--trade-country', default=os.getenv('DEFAULT_TENANT_TRADE_COUNTRY', 'GH'))

    def handle(self, *args, **options):
        name = options['name']
        schema_name = options['schema_name']
        domains = [item.strip() for item in options['domains'].split(',') if item.strip()]
        trade_country = options['trade_country']

        payment_class, _ = PaymentClass.objects.get_or_create(
            name='Standard',
            defaults={'description': 'Default payment class for bootstrapped tenants.'},
        )
        business_type, _ = BusinessType.objects.get_or_create(
            name='General',
            defaults={'description': 'Default business type for bootstrapped tenants.'},
        )

        company_defaults = {
            'name': name,
            'trade_name': name,
            'trade_country': trade_country,
            'payment_class': payment_class,
            'business_type': business_type,
        }

        company, created = Company.objects.get_or_create(schema_name=schema_name, defaults=company_defaults)

        if not created:
            updated = False
            for field, value in company_defaults.items():
                if getattr(company, field) != value:
                    setattr(company, field, value)
                    updated = True
            if updated:
                company.save()

        primary_domain = domains[0] if domains else None
        for domain_name in domains:
            domain, _ = Domain.objects.get_or_create(
                domain=domain_name,
                defaults={
                    'tenant': company,
                    'is_primary': domain_name == primary_domain,
                },
            )
            changed = False
            if domain.tenant_id != company.id:
                domain.tenant = company
                changed = True
            if domain.is_primary != (domain_name == primary_domain):
                domain.is_primary = domain_name == primary_domain
                changed = True
            if changed:
                domain.save()

        self.stdout.write(
            self.style.SUCCESS(
                f"Tenant '{company.name}' is ready on schema '{company.schema_name}' for domains: {', '.join(domains)}"
            )
        )