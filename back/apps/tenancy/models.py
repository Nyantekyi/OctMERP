from django.conf import settings
from django.db import models

from apps.common.models import activearchlockedMixin, createdtimestamp_uid

if getattr(settings, "USE_DJANGO_TENANTS", False):
    from django_tenants.models import DomainMixin, TenantMixin

    _TenantBase = (createdtimestamp_uid, activearchlockedMixin, TenantMixin)
    _DomainBase = (createdtimestamp_uid, activearchlockedMixin, DomainMixin)
else:
    _TenantBase = (createdtimestamp_uid, activearchlockedMixin)
    _DomainBase = (createdtimestamp_uid, activearchlockedMixin)


class Tenant(*_TenantBase):
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    schema_name = models.SlugField(blank=True, default="public")
    paid_until = models.DateField(null=True, blank=True)
    on_trial = models.BooleanField(default=True)

    if getattr(settings, "USE_DJANGO_TENANTS", False):
        auto_create_schema = True

    def __str__(self):
        return self.name


class TenantDomain(*_DomainBase):
    if not getattr(settings, "USE_DJANGO_TENANTS", False):
        tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="domains")
        domain = models.CharField(max_length=255, unique=True)
        is_primary = models.BooleanField(default=False)

    def __str__(self):
        return getattr(self, "domain", str(self.pk))
