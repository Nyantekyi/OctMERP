"""
apps/contact/models.py

Geographic data and contact information models.
Country/State/City are loaded from CSV via post_migrate signal.
Phone, Email, Website, Address are wrapped by Contact (GenericFK).
"""

import uuid
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.signals import post_migrate, post_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _
from djmoney.models.fields import MoneyField

from apps.common.models import TenantAwareModel, TimeStampedModel


# ─────────────────────────────────────────────────────────────────────────────
# Geography (public schema, TimeStampedModel)
# ─────────────────────────────────────────────────────────────────────────────

class Country(TimeStampedModel):
    name = models.CharField(max_length=100, unique=True)
    iso3 = models.CharField(max_length=3, blank=True)
    iso2 = models.CharField(max_length=2, blank=True)
    numeric_code = models.CharField(max_length=10, blank=True)
    phone_code = models.CharField(max_length=20, blank=True)
    currency = models.CharField(max_length=3, blank=True)
    currency_name = models.CharField(max_length=50, blank=True)
    lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    lon = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    class Meta:
        verbose_name = _("Country")
        verbose_name_plural = _("Countries")
        ordering = ["name"]

    def __str__(self):
        return self.name


class State(TimeStampedModel):
    country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name="states")
    name = models.CharField(max_length=100)
    state_code = models.CharField(max_length=10, blank=True)
    lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    lon = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    class Meta:
        verbose_name = _("State / Region")
        verbose_name_plural = _("States / Regions")
        unique_together = ("country", "name")

    def __str__(self):
        return f"{self.name}, {self.country}"


class City(TimeStampedModel):
    state = models.ForeignKey(State, on_delete=models.CASCADE, related_name="cities")
    name = models.CharField(max_length=100)
    lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    lon = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    class Meta:
        verbose_name = _("City")
        verbose_name_plural = _("Cities")
        ordering = ["name"]

    def __str__(self):
        return f"{self.name}, {self.state}"


# ─────────────────────────────────────────────────────────────────────────────
# Type lookup tables (tenant-scoped)
# ─────────────────────────────────────────────────────────────────────────────

class AddressType(TenantAwareModel):
    name = models.CharField(max_length=50, unique=True)  # Billing, Shipping, Office, Warehouse

    class Meta:
        verbose_name = _("Address Type")

    def __str__(self):
        return self.name


class PhoneType(TenantAwareModel):
    name = models.CharField(max_length=50, unique=True)  # Mobile, Work, Landline

    class Meta:
        verbose_name = _("Phone Type")

    def __str__(self):
        return self.name


class EmailType(TenantAwareModel):
    name = models.CharField(max_length=50, unique=True)  # Personal, Company

    class Meta:
        verbose_name = _("Email Type")

    def __str__(self):
        return self.name


class WebType(TenantAwareModel):
    name = models.CharField(max_length=50, unique=True)  # Website, Social Media, Blog

    class Meta:
        verbose_name = _("Web Type")

    def __str__(self):
        return self.name


# ─────────────────────────────────────────────────────────────────────────────
# Contact data models
# ─────────────────────────────────────────────────────────────────────────────

class Phone(TenantAwareModel):
    phonetype = models.ForeignKey(
        PhoneType, null=True, blank=True, on_delete=models.CASCADE, related_name="phones"
    )
    phone = models.CharField(_("Phone Number"), max_length=50)
    is_whatsapp = models.BooleanField(_("WhatsApp?"), default=False)

    class Meta:
        verbose_name = _("Phone")

    def __str__(self):
        return self.phone


class Address(TenantAwareModel):
    addresstype = models.ForeignKey(
        AddressType, null=True, blank=True, on_delete=models.CASCADE, related_name="addresses"
    )
    line = models.CharField(_("Street / Address Line"), max_length=200)
    city = models.ForeignKey(City, on_delete=models.CASCADE, related_name="addresses")
    postal_code = models.CharField(max_length=20, blank=True)
    landmark = models.CharField(max_length=200, blank=True)
    lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    lon = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    class Meta:
        verbose_name = _("Address")
        verbose_name_plural = _("Addresses")

    def __str__(self):
        return f"{self.line}, {self.city}"


class Email(TenantAwareModel):
    email = models.EmailField(_("Email Address"))
    email_type = models.ForeignKey(
        EmailType, null=True, blank=True, on_delete=models.CASCADE, related_name="emails"
    )

    class Meta:
        verbose_name = _("Email")

    def __str__(self):
        return self.email


class Website(TenantAwareModel):
    website = models.URLField(_("URL"))
    webtype = models.ForeignKey(
        WebType, null=True, blank=True, on_delete=models.CASCADE, related_name="websites"
    )

    class Meta:
        verbose_name = _("Website")

    def __str__(self):
        return self.website


# ─────────────────────────────────────────────────────────────────────────────
# Contact wrapper (Generic FK — links any Phone/Email/Website/Address)
# ─────────────────────────────────────────────────────────────────────────────

class Contact(TenantAwareModel):
    """
    Wraps any Phone / Email / Website / Address instance.
    Used as M2M on most party models (Company, Branch, Staff, Client, Vendor…).
    """
    ALLOWED_MODELS = ["Phone", "Address", "Website", "Email"]

    content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE, editable=False, related_name="contact_wrappers"
    )
    contact_id = models.UUIDField(editable=False)
    contactobject = GenericForeignKey("content_type", "contact_id")
    is_verified = models.BooleanField(_("Verified"), default=False)
    related_contacts = models.ManyToManyField("self", blank=True)

    class Meta:
        verbose_name = _("Contact")
        unique_together = ("content_type", "contact_id")

    def __str__(self):
        return f"Contact({self.content_type.model}: {self.contact_id})"

    def clean(self):
        if self.content_type and self.content_type.model not in [m.lower() for m in self.ALLOWED_MODELS]:
            raise ValidationError(
                f"Contact can only wrap: {', '.join(self.ALLOWED_MODELS)}"
            )


# ─────────────────────────────────────────────────────────────────────────────
# Auto-create Contact wrappers on Phone/Email/Website/Address save
# ─────────────────────────────────────────────────────────────────────────────

def _auto_wrap_contact(sender, instance, created, **kwargs):
    if created:
        ct = ContentType.objects.get_for_model(sender)
        Contact.objects.get_or_create(content_type=ct, contact_id=instance.id)


for _model in (Phone, Email, Website, Address):
    post_save.connect(_auto_wrap_contact, sender=_model)


# ─────────────────────────────────────────────────────────────────────────────
# Document management
# ─────────────────────────────────────────────────────────────────────────────

class DocumentType(TenantAwareModel):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name = _("Document Type")

    def __str__(self):
        return self.name


class Document(TenantAwareModel):
    document_type = models.ForeignKey(
        DocumentType, on_delete=models.CASCADE, null=True, related_name="documents"
    )
    document_url = models.CharField(_("File URL"), max_length=500)
    description = models.TextField(blank=True, null=True)
    custom_fields = models.JSONField(blank=True, null=True, default=dict)

    class Meta:
        verbose_name = _("Document")

    def __str__(self):
        return f"{self.document_type}: {self.document_url}"


# ─────────────────────────────────────────────────────────────────────────────
# Load geographic data from CSV on post_migrate
# ─────────────────────────────────────────────────────────────────────────────

@receiver(post_migrate)
def load_location_data(sender, **kwargs):
    """Load Country/State/City from CSV files if the tables are empty."""
    if sender.name != "apps.contact":
        return
    if Country.objects.exists():
        return
    import csv
    import os
    from django.conf import settings

    csv_dir = os.path.join(settings.BASE_DIR, "data", "geo")
    countries_csv = os.path.join(csv_dir, "countries.csv")
    if not os.path.exists(countries_csv):
        return

    with open(countries_csv, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        Country.objects.bulk_create(
            [
                Country(
                    name=row.get("name", ""),
                    iso3=row.get("iso3", ""),
                    iso2=row.get("iso2", ""),
                    numeric_code=row.get("numeric_code", ""),
                    phone_code=row.get("phone_code", ""),
                    currency=row.get("currency", ""),
                    currency_name=row.get("currency_name", ""),
                    lat=row.get("latitude") or None,
                    lon=row.get("longitude") or None,
                )
                for row in reader
            ],
            ignore_conflicts=True,
        )
