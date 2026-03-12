from django.db import models

from apps.common.models import activearchlockedMixin, createdtimestamp_uid


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


class Company(createdtimestamp_uid, activearchlockedMixin):
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


class Domain(createdtimestamp_uid, activearchlockedMixin):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="domains")
    domain = models.CharField(max_length=255, unique=True)
    is_primary = models.BooleanField(default=False)

    def __str__(self):
        return self.domain
