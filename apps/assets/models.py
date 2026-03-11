"""
apps/assets/models.py

Fixed-asset lifecycle management:
  - Asset categories and individual assets
  - Depreciation schedules (straight-line / declining-balance / sum-of-years-digits)
  - Maintenance records
  - Disposal and write-off
  - Branch/department transfers
"""

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from djmoney.models.fields import MoneyField

from apps.common.models import TenantAwareModel, DEFAULT_CURRENCY, CURRENCY_CHOICES


# ─────────────────────────────────────────────────────────────────────────────
# Asset Category
# ─────────────────────────────────────────────────────────────────────────────

class AssetCategory(TenantAwareModel):
    """
    Hierarchical category for assets (e.g. Property → Buildings,
    Equipment → Office Equipment → Computers).
    Holds the default depreciation policy for the category.
    """
    DEPRECIATION_METHOD_CHOICES = [
        ("straight_line", _("Straight Line")),
        ("declining_balance", _("Declining Balance")),
        ("sum_of_years", _("Sum of Years Digits")),
        ("none", _("No Depreciation")),
    ]

    name = models.CharField(_("Category Name"), max_length=100)
    parent = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, blank=True, related_name="children"
    )
    account_asset = models.ForeignKey(
        "accounting.Account", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="category_asset_accounts", verbose_name=_("Asset Account")
    )
    account_depreciation = models.ForeignKey(
        "accounting.Account", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="category_depreciation_accounts", verbose_name=_("Accumulated Depreciation Account")
    )
    account_expense = models.ForeignKey(
        "accounting.Account", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="category_expense_accounts", verbose_name=_("Depreciation Expense Account")
    )
    default_depreciation_method = models.CharField(
        _("Default Depreciation Method"), max_length=30,
        choices=DEPRECIATION_METHOD_CHOICES, default="straight_line"
    )
    default_useful_life_years = models.PositiveSmallIntegerField(_("Default Useful Life (years)"), default=5)
    default_residual_value = models.DecimalField(
        _("Default Residual Value (%)"), max_digits=5, decimal_places=2, default=0
    )
    description = models.TextField(blank=True)

    class Meta:
        verbose_name = _("Asset Category")
        verbose_name_plural = _("Asset Categories")
        ordering = ["name"]

    def __str__(self):
        return self.name


# ─────────────────────────────────────────────────────────────────────────────
# Asset
# ─────────────────────────────────────────────────────────────────────────────

class Asset(TenantAwareModel):
    STATUS_CHOICES = [
        ("draft", _("Draft")),
        ("active", _("Active")),
        ("disposed", _("Disposed")),
        ("written_off", _("Written Off")),
        ("under_repair", _("Under Repair")),
    ]
    DEPRECIATION_METHOD_CHOICES = AssetCategory.DEPRECIATION_METHOD_CHOICES

    asset_code = models.CharField(_("Asset Code"), max_length=50, unique=True)
    name = models.CharField(_("Asset Name"), max_length=100)
    category = models.ForeignKey(AssetCategory, on_delete=models.PROTECT, related_name="assets")
    branch = models.ForeignKey(
        "department.Branch", on_delete=models.PROTECT, related_name="assets"
    )
    department = models.ForeignKey(
        "department.Department", on_delete=models.SET_NULL, null=True, blank=True, related_name="assets"
    )
    assigned_to = models.ForeignKey(
        "party.StaffProfile", on_delete=models.SET_NULL, null=True, blank=True, related_name="assigned_assets"
    )
    supplier = models.ForeignKey(
        "party.SupplierProfile", on_delete=models.SET_NULL, null=True, blank=True, related_name="supplied_assets"
    )
    purchase_date = models.DateField(_("Purchase Date"))
    purchase_cost = MoneyField(
        _("Purchase Cost"), max_digits=20, decimal_places=2,
        default=0, default_currency=DEFAULT_CURRENCY, currency_choices=CURRENCY_CHOICES
    )
    residual_value = MoneyField(
        _("Residual / Salvage Value"), max_digits=20, decimal_places=2,
        default=0, default_currency=DEFAULT_CURRENCY, currency_choices=CURRENCY_CHOICES
    )
    useful_life_years = models.PositiveSmallIntegerField(_("Useful Life (years)"), default=5)
    depreciation_method = models.CharField(
        _("Depreciation Method"), max_length=30,
        choices=DEPRECIATION_METHOD_CHOICES, default="straight_line"
    )
    status = models.CharField(_("Status"), max_length=20, choices=STATUS_CHOICES, default="draft")
    serial_number = models.CharField(_("Serial Number"), max_length=100, blank=True)
    model_number = models.CharField(_("Model Number"), max_length=100, blank=True)
    warranty_expiry = models.DateField(_("Warranty Expiry"), null=True, blank=True)
    # Links to accounting (auto-set via signal)
    asset_account = models.ForeignKey(
        "accounting.Account", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="asset_records", editable=False
    )
    disposal_date = models.DateField(_("Disposal Date"), null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = _("Asset")
        verbose_name_plural = _("Assets")
        ordering = ["category", "asset_code"]

    def __str__(self):
        return f"{self.asset_code} — {self.name}"

    @property
    def current_book_value(self):
        total_depreciated = self.depreciations.aggregate(
            total=models.Sum("amount")
        )["total"] or Decimal("0")
        return self.purchase_cost - total_depreciated

    @property
    def accumulated_depreciation(self):
        return self.depreciations.aggregate(total=models.Sum("amount"))["total"] or Decimal("0")


# ─────────────────────────────────────────────────────────────────────────────
# Depreciation
# ─────────────────────────────────────────────────────────────────────────────

class AssetDepreciation(TenantAwareModel):
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name="depreciations")
    period_start = models.DateField(_("Period Start"))
    period_end = models.DateField(_("Period End"))
    amount = MoneyField(
        _("Depreciation Amount"), max_digits=20, decimal_places=2,
        default=0, default_currency=DEFAULT_CURRENCY, currency_choices=CURRENCY_CHOICES
    )
    book_value_after = MoneyField(
        _("Book Value After"), max_digits=20, decimal_places=2,
        default=0, default_currency=DEFAULT_CURRENCY, currency_choices=CURRENCY_CHOICES
    )
    journal_entry = models.ForeignKey(
        "accounting.JournalEntry", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="depreciation_entries"
    )
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = _("Asset Depreciation")
        verbose_name_plural = _("Asset Depreciations")
        ordering = ["-period_end"]
        unique_together = ("asset", "period_start", "period_end")

    def __str__(self):
        return f"{self.asset} depr. {self.period_start}→{self.period_end}"


# ─────────────────────────────────────────────────────────────────────────────
# Maintenance
# ─────────────────────────────────────────────────────────────────────────────

class AssetMaintenance(TenantAwareModel):
    MAINTENANCE_TYPE_CHOICES = [
        ("preventive", _("Preventive")),
        ("corrective", _("Corrective")),
        ("inspection", _("Inspection")),
        ("upgrade", _("Upgrade")),
    ]
    STATUS_CHOICES = [
        ("scheduled", _("Scheduled")),
        ("in_progress", _("In Progress")),
        ("completed", _("Completed")),
        ("cancelled", _("Cancelled")),
    ]

    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name="maintenance_records")
    maintenance_type = models.CharField(_("Type"), max_length=20, choices=MAINTENANCE_TYPE_CHOICES)
    description = models.CharField(_("Description"), max_length=255)
    requested_by = models.ForeignKey(
        "party.StaffProfile", on_delete=models.SET_NULL, null=True, blank=True, related_name="maintenance_requests"
    )
    assigned_to = models.ForeignKey(
        "party.StaffProfile", on_delete=models.SET_NULL, null=True, blank=True, related_name="maintenance_assignments"
    )
    scheduled_date = models.DateField(_("Scheduled Date"), null=True, blank=True)
    actual_date = models.DateField(_("Actual Date"), null=True, blank=True)
    cost = MoneyField(
        _("Cost"), max_digits=20, decimal_places=2,
        default=0, default_currency=DEFAULT_CURRENCY, currency_choices=CURRENCY_CHOICES
    )
    status = models.CharField(_("Status"), max_length=20, choices=STATUS_CHOICES, default="scheduled")
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = _("Asset Maintenance")
        verbose_name_plural = _("Asset Maintenance Records")
        ordering = ["-scheduled_date"]

    def __str__(self):
        return f"{self.asset} — {self.maintenance_type} ({self.status})"


# ─────────────────────────────────────────────────────────────────────────────
# Disposal
# ─────────────────────────────────────────────────────────────────────────────

class AssetDisposal(TenantAwareModel):
    DISPOSAL_METHOD_CHOICES = [
        ("sale", _("Sale")),
        ("scrap", _("Scrap")),
        ("donation", _("Donation")),
        ("write_off", _("Write-Off")),
    ]

    asset = models.OneToOneField(Asset, on_delete=models.PROTECT, related_name="disposal")
    disposal_method = models.CharField(_("Disposal Method"), max_length=20, choices=DISPOSAL_METHOD_CHOICES)
    disposal_date = models.DateField(_("Disposal Date"))
    proceeds = MoneyField(
        _("Proceeds Received"), max_digits=20, decimal_places=2,
        default=0, default_currency=DEFAULT_CURRENCY, currency_choices=CURRENCY_CHOICES
    )
    book_value_at_disposal = MoneyField(
        _("Book Value at Disposal"), max_digits=20, decimal_places=2,
        default=0, default_currency=DEFAULT_CURRENCY, currency_choices=CURRENCY_CHOICES
    )
    gain_loss = MoneyField(
        _("Gain / Loss"), max_digits=20, decimal_places=2,
        default=0, default_currency=DEFAULT_CURRENCY, currency_choices=CURRENCY_CHOICES, editable=False
    )
    journal_entry = models.ForeignKey(
        "accounting.JournalEntry", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="disposal_entries"
    )
    buyer_name = models.CharField(_("Buyer / Recipient"), max_length=200, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = _("Asset Disposal")
        verbose_name_plural = _("Asset Disposals")

    def save(self, *args, **kwargs):
        self.gain_loss = self.proceeds - self.book_value_at_disposal
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.asset} disposed via {self.disposal_method} on {self.disposal_date}"


# ─────────────────────────────────────────────────────────────────────────────
# Transfer
# ─────────────────────────────────────────────────────────────────────────────

class AssetTransfer(TenantAwareModel):
    STATUS_CHOICES = [
        ("pending", _("Pending Approval")),
        ("approved", _("Approved")),
        ("completed", _("Completed")),
        ("rejected", _("Rejected")),
    ]

    asset = models.ForeignKey(Asset, on_delete=models.PROTECT, related_name="transfers")
    from_branch = models.ForeignKey(
        "department.Branch", on_delete=models.PROTECT, related_name="asset_transfers_out"
    )
    to_branch = models.ForeignKey(
        "department.Branch", on_delete=models.PROTECT, related_name="asset_transfers_in"
    )
    from_department = models.ForeignKey(
        "department.Department", on_delete=models.SET_NULL, null=True, blank=True, related_name="asset_transfers_out"
    )
    to_department = models.ForeignKey(
        "department.Department", on_delete=models.SET_NULL, null=True, blank=True, related_name="asset_transfers_in"
    )
    transfer_date = models.DateField(_("Transfer Date"))
    requested_by = models.ForeignKey(
        "party.StaffProfile", on_delete=models.SET_NULL, null=True, blank=True, related_name="asset_transfer_requests"
    )
    approved_by = models.ForeignKey(
        "party.StaffProfile", on_delete=models.SET_NULL, null=True, blank=True, related_name="asset_transfer_approvals"
    )
    status = models.CharField(_("Status"), max_length=20, choices=STATUS_CHOICES, default="pending")
    reason = models.TextField(blank=True)

    class Meta:
        verbose_name = _("Asset Transfer")
        verbose_name_plural = _("Asset Transfers")
        ordering = ["-transfer_date"]

    def __str__(self):
        return f"{self.asset} from {self.from_branch} → {self.to_branch}"


# ─────────────────────────────────────────────────────────────────────────────
# Signal: auto-create asset account on Asset creation
# ─────────────────────────────────────────────────────────────────────────────

@receiver(post_save, sender=Asset)
def create_asset_account(sender, instance, created, **kwargs):
    if not created or not instance.name:
        return
    try:
        from django.contrib.contenttypes.models import ContentType
        from apps.accounting.models import Account
        if instance.category.account_asset:
            ct = ContentType.objects.get_for_model(sender)
            acc, _ = Account.objects.get_or_create(
                content_type=ct, object_id=instance.id,
                account_type=instance.category.account_asset
            )
            Asset.objects.filter(pk=instance.id).update(asset_account=acc)
    except Exception:
        pass
