"""
apps/company/models.py

Public-schema models for multi-tenancy.
Company extends TenantMixin — lives in the PostgreSQL public schema.
"""

import uuid
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _
from django_tenants.models import TenantMixin, DomainMixin
from djmoney.models.fields import CurrencyField


class Industry(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    additional_info = models.JSONField(blank=True, null=True, default=dict)

    class Meta:
        verbose_name = _("Industry")
        verbose_name_plural = _("Industries")

    def __str__(self):
        return self.name


class BusinessType(models.Model):
    """
    Pharmacy, Clinic, Hospital, Retail, Wholesale, Manufacturing, etc.
    """
    name = models.CharField(max_length=50, unique=True)

    class Meta:
        verbose_name = _("Business Type")

    def __str__(self):
        return self.name


class PaymentClass(models.Model):
    """Controls payment method availability per company subscription tier."""
    name = models.CharField(max_length=50, unique=True)

    class Meta:
        verbose_name = _("Payment Class")

    def __str__(self):
        return self.name


class Company(TenantMixin):
    """
    One Company = one PostgreSQL schema = one tenant.
    schema_name is set from slug on save.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(_("Company Name"), max_length=200)
    slug = models.SlugField(_("Slug"), unique=True, help_text=_("Used as PostgreSQL schema name"))
    logo = models.CharField(max_length=200, blank=True, null=True)
    industry = models.ForeignKey(
        Industry, on_delete=models.SET_NULL, null=True, blank=True, related_name="companies"
    )
    business_type = models.ForeignKey(
        BusinessType, on_delete=models.SET_NULL, null=True, blank=True, related_name="companies"
    )
    payment = models.ForeignKey(
        PaymentClass, on_delete=models.PROTECT, null=True, blank=True, related_name="companies"
    )
    default_currency = CurrencyField(default="GHS")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # django-tenants required field
    auto_create_schema = True

    class Meta:
        verbose_name = _("Company")
        verbose_name_plural = _("Companies")

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.schema_name:
            self.schema_name = self.slug
        super().save(*args, **kwargs)


class Domain(DomainMixin):
    """Maps a subdomain or custom domain to a Company tenant."""

    class Meta:
        verbose_name = _("Domain")

    def __str__(self):
        return self.domain
