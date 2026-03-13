from datetime import date

from django.core.management.base import BaseCommand
from django_tenants.utils import tenant_context

from apps.accounting.models import AccountingEntry
from apps.core_shared.models import GlobalAnnouncement
from apps.crm.models import Lead
from apps.customers.models import Company, CompanyType, Domain
from apps.manufacturing.models import WorkOrder


class Command(BaseCommand):
    help = "Create demo tenants and seed shared + tenant-specific sample data"

    def handle(self, *args, **options):
        self._seed_shared_data()
        tenants = self._ensure_tenants()
        self._seed_tenant_data(tenants)
        self.stdout.write(self.style.SUCCESS("Demo data seeded."))

    def _seed_shared_data(self) -> None:
        GlobalAnnouncement.objects.get_or_create(
            title="Platform Maintenance",
            defaults={
                "body": "Monthly maintenance runs every first Saturday.",
                "is_active": True,
            },
        )
        GlobalAnnouncement.objects.get_or_create(
            title="Security Reminder",
            defaults={
                "body": "All users should enable MFA by quarter end.",
                "is_active": True,
            },
        )

    def _ensure_tenants(self) -> list[Company]:
        tenants = []

        alpha, _ = Company.objects.get_or_create(
            schema_name="alpha",
            defaults={
                "name": "Alpha Services",
                "company_type": CompanyType.SERVICE,
            },
        )
        Domain.objects.get_or_create(domain="alpha.localhost", tenant=alpha, defaults={"is_primary": True})
        tenants.append(alpha)

        beta, _ = Company.objects.get_or_create(
            schema_name="beta",
            defaults={
                "name": "Beta Manufacturing",
                "company_type": CompanyType.MANUFACTURING,
            },
        )
        Domain.objects.get_or_create(domain="beta.localhost", tenant=beta, defaults={"is_primary": True})
        tenants.append(beta)

        gamma, _ = Company.objects.get_or_create(
            schema_name="gamma",
            defaults={
                "name": "Gamma Hybrid",
                "company_type": CompanyType.HYBRID,
            },
        )
        Domain.objects.get_or_create(domain="gamma.localhost", tenant=gamma, defaults={"is_primary": True})
        tenants.append(gamma)

        return tenants

    def _seed_tenant_data(self, tenants: list[Company]) -> None:
        for tenant in tenants:
            with tenant_context(tenant):
                AccountingEntry.objects.get_or_create(
                    description="Opening balance",
                    defaults={
                        "amount": "10000.00",
                        "currency": "USD",
                        "entry_date": date.today(),
                    },
                )

                if "crm" in tenant.enabled_modules:
                    Lead.objects.get_or_create(
                        name="Acme Corp",
                        defaults={"email": "ops@acme.example", "stage": "qualified"},
                    )

                if "manufacturing" in tenant.enabled_modules:
                    WorkOrder.objects.get_or_create(
                        title="WO-100 Demo Batch",
                        defaults={"status": "planned", "quantity": 120},
                    )
