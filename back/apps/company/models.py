from django.conf import settings
from django.db import models

from apps.common.models import activearchlockedMixin, createdtimestamp_uid

if getattr(settings, "USE_DJANGO_TENANTS", False):
    from django_tenants.models import DomainMixin, TenantMixin
    _CompanyBase = (createdtimestamp_uid, activearchlockedMixin, TenantMixin)
    _DomainBase = (createdtimestamp_uid, activearchlockedMixin, DomainMixin)
else:
    _CompanyBase = (createdtimestamp_uid, activearchlockedMixin)
    _DomainBase = (createdtimestamp_uid, activearchlockedMixin)


class Industry(createdtimestamp_uid, activearchlockedMixin):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    additional_info = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return self.name


class PaymentClass(createdtimestamp_uid, activearchlockedMixin):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class BusinessType(createdtimestamp_uid, activearchlockedMixin):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class Company(*_CompanyBase):
    auto_create_schema = True  # used by django-tenants when enabled

    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    schema_name = models.SlugField(blank=True)
    industry = models.ForeignKey(Industry, null=True, blank=True, on_delete=models.SET_NULL, related_name="companies")
    payment = models.ForeignKey(PaymentClass, null=True, blank=True, on_delete=models.SET_NULL, related_name="companies")
    business_type = models.ForeignKey(BusinessType, null=True, blank=True, on_delete=models.SET_NULL, related_name="companies")
    default_currency = models.CharField(max_length=3, default="GHS")
    tradecountry = models.ForeignKey("contact.Country", null=True, blank=True, on_delete=models.SET_NULL, related_name="companies")
    contact = models.ManyToManyField("contact.Contact", blank=True, related_name="companies")

    def save(self, *args, **kwargs):
        if not self.schema_name:
            self.schema_name = self.slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Domain(*_DomainBase):
    # When USE_DJANGO_TENANTS=True, FK and domain fields come from DomainMixin.
    # When False, define them explicitly.
    if not getattr(settings, "USE_DJANGO_TENANTS", False):
        company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="domains")
        domain = models.CharField(max_length=255, unique=True)
        is_primary = models.BooleanField(default=False)

    def __str__(self):
        return self.domain
