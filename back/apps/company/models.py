from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

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
    """Controls payment method availability and validation per company tier."""
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    # Which payment channels are permitted for this class
    allowed_methods = models.JSONField(
        default=list,
        blank=True,
        help_text="e.g. ['cash','mobile_money','bank_transfer','cheque']",
    )

    def __str__(self):
        return self.name


class BusinessType(createdtimestamp_uid, activearchlockedMixin):
    """e.g. Pharmacy, Clinic, Hospital, Retail, Wholesale, Manufacturing."""
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class Company(*_CompanyBase):
    """
    One Company == one PostgreSQL schema == one tenant.

    When USE_DJANGO_TENANTS=True the TenantMixin supplies `schema_name` and
    `auto_create_schema`.  The `slug` doubles as the schema_name.
    """
    auto_create_schema = True  # used by django-tenants when enabled

    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    schema_name = models.SlugField(blank=True)

    industry = models.ForeignKey(
        Industry, null=True, blank=True, on_delete=models.SET_NULL, related_name="companies"
    )
    payment = models.ForeignKey(
        PaymentClass, null=True, blank=True, on_delete=models.SET_NULL, related_name="companies"
    )
    business_type = models.ForeignKey(
        BusinessType, null=True, blank=True, on_delete=models.SET_NULL, related_name="companies"
    )
    default_currency = models.CharField(max_length=3, default="GHS")
    tradecountry = models.ForeignKey(
        "contact.Country", null=True, blank=True, on_delete=models.SET_NULL, related_name="companies"
    )
    contact = models.ManyToManyField("contact.Contact", blank=True, related_name="companies")
    logo = models.CharField(max_length=255, blank=True)
    # SaaS subscription fields
    paid_until = models.DateField(null=True, blank=True)
    on_trial = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if not self.schema_name:
            self.schema_name = self.slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Domain(*_DomainBase):
    """Maps subdomain/domain to a Company tenant."""

    if not getattr(settings, "USE_DJANGO_TENANTS", False):
        company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="domains")
        domain = models.CharField(max_length=255, unique=True)
        is_primary = models.BooleanField(default=False)

    def __str__(self):
        return getattr(self, "domain", str(self.pk))


# ---------------------------------------------------------------------------
# Post-save signal — seed address types when a Company is first created
# ---------------------------------------------------------------------------

@receiver(post_save, sender=Company)
def seed_company_initial_data(sender, instance, created, **kwargs):
    """Auto-seeds foundational lookup data when a new Company tenant is created."""
    if not created:
        return

    from django.apps import apps

    # 1. Seed AddressTypes
    AddressType = apps.get_model("contact", "AddressType")
    for name in ("Billing", "Shipping", "Office", "Warehouse"):
        AddressType.objects.get_or_create(name=name)

    # 2. Seed PhoneTypes
    PhoneType = apps.get_model("contact", "PhoneType")
    for name in ("Mobile", "Work", "Home", "Landline"):
        PhoneType.objects.get_or_create(name=name)

    # 3. Seed EmailTypes
    EmailType = apps.get_model("contact", "EmailType")
    for name in ("Personal", "Company"):
        EmailType.objects.get_or_create(name=name)

    # 4. Seed Charts of Account (full 5-type COA template)
    Charts_of_account = apps.get_model("accounts", "Charts_of_account")
    coa_seed = [
        # (name, account_type, acc_number)
        ("Cash and Cash Equivalents", "Assets", 10100000),
        ("Accounts Receivable", "Assets", 10101000),
        ("Inventory", "Assets", 10102000),
        ("Prepaid Expenses", "Assets", 10103000),
        ("Fixed Assets", "Assets", 10200000),
        ("Accounts Payable", "Liabilities", 20100000),
        ("Wages Payable", "Liabilities", 20102000),
        ("Taxes Payable", "Liabilities", 20104000),
        ("Short-term Loans Payable", "Liabilities", 20106000),
        ("Notes Payable", "Liabilities", 20108000),
        ("Interest Payable", "Liabilities", 20110000),
        ("Other Liabilities", "Liabilities", 20112000),
        ("Capital", "Capital_Equity", 30100000),
        ("Retained Earnings", "Capital_Equity", 30101000),
        ("Revenue / Income", "Revenues_Income", 40100000),
        ("Operational Income", "Revenues_Income", 40101000),
        ("Cost of Goods Sold", "Expenses", 50100000),
        ("Payroll Expenses", "Expenses", 50102000),
        ("Tax Expense", "Expenses", 50104000),
        ("Depreciation Expense", "Expenses", 50106000),
        ("Marketing Expenses", "Expenses", 50108000),
        ("Freight Expense", "Expenses", 50110000),
        ("Regular Expense", "Expenses", 50112000),
    ]
    for (name, acc_type, acc_num) in coa_seed:
        Charts_of_account.objects.get_or_create(
            name=name,
            defaults={"account_type": acc_type, "acc_number": acc_num},
        )
