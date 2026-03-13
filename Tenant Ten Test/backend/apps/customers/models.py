from django.db import models
from django_tenants.models import DomainMixin, TenantMixin

COMMON_MODULES = ("accounting",)
SPECIALIZED_MODULES_BY_TYPE = {
    "service": ("crm",),
    "manufacturing": ("manufacturing",),
    "hybrid": ("crm", "manufacturing"),
}


class CompanyType(models.TextChoices):
    SERVICE = "service", "Service"
    MANUFACTURING = "manufacturing", "Manufacturing"
    HYBRID = "hybrid", "Hybrid"


class Company(TenantMixin):
    name = models.CharField(max_length=120)
    company_type = models.CharField(max_length=32, choices=CompanyType.choices, default=CompanyType.SERVICE)
    created_on = models.DateField(auto_now_add=True)
    paid_until = models.DateField(null=True, blank=True)
    on_trial = models.BooleanField(default=True)
    extra_modules = models.JSONField(default=list, blank=True)

    auto_create_schema = True

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return f"{self.name} ({self.schema_name})"

    @property
    def enabled_modules(self) -> list[str]:
        modules = set(COMMON_MODULES)
        modules.update(SPECIALIZED_MODULES_BY_TYPE.get(self.company_type, ()))
        modules.update(self.extra_modules or [])
        return sorted(modules)


class Domain(DomainMixin):
    pass
