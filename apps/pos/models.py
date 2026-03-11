"""
apps/pos/models.py

Point of Sale system for the ERP.

Covers:
  - POS configuration per branch
  - POS sessions (replaces the old Tender_Repository)
  - POS orders (in-store transactions)
  - POS order lines
  - POS payments (multi-tender)
  - Cash drawer open/close events
"""

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from djmoney.models.fields import MoneyField

from apps.common.models import TenantAwareModel, DEFAULT_CURRENCY, CURRENCY_CHOICES


# ─────────────────────────────────────────────────────────────────────────────
# POS Configuration
# ─────────────────────────────────────────────────────────────────────────────

class POSConfig(TenantAwareModel):
    """
    Per-branch POS terminal configuration.
    One branch can have multiple terminals (e.g. cashier 1, cashier 2).
    """
    name = models.CharField(_("Terminal Name"), max_length=100)
    branch = models.ForeignKey("department.Branch", on_delete=models.CASCADE, related_name="pos_configs")
    allowed_payment_methods = models.JSONField(
        _("Allowed Payment Methods"),
        default=list,
        help_text=_("List of method keys: cash, card, mobile_money, etc.")
    )
    allow_discount = models.BooleanField(_("Allow Discounts?"), default=True)
    max_discount_percent = models.DecimalField(_("Max Discount %"), max_digits=5, decimal_places=2, default=100)
    require_customer = models.BooleanField(_("Require Customer?"), default=False)
    allow_negative_stock = models.BooleanField(_("Allow Negative Stock?"), default=False)
    opening_float = MoneyField(
        _("Default Opening Float"), max_digits=20, decimal_places=2,
        default=0, default_currency=DEFAULT_CURRENCY, currency_choices=CURRENCY_CHOICES
    )
    receipt_header = models.TextField(_("Receipt Header"), blank=True)
    receipt_footer = models.TextField(_("Receipt Footer"), blank=True)
    printer_ip = models.GenericIPAddressField(_("Receipt Printer IP"), null=True, blank=True)

    class Meta:
        verbose_name = _("POS Config")
        verbose_name_plural = _("POS Configs")
        unique_together = ("branch", "name")
        ordering = ["branch", "name"]

    def __str__(self):
        return f"{self.name} @ {self.branch}"


# ─────────────────────────────────────────────────────────────────────────────
# POS Session  (formerly Tender_Repository)
# ─────────────────────────────────────────────────────────────────────────────

class POSSession(TenantAwareModel):
    """
    A daily/shift open-close cycle for a POS terminal.
    A cash account is auto-created for each session via post_save signal.
    """
    STATUS_CHOICES = [
        ("new", _("New / Not Started")),
        ("open", _("Open")),
        ("closing", _("Closing")),
        ("closed", _("Closed")),
    ]

    config = models.ForeignKey(POSConfig, on_delete=models.PROTECT, related_name="sessions")
    cashier = models.ForeignKey(
        "party.StaffProfile", on_delete=models.PROTECT, related_name="pos_sessions"
    )
    opened_at = models.DateTimeField(_("Opened At"), null=True, blank=True)
    closed_at = models.DateTimeField(_("Closed At"), null=True, blank=True)
    status = models.CharField(_("Status"), max_length=10, choices=STATUS_CHOICES, default="new")
    opening_balance = MoneyField(
        _("Opening Balance (Float)"), max_digits=20, decimal_places=2,
        default=0, default_currency=DEFAULT_CURRENCY, currency_choices=CURRENCY_CHOICES
    )
    closing_balance = MoneyField(
        _("Closing Balance (Counted)"), max_digits=20, decimal_places=2,
        default=0, default_currency=DEFAULT_CURRENCY, currency_choices=CURRENCY_CHOICES
    )
    expected_balance = MoneyField(
        _("Expected Balance"), max_digits=20, decimal_places=2,
        default=0, default_currency=DEFAULT_CURRENCY, currency_choices=CURRENCY_CHOICES, editable=False
    )
    difference = MoneyField(
        _("Difference (Over/Short)"), max_digits=20, decimal_places=2,
        default=0, default_currency=DEFAULT_CURRENCY, currency_choices=CURRENCY_CHOICES, editable=False
    )
    notes = models.TextField(blank=True)
    # Auto-linked cash account (mirrors the old Tender_Repository pattern)
    cash_account = models.ForeignKey(
        "accounting.Account", null=True, blank=True, editable=False,
        on_delete=models.SET_NULL, related_name="pos_sessions"
    )

    class Meta:
        verbose_name = _("POS Session")
        verbose_name_plural = _("POS Sessions")
        ordering = ["-opened_at"]

    def __str__(self):
        return f"{self.config} — {self.opened_at or 'Not started'}"

    def open(self):
        if self.status != "new":
            raise ValidationError(_("Session is already open or closed."))
        self.status = "open"
        self.opened_at = timezone.now()
        self.save()

    def close(self, counted_balance):
        self.closing_balance = counted_balance
        self.status = "closed"
        self.closed_at = timezone.now()
        self.save()


# ─────────────────────────────────────────────────────────────────────────────
# POS Order
# ─────────────────────────────────────────────────────────────────────────────

class POSOrder(TenantAwareModel):
    STATUS_CHOICES = [
        ("draft", _("Draft / In Progress")),
        ("paid", _("Paid")),
        ("refunded", _("Refunded")),
        ("cancelled", _("Cancelled")),
    ]

    session = models.ForeignKey(POSSession, on_delete=models.PROTECT, related_name="orders")
    client = models.ForeignKey(
        "party.ClientProfile", on_delete=models.SET_NULL, null=True, blank=True, related_name="pos_orders"
    )
    order_date = models.DateTimeField(_("Order Date"), default=timezone.now)
    status = models.CharField(_("Status"), max_length=20, choices=STATUS_CHOICES, default="draft")
    subtotal = MoneyField(
        _("Subtotal"), max_digits=20, decimal_places=2,
        default=0, default_currency=DEFAULT_CURRENCY, currency_choices=CURRENCY_CHOICES
    )
    discount_amount = MoneyField(
        _("Discount Amount"), max_digits=20, decimal_places=2,
        default=0, default_currency=DEFAULT_CURRENCY, currency_choices=CURRENCY_CHOICES
    )
    tax_amount = MoneyField(
        _("Tax Amount"), max_digits=20, decimal_places=2,
        default=0, default_currency=DEFAULT_CURRENCY, currency_choices=CURRENCY_CHOICES
    )
    total_amount = MoneyField(
        _("Total Amount"), max_digits=20, decimal_places=2,
        default=0, default_currency=DEFAULT_CURRENCY, currency_choices=CURRENCY_CHOICES
    )
    amount_tendered = MoneyField(
        _("Amount Tendered"), max_digits=20, decimal_places=2,
        default=0, default_currency=DEFAULT_CURRENCY, currency_choices=CURRENCY_CHOICES
    )
    change_due = MoneyField(
        _("Change Due"), max_digits=20, decimal_places=2,
        default=0, default_currency=DEFAULT_CURRENCY, currency_choices=CURRENCY_CHOICES, editable=False
    )
    invoice = models.OneToOneField(
        "accounting.Invoice", on_delete=models.SET_NULL, null=True, blank=True, related_name="pos_order"
    )
    transaction_doc = models.ForeignKey(
        "accounting.TransactionDoc", on_delete=models.SET_NULL, null=True, blank=True, related_name="pos_orders"
    )
    receipt_printed = models.BooleanField(_("Receipt Printed?"), default=False)
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = _("POS Order")
        verbose_name_plural = _("POS Orders")
        ordering = ["-order_date"]

    def __str__(self):
        return f"POS-{self.pk} — {self.total_amount}"

    def compute_change(self):
        self.change_due = max(self.amount_tendered - self.total_amount,
                              type(self.total_amount)(0, self.total_amount.currency))
        return self.change_due


class POSOrderLine(TenantAwareModel):
    order = models.ForeignKey(POSOrder, on_delete=models.CASCADE, related_name="lines")
    product = models.ForeignKey("inventory.Product", on_delete=models.PROTECT, related_name="pos_lines")
    variant = models.ForeignKey(
        "inventory.ProductVariant", on_delete=models.PROTECT, null=True, blank=True, related_name="pos_lines"
    )
    quantity = models.DecimalField(_("Quantity"), max_digits=14, decimal_places=4)
    unit = models.ForeignKey("inventory.Unit", on_delete=models.PROTECT, related_name="pos_lines")
    item_pricing = models.ForeignKey(
        "inventory.ItemPricingDepartment",
        on_delete=models.PROTECT, null=True, blank=True,
        related_name="pos_lines",
        verbose_name=_("Pricing Rule")
    )
    unit_price = MoneyField(
        _("Unit Price"), max_digits=20, decimal_places=2,
        default=0, default_currency=DEFAULT_CURRENCY, currency_choices=CURRENCY_CHOICES
    )
    discount_percent = models.DecimalField(_("Discount %"), max_digits=5, decimal_places=2, default=0)
    tax = models.ForeignKey(
        "accounting.Tax", on_delete=models.SET_NULL, null=True, blank=True, related_name="pos_lines"
    )
    line_total = MoneyField(
        _("Line Total"), max_digits=20, decimal_places=2,
        default=0, default_currency=DEFAULT_CURRENCY, currency_choices=CURRENCY_CHOICES, editable=False
    )
    lot = models.ForeignKey(
        "inventory.ItemLot", on_delete=models.SET_NULL, null=True, blank=True, related_name="pos_lines"
    )
    is_returned = models.BooleanField(_("Returned?"), default=False)

    class Meta:
        verbose_name = _("POS Order Line")
        verbose_name_plural = _("POS Order Lines")

    def save(self, *args, **kwargs):
        from decimal import Decimal
        net = self.unit_price * self.quantity
        self.line_total = net * (1 - self.discount_percent / Decimal("100"))
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.order} — {self.product.name} x {self.quantity}"


# ─────────────────────────────────────────────────────────────────────────────
# POS Payment (multi-tender)
# ─────────────────────────────────────────────────────────────────────────────

class POSPayment(TenantAwareModel):
    """One row per tender/payment method used in a POS transaction."""
    PAYMENT_METHOD_CHOICES = [
        ("cash", _("Cash")),
        ("card", _("Card")),
        ("mobile_money", _("Mobile Money")),
        ("voucher", _("Voucher")),
        ("loyalty_points", _("Loyalty Points")),
        ("bank_transfer", _("Bank Transfer")),
        ("other", _("Other")),
    ]

    order = models.ForeignKey(POSOrder, on_delete=models.CASCADE, related_name="payments")
    payment_method = models.CharField(_("Payment Method"), max_length=20, choices=PAYMENT_METHOD_CHOICES)
    amount = MoneyField(
        _("Amount"), max_digits=20, decimal_places=2,
        default=0, default_currency=DEFAULT_CURRENCY, currency_choices=CURRENCY_CHOICES
    )
    reference = models.CharField(_("Payment Reference"), max_length=100, blank=True)
    payment_at = models.DateTimeField(_("Payment Time"), default=timezone.now)
    bank_account = models.ForeignKey(
        "accounting.BankAccount", on_delete=models.SET_NULL, null=True, blank=True, related_name="pos_payments"
    )

    class Meta:
        verbose_name = _("POS Payment")
        verbose_name_plural = _("POS Payments")
        ordering = ["-payment_at"]

    def __str__(self):
        return f"{self.payment_method}: {self.amount} on {self.order}"


# ─────────────────────────────────────────────────────────────────────────────
# Cash Drawer Events
# ─────────────────────────────────────────────────────────────────────────────

class CashDrawerEvent(TenantAwareModel):
    """
    Records cash going in/out of the till outside of a sale
    (float top-up, petty cash out, etc.).
    """
    EVENT_TYPE_CHOICES = [
        ("float_in", _("Float In")),
        ("float_out", _("Float Out")),
        ("petty_cash_out", _("Petty Cash Out")),
        ("other_in", _("Other In")),
        ("other_out", _("Other Out")),
    ]

    session = models.ForeignKey(POSSession, on_delete=models.CASCADE, related_name="cash_events")
    event_type = models.CharField(_("Event Type"), max_length=20, choices=EVENT_TYPE_CHOICES)
    amount = MoneyField(
        _("Amount"), max_digits=20, decimal_places=2,
        default=0, default_currency=DEFAULT_CURRENCY, currency_choices=CURRENCY_CHOICES
    )
    reason = models.CharField(_("Reason"), max_length=255)
    performed_by = models.ForeignKey(
        "party.StaffProfile", on_delete=models.PROTECT, related_name="cash_draw_events"
    )
    occurred_at = models.DateTimeField(_("Occurred At"), default=timezone.now)

    class Meta:
        verbose_name = _("Cash Drawer Event")
        verbose_name_plural = _("Cash Drawer Events")
        ordering = ["-occurred_at"]

    def __str__(self):
        return f"{self.event_type}: {self.amount} in {self.session}"


# ─────────────────────────────────────────────────────────────────────────────
# Auto-create Cash Account for new POS Session
# ─────────────────────────────────────────────────────────────────────────────

@receiver(post_save, sender=POSSession)
def create_pos_session_account(sender, instance, created, **kwargs):
    if not created:
        return
    try:
        from django.contrib.contenttypes.models import ContentType
        from apps.accounting.models import Account, ChartsOfAccount
        coa = ChartsOfAccount.objects.get(name="Cash")
        ct = ContentType.objects.get_for_model(sender)
        acc, _ = Account.objects.get_or_create(
            content_type=ct, object_id=instance.id, account_type=coa
        )
        POSSession.objects.filter(pk=instance.id).update(cash_account=acc)
    except Exception:
        pass
