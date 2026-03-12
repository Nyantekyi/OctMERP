"""
apps/party/models.py

User management and profile models.

Hierarchy:
    CustomUser (AbstractBaseUser + PermissionsMixin)
      ├── StaffProfile   (branches M2M, is_manager)
      ├── ClientProfile  (department FK → apps.department)
      └── SupplierProfile(department FK → apps.department)

Geographic / org data lives in separate apps:
    Country / State / City          → apps.contact
    Company / Domain (TenantMixin)  → apps.company
    Department / Branch / Room      → apps.department
"""

import uuid
from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.common.models import TenantAwareModel, TimeStampedModel


# ─────────────────────────────────────────────────────────────────────────────
# Lookup tables
# ─────────────────────────────────────────────────────────────────────────────

class Occupation(TimeStampedModel):
    """Job title / occupation drawn from ISCO-08 standard."""
    name = models.CharField(_("Occupation Title"), max_length=255, unique=True)
    definition = models.TextField(blank=True, null=True)
    task = models.TextField(_("Tasks Include"), blank=True, null=True)
    isco_code = models.CharField(_("ISCO Code"), max_length=20, blank=True, null=True)

    class Meta:
        verbose_name = _("Occupation")
        verbose_name_plural = _("Occupations")
        ordering = ["name"]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("occupation_detail", kwargs={"pk": self.pk})


# ─────────────────────────────────────────────────────────────────────────────
# Custom User
# ─────────────────────────────────────────────────────────────────────────────

class UserType(models.TextChoices):
    """Canonical user types used throughout the ERP."""
    STAFF    = "staff",    _("Staff")
    CLIENT   = "client",   _("Client")
    SUPPLIER = "supplier", _("Supplier")
    AGENT    = "agent",    _("AI Agent")


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_("Email address is required."))
        email = self.normalize_email(email)
        extra_fields.setdefault("is_active", True)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("user_type", "staff")
        if not extra_fields.get("is_staff"):
            raise ValueError(_("Superuser must have is_staff=True."))
        if not extra_fields.get("is_superuser"):
            raise ValueError(_("Superuser must have is_superuser=True."))
        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(_("Email Address"), unique=True)
    first_name = models.CharField(_("First Name"), max_length=150)
    last_name = models.CharField(_("Last Name"), max_length=150)
    user_type = models.CharField(
        _("User Type"), max_length=20, choices=UserType.choices, default=UserType.STAFF
    )
    avatar = models.CharField(_("Avatar URL / Path"), max_length=500, blank=True, null=True)
    phone = models.CharField(_("Phone"), max_length=30, blank=True, null=True)

    is_staff = models.BooleanField(
        _("Admin Access"),
        default=False,
        help_text=_("Designates whether the user can log into the Django admin site."),
    )
    is_active = models.BooleanField(_("Active"), default=True)
    date_joined = models.DateTimeField(_("Date Joined"), default=timezone.now)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    objects = CustomUserManager()

    class Meta:
        verbose_name = _("User")
        verbose_name_plural = _("Users")
        ordering = ["email"]

    def __str__(self):
        return self.get_full_name() or self.email

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def get_short_name(self):
        return self.first_name

    def get_absolute_url(self):
        return reverse("user_detail", kwargs={"pk": self.pk})



# ─────────────────────────────────────────────────────────────────────────────
# User Profiles
# ─────────────────────────────────────────────────────────────────────────────

class StaffProfile(TenantAwareModel):
    """Extended profile for staff users. Created automatically via post_save."""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="staff_profile"
    )
    is_manager = models.BooleanField(_("Is Manager?"), default=False)
    branches = models.ManyToManyField(
        "department.Branch", verbose_name=_("Assigned Branches"), blank=True
    )
    department = models.ForeignKey(
        "department.Department", verbose_name=_("Primary Department"), on_delete=models.SET_NULL,
        null=True, blank=True, related_name="staff_members"
    )
    occupation = models.ForeignKey(
        Occupation, verbose_name=_("Occupation"), on_delete=models.SET_NULL, null=True, blank=True
    )
    # Accounting link — set via post_save in accounting app
    staff_account = models.ForeignKey(
        "accounting.Account",
        verbose_name=_("Payroll Account"),
        on_delete=models.SET_NULL,
        null=True, blank=True,
        editable=False,
        related_name="staff_payroll_accounts",
    )
    credit_sale_account = models.ForeignKey(
        "accounting.Account",
        verbose_name=_("AR Account"),
        on_delete=models.SET_NULL,
        null=True, blank=True,
        editable=False,
        related_name="staff_ar_accounts",
    )
    employee_id = models.CharField(_("Employee ID"), max_length=50, blank=True, null=True, unique=True)
    date_of_birth = models.DateField(_("Date of Birth"), blank=True, null=True)
    hire_date = models.DateField(_("Hire Date"), blank=True, null=True)
    national_id = models.CharField(_("National ID"), max_length=50, blank=True, null=True)
    emergency_contact_name = models.CharField(_("Emergency Contact Name"), max_length=150, blank=True, null=True)
    emergency_contact_phone = models.CharField(_("Emergency Contact Phone"), max_length=30, blank=True, null=True)

    class Meta:
        verbose_name = _("Staff Profile")
        verbose_name_plural = _("Staff Profiles")
        ordering = ["user__last_name", "user__first_name"]

    def __str__(self):
        return self.user.get_full_name()

    def get_absolute_url(self):
        return reverse("staff_profile_detail", kwargs={"pk": self.pk})


class ClientProfile(TenantAwareModel):
    """Extended profile for client (customer) users."""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="client_profile"
    )
    department = models.ForeignKey(
        "department.Department", verbose_name=_("Assigned Department"),
        on_delete=models.SET_NULL, null=True, blank=True, related_name="clients"
    )
    payment_class = models.ForeignKey(
        "company.PaymentClass", verbose_name=_("Payment Class"), on_delete=models.PROTECT, null=True, blank=True
    )
    client_account = models.ForeignKey(
        "accounting.Account",
        verbose_name=_("Accounts Receivable Account"),
        on_delete=models.SET_NULL,
        null=True, blank=True,
        editable=False,
        related_name="client_ar_accounts",
    )
    loyalty_points = models.PositiveIntegerField(_("Loyalty Points"), default=0)
    credit_limit = models.DecimalField(_("Credit Limit"), max_digits=18, decimal_places=2, default=0)
    payment_terms = models.PositiveIntegerField(
        _("Payment Terms (Days)"), default=30,
        help_text=_("Number of days after invoice date by which payment is due.")
    )
    tier = models.CharField(
        _("Client Tier"), max_length=20,
        choices=[
            ("standard",  _("Standard")),
            ("silver",    _("Silver")),
            ("gold",      _("Gold")),
            ("platinum",  _("Platinum")),
        ],
        default="standard"
    )
    date_of_birth = models.DateField(_("Date of Birth"), blank=True, null=True)
    national_id = models.CharField(_("National ID"), max_length=50, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = _("Client Profile")
        verbose_name_plural = _("Client Profiles")
        ordering = ["user__last_name", "user__first_name"]

    def __str__(self):
        return self.user.get_full_name()

    def get_absolute_url(self):
        return reverse("client_profile_detail", kwargs={"pk": self.pk})


class SupplierProfile(TenantAwareModel):
    """Extended profile for supplier users."""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="supplier_profile"
    )
    department = models.ForeignKey(
        "department.Department", verbose_name=_("Assigned Department"),
        on_delete=models.SET_NULL, null=True, blank=True, related_name="suppliers"
    )
    company_name = models.CharField(_("Supplier Company Name"), max_length=255, blank=True, null=True)
    registration_number = models.CharField(
        _("Registration Number"), max_length=60, blank=True,
        help_text=_("Business registration / company number.")
    )
    vendor_account = models.ForeignKey(
        "accounting.Account",
        verbose_name=_("Accounts Payable Account"),
        on_delete=models.SET_NULL,
        null=True, blank=True,
        editable=False,
        related_name="supplier_ap_accounts",
    )
    payment_class = models.ForeignKey(
        "company.PaymentClass", verbose_name=_("Payment Class"), on_delete=models.PROTECT, null=True, blank=True
    )
    tax_id = models.CharField(_("Tax ID / TIN"), max_length=100, blank=True, null=True)
    payment_terms_days = models.PositiveIntegerField(_("Payment Terms (Days)"), default=30)
    is_approved = models.BooleanField(_("Approved Supplier?"), default=False)
    rating = models.DecimalField(
        _("Supplier Rating"), max_digits=3, decimal_places=2, default=0,
        help_text=_("Computed average evaluation score (0–5).")
    )
    notes = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = _("Supplier Profile")
        verbose_name_plural = _("Supplier Profiles")
        ordering = ["user__last_name", "user__first_name"]

    def __str__(self):
        return self.company_name or self.user.get_full_name()

    def get_absolute_url(self):
        return reverse("supplier_profile_detail", kwargs={"pk": self.pk})


class AgentProfile(TenantAwareModel):
    """
    Extended profile for AI-agent users.  Created automatically via post_save
    when CustomUser.user_type == "agent".
    """
    AGENT_TYPE_CHOICES = [
        ("monitor", _("Monitor")),
        ("executor", _("Executor")),
        ("analyst", _("Analyst")),
        ("assistant", _("Assistant")),
    ]
    STATUS_CHOICES = [
        ("active", _("Active")),
        ("paused", _("Paused")),
        ("error", _("Error")),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="agent_profile"
    )
    agent_type = models.CharField(_("Agent Type"), max_length=30, choices=AGENT_TYPE_CHOICES, default="assistant")
    capabilities = models.JSONField(_("Capabilities"), default=list, blank=True)
    assigned_modules = models.JSONField(_("Assigned Modules"), default=list, blank=True)
    status = models.CharField(_("Status"), max_length=20, choices=STATUS_CHOICES, default="active")
    api_key = models.CharField(_("API Key"), max_length=100, unique=True, blank=True)

    class Meta:
        verbose_name = _("Agent Profile")
        verbose_name_plural = _("Agent Profiles")
        ordering = ["user__email"]

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.get_agent_type_display()})"

    def save(self, *args, **kwargs):
        if not self.api_key:
            import secrets
            self.api_key = secrets.token_urlsafe(48)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("agent_profile_detail", kwargs={"pk": self.pk})


# Auto-create profile on user creation
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    if not created:
        return
    if instance.user_type == "staff":
        StaffProfile.objects.get_or_create(user=instance)
    elif instance.user_type == "client":
        ClientProfile.objects.get_or_create(user=instance)
    elif instance.user_type == "supplier":
        SupplierProfile.objects.get_or_create(user=instance)
    elif instance.user_type == "agent":
        AgentProfile.objects.get_or_create(user=instance)


# ─────────────────────────────────────────────────────────────────────────────
# Generic Contact Pattern
# Replaces the old Phone / Email / Website / Address separate models.
# Attach to ANY model via content_type + object_id.
# ─────────────────────────────────────────────────────────────────────────────

class ContactPoint(TenantAwareModel):
    """
    Polymorphic contact record.
    Use contact_type to distinguish phone / email / website / social etc.
    """
    CONTACT_TYPE_CHOICES = [
        ("phone", _("Phone")),
        ("mobile", _("Mobile")),
        ("email", _("Email")),
        ("website", _("Website")),
        ("fax", _("Fax")),
        ("linkedin", _("LinkedIn")),
        ("twitter", _("Twitter / X")),
        ("facebook", _("Facebook")),
        ("instagram", _("Instagram")),
        ("whatsapp", _("WhatsApp")),
        ("other", _("Other")),
    ]

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, verbose_name=_("Content Type"))
    object_id = models.UUIDField(verbose_name=_("Object ID"))
    contact_owner = GenericForeignKey("content_type", "object_id")

    contact_type = models.CharField(_("Contact Type"), max_length=20, choices=CONTACT_TYPE_CHOICES)
    value = models.CharField(_("Value"), max_length=500)
    label = models.CharField(_("Label"), max_length=100, blank=True, help_text=_("e.g. 'Work', 'Personal'"))
    is_primary = models.BooleanField(_("Is Primary?"), default=False)
    is_verified = models.BooleanField(_("Is Verified?"), default=False)
    is_whatsapp = models.BooleanField(_("Accepts WhatsApp?"), default=False)

    class Meta:
        verbose_name = _("Contact Point")
        verbose_name_plural = _("Contact Points")
        ordering = ["-is_primary", "contact_type"]
        indexes = [
            models.Index(fields=["content_type", "object_id"]),
        ]

    def __str__(self):
        return f"{self.get_contact_type_display()}: {self.value}"

    def save(self, *args, **kwargs):
        # Only one primary per type per object
        if self.is_primary:
            ContactPoint.objects.filter(
                content_type=self.content_type,
                object_id=self.object_id,
                contact_type=self.contact_type,
                is_primary=True,
            ).exclude(pk=self.pk).update(is_primary=False)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("contactpoint_detail", kwargs={"pk": self.pk})


class Address(TenantAwareModel):
    """
    Polymorphic address record.
    Can be attached to Company, Branch, Staff, Client, Supplier, etc.
    """
    ADDRESS_TYPE_CHOICES = [
        ("billing", _("Billing")),
        ("shipping", _("Shipping")),
        ("office", _("Office")),
        ("home", _("Home")),
        ("warehouse", _("Warehouse")),
        ("branch", _("Branch")),
        ("other", _("Other")),
    ]

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, verbose_name=_("Content Type"))
    object_id = models.UUIDField(verbose_name=_("Object ID"))
    address_owner = GenericForeignKey("content_type", "object_id")

    address_type = models.CharField(_("Address Type"), max_length=20, choices=ADDRESS_TYPE_CHOICES, default="office")
    line1 = models.CharField(_("Address Line 1"), max_length=255)
    line2 = models.CharField(_("Address Line 2"), max_length=255, blank=True)
    city = models.ForeignKey("contact.City", verbose_name=_("City"), on_delete=models.PROTECT, related_name="party_addresses")
    state = models.ForeignKey("contact.State", verbose_name=_("State"), on_delete=models.PROTECT, related_name="party_addresses")
    country = models.ForeignKey("contact.Country", verbose_name=_("Country"), on_delete=models.PROTECT, related_name="party_addresses")
    postal_code = models.CharField(_("Postal Code"), max_length=20, blank=True)
    is_primary = models.BooleanField(_("Is Primary?"), default=False)
    latitude = models.DecimalField(_("Latitude"), max_digits=10, decimal_places=8, blank=True, null=True)
    longitude = models.DecimalField(_("Longitude"), max_digits=11, decimal_places=8, blank=True, null=True)

    class Meta:
        verbose_name = _("Address")
        verbose_name_plural = _("Addresses")
        ordering = ["-is_primary", "address_type"]
        indexes = [
            models.Index(fields=["content_type", "object_id"]),
        ]

    def __str__(self):
        return f"{self.line1}, {self.city.name} ({self.get_address_type_display()})"

    def save(self, *args, **kwargs):
        if self.is_primary:
            Address.objects.filter(
                content_type=self.content_type,
                object_id=self.object_id,
                address_type=self.address_type,
                is_primary=True,
            ).exclude(pk=self.pk).update(is_primary=False)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("address_detail", kwargs={"pk": self.pk})


# ─────────────────────────────────────────────────────────────────────────────
# Company Documents
# ─────────────────────────────────────────────────────────────────────────────

class DocumentType(TenantAwareModel):
    name = models.CharField(_("Document Type"), max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = _("Document Type")
        verbose_name_plural = _("Document Types")
        ordering = ["name"]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("doctype_detail", kwargs={"pk": self.pk})


class Document(TenantAwareModel):
    document_type = models.ForeignKey(
        DocumentType, verbose_name=_("Document Type"),
        on_delete=models.SET_NULL, null=True, blank=True, related_name="documents"
    )
    document_url = models.CharField(_("Document File URL"), max_length=500)
    description = models.TextField(blank=True, null=True)
    custom_fields = models.JSONField(_("Custom Fields"), blank=True, null=True, default=dict)
    # Attach to any model (Company, StaffProfile, etc.)
    content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE, null=True, blank=True, verbose_name=_("Related Object Type")
    )
    object_id = models.UUIDField(null=True, blank=True, verbose_name=_("Related Object ID"))
    document_owner = GenericForeignKey("content_type", "object_id")

    class Meta:
        verbose_name = _("Document")
        verbose_name_plural = _("Documents")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["content_type", "object_id"]),
        ]

    def __str__(self):
        return str(self.document_url)

    def get_absolute_url(self):
        return reverse("document_detail", kwargs={"pk": self.pk})
