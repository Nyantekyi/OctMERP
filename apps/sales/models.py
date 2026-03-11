"""
apps/sales/models.py

Sales order lifecycle for the ERP.

Covers:
  - Quotations → Sales Orders
  - Delivery (outbound dispatch)
  - Returns / credit notes
  - Commission records
"""

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from djmoney.models.fields import MoneyField

from apps.common.models import TenantAwareModel, DEFAULT_CURRENCY, CURRENCY_CHOICES


# ─────────────────────────────────────────────────────────────────────────────
# Quotation → Order
# ─────────────────────────────────────────────────────────────────────────────

class SalesQuotation(TenantAwareModel):
    STATUS_CHOICES = [
        ("draft", _("Draft")),
        ("sent", _("Sent to Client")),
        ("accepted", _("Accepted")),
        ("rejected", _("Rejected")),
        ("expired", _("Expired")),
        ("cancelled", _("Cancelled")),
    ]

    reference = models.CharField(_("Quotation Ref"), max_length=50, unique=True)
    client = models.ForeignKey(
        "party.ClientProfile", on_delete=models.PROTECT, related_name="quotations"
    )
    branch = models.ForeignKey("department.Branch", on_delete=models.PROTECT, related_name="quotations")
    issued_by = models.ForeignKey(
        "party.StaffProfile", on_delete=models.PROTECT, related_name="issued_quotations"
    )
    issue_date = models.DateField(_("Issue Date"), default=timezone.now)
    expiry_date = models.DateField(_("Expiry Date"), null=True, blank=True)
    status = models.CharField(_("Status"), max_length=20, choices=STATUS_CHOICES, default="draft")
    pricing_department = models.ForeignKey(
        "department.Department", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="quotation_pricing",
        help_text=_("Department whose ItemPricingDepartment rules apply to this quotation.")
    )
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
    notes = models.TextField(blank=True)
    terms = models.TextField(_("Terms and Conditions"), blank=True)

    class Meta:
        verbose_name = _("Sales Quotation")
        verbose_name_plural = _("Sales Quotations")
        ordering = ["-issue_date"]

    def __str__(self):
        return f"QUO-{self.reference}"


class SalesQuotationLine(TenantAwareModel):
    quotation = models.ForeignKey(SalesQuotation, on_delete=models.CASCADE, related_name="lines")
    product = models.ForeignKey("inventory.Product", on_delete=models.PROTECT, related_name="quotation_lines")
    variant = models.ForeignKey(
        "inventory.ProductVariant", on_delete=models.PROTECT, null=True, blank=True, related_name="quotation_lines"
    )
    quantity = models.DecimalField(_("Quantity"), max_digits=14, decimal_places=4)
    unit = models.ForeignKey("inventory.Unit", on_delete=models.PROTECT, related_name="quotation_lines")
    item_pricing = models.ForeignKey(
        "inventory.ItemPricingDepartment",
        on_delete=models.PROTECT, null=True, blank=True,
        related_name="quotation_lines",
        verbose_name=_("Pricing Rule")
    )
    unit_price = MoneyField(
        _("Unit Price"), max_digits=20, decimal_places=2,
        default=0, default_currency=DEFAULT_CURRENCY, currency_choices=CURRENCY_CHOICES
    )
    discount_percent = models.DecimalField(_("Discount %"), max_digits=5, decimal_places=2, default=0)
    tax = models.ForeignKey(
        "accounting.Tax", on_delete=models.SET_NULL, null=True, blank=True, related_name="quotation_lines"
    )
    line_total = MoneyField(
        _("Line Total"), max_digits=20, decimal_places=2,
        default=0, default_currency=DEFAULT_CURRENCY, currency_choices=CURRENCY_CHOICES, editable=False
    )
    description = models.CharField(_("Description / Note"), max_length=255, blank=True)

    class Meta:
        verbose_name = _("Quotation Line")
        verbose_name_plural = _("Quotation Lines")

    def save(self, *args, **kwargs):
        from decimal import Decimal
        net = self.unit_price * self.quantity
        discount = net * self.discount_percent / Decimal("100")
        self.line_total = net - discount
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.quotation} — {self.product.name} x {self.quantity}"


class SalesOrder(TenantAwareModel):
    STATUS_CHOICES = [
        ("draft", _("Draft")),
        ("confirmed", _("Confirmed")),
        ("picking", _("Picking in Progress")),
        ("partial", _("Partially Delivered")),
        ("delivered", _("Fully Delivered")),
        ("invoiced", _("Invoiced")),
        ("closed", _("Closed")),
        ("cancelled", _("Cancelled")),
    ]

    reference = models.CharField(_("SO Number"), max_length=50, unique=True)
    quotation = models.ForeignKey(
        SalesQuotation, on_delete=models.SET_NULL, null=True, blank=True, related_name="sales_orders"
    )
    client = models.ForeignKey("party.ClientProfile", on_delete=models.PROTECT, related_name="sales_orders")
    branch = models.ForeignKey("department.Branch", on_delete=models.PROTECT, related_name="sales_orders")
    processed_by = models.ForeignKey(
        "party.StaffProfile", on_delete=models.PROTECT, related_name="processed_sales_orders"
    )
    order_date = models.DateTimeField(_("Order Date"), default=timezone.now)
    requested_delivery_date = models.DateField(_("Requested Delivery Date"), null=True, blank=True)
    status = models.CharField(_("Status"), max_length=20, choices=STATUS_CHOICES, default="draft")
    pricing_department = models.ForeignKey(
        "department.Department", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="sales_order_pricing",
        help_text=_("Department whose ItemPricingDepartment rules apply to this order.")
    )
    shipping_address_line1 = models.CharField(_("Ship To Line 1"), max_length=255, blank=True)
    shipping_address_line2 = models.CharField(_("Ship To Line 2"), max_length=255, blank=True)
    shipping_city = models.ForeignKey(
        "contact.City", on_delete=models.SET_NULL, null=True, blank=True, related_name="sales_orders"
    )
    subtotal = MoneyField(
        _("Subtotal"), max_digits=20, decimal_places=2,
        default=0, default_currency=DEFAULT_CURRENCY, currency_choices=CURRENCY_CHOICES
    )
    discount_amount = MoneyField(
        _("Total Discount"), max_digits=20, decimal_places=2,
        default=0, default_currency=DEFAULT_CURRENCY, currency_choices=CURRENCY_CHOICES
    )
    tax_amount = MoneyField(
        _("Total Tax"), max_digits=20, decimal_places=2,
        default=0, default_currency=DEFAULT_CURRENCY, currency_choices=CURRENCY_CHOICES
    )
    total_amount = MoneyField(
        _("Total Amount"), max_digits=20, decimal_places=2,
        default=0, default_currency=DEFAULT_CURRENCY, currency_choices=CURRENCY_CHOICES
    )
    invoice = models.OneToOneField(
        "accounting.Invoice", on_delete=models.SET_NULL, null=True, blank=True, related_name="sales_order"
    )
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = _("Sales Order")
        verbose_name_plural = _("Sales Orders")
        ordering = ["-order_date"]

    def __str__(self):
        return f"SO-{self.reference}"


class SalesOrderLine(TenantAwareModel):
    order = models.ForeignKey(SalesOrder, on_delete=models.CASCADE, related_name="lines")
    product = models.ForeignKey("inventory.Product", on_delete=models.PROTECT, related_name="so_lines")
    variant = models.ForeignKey(
        "inventory.ProductVariant", on_delete=models.PROTECT, null=True, blank=True, related_name="so_lines"
    )
    quantity_ordered = models.DecimalField(_("Qty Ordered"), max_digits=14, decimal_places=4)
    quantity_delivered = models.DecimalField(_("Qty Delivered"), max_digits=14, decimal_places=4, default=0)
    unit = models.ForeignKey("inventory.Unit", on_delete=models.PROTECT, related_name="so_lines")
    item_pricing = models.ForeignKey(
        "inventory.ItemPricingDepartment",
        on_delete=models.PROTECT, null=True, blank=True,
        related_name="so_lines",
        verbose_name=_("Pricing Rule")
    )
    unit_price = MoneyField(
        _("Unit Price"), max_digits=20, decimal_places=2,
        default=0, default_currency=DEFAULT_CURRENCY, currency_choices=CURRENCY_CHOICES
    )
    discount_percent = models.DecimalField(_("Discount %"), max_digits=5, decimal_places=2, default=0)
    tax = models.ForeignKey(
        "accounting.Tax", on_delete=models.SET_NULL, null=True, blank=True, related_name="so_lines"
    )
    line_total = MoneyField(
        _("Line Total"), max_digits=20, decimal_places=2,
        default=0, default_currency=DEFAULT_CURRENCY, currency_choices=CURRENCY_CHOICES, editable=False
    )
    lot = models.ForeignKey(
        "inventory.ItemLot", on_delete=models.SET_NULL, null=True, blank=True, related_name="so_lines"
    )

    class Meta:
        verbose_name = _("SO Line")
        verbose_name_plural = _("SO Lines")

    def save(self, *args, **kwargs):
        from decimal import Decimal
        net = self.unit_price * self.quantity_ordered
        discount = net * self.discount_percent / Decimal("100")
        self.line_total = net - discount
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.order} — {self.product.name} x {self.quantity_ordered}"

    @property
    def quantity_remaining(self):
        return max(0, self.quantity_ordered - self.quantity_delivered)


# ─────────────────────────────────────────────────────────────────────────────
# Delivery
# ─────────────────────────────────────────────────────────────────────────────

class Delivery(TenantAwareModel):
    STATUS_CHOICES = [
        ("draft", _("Draft")),
        ("scheduled", _("Scheduled")),
        ("dispatched", _("Dispatched")),
        ("delivered", _("Delivered")),
        ("failed", _("Failed")),
        ("cancelled", _("Cancelled")),
    ]

    reference = models.CharField(_("Delivery Ref"), max_length=50, unique=True)
    sales_order = models.ForeignKey(SalesOrder, on_delete=models.PROTECT, related_name="deliveries")
    branch = models.ForeignKey("department.Branch", on_delete=models.PROTECT, related_name="deliveries")
    carrier = models.ForeignKey(
        "logistics.Carrier", on_delete=models.SET_NULL, null=True, blank=True, related_name="deliveries"
    )
    scheduled_date = models.DateField(_("Scheduled Date"), null=True, blank=True)
    actual_date = models.DateTimeField(_("Actual Delivery Date"), null=True, blank=True)
    status = models.CharField(_("Status"), max_length=20, choices=STATUS_CHOICES, default="draft")
    driver = models.ForeignKey(
        "logistics.Driver", on_delete=models.SET_NULL, null=True, blank=True, related_name="deliveries"
    )
    tracking_number = models.CharField(_("Tracking Number"), max_length=100, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = _("Delivery")
        verbose_name_plural = _("Deliveries")
        ordering = ["-scheduled_date"]

    def __str__(self):
        return f"DEL-{self.reference}"


class DeliveryLine(TenantAwareModel):
    delivery = models.ForeignKey(Delivery, on_delete=models.CASCADE, related_name="lines")
    so_line = models.ForeignKey(SalesOrderLine, on_delete=models.PROTECT, related_name="delivery_lines")
    quantity_dispatched = models.DecimalField(_("Qty Dispatched"), max_digits=14, decimal_places=4)
    lot = models.ForeignKey(
        "inventory.ItemLot", on_delete=models.SET_NULL, null=True, blank=True, related_name="delivery_lines"
    )

    class Meta:
        verbose_name = _("Delivery Line")
        verbose_name_plural = _("Delivery Lines")

    def __str__(self):
        return f"{self.delivery} — {self.so_line.product.name} x {self.quantity_dispatched}"


# ─────────────────────────────────────────────────────────────────────────────
# Sales Return / Credit Note
# ─────────────────────────────────────────────────────────────────────────────

class SalesReturn(TenantAwareModel):
    STATUS_CHOICES = [
        ("requested", _("Requested")),
        ("approved", _("Approved")),
        ("received", _("Goods Received")),
        ("refunded", _("Refunded")),
        ("rejected", _("Rejected")),
        ("cancelled", _("Cancelled")),
    ]
    RETURN_REASON_CHOICES = [
        ("defective", _("Defective / Damaged")),
        ("wrong_item", _("Wrong Item")),
        ("not_needed", _("No Longer Needed")),
        ("duplicate", _("Duplicate Order")),
        ("other", _("Other")),
    ]

    reference = models.CharField(_("Return Ref"), max_length=50, unique=True)
    sales_order = models.ForeignKey(SalesOrder, on_delete=models.PROTECT, related_name="returns")
    client = models.ForeignKey("party.ClientProfile", on_delete=models.PROTECT, related_name="sales_returns")
    return_date = models.DateField(_("Return Date"), default=timezone.now)
    reason = models.CharField(_("Reason"), max_length=20, choices=RETURN_REASON_CHOICES, default="other")
    reason_detail = models.TextField(blank=True)
    status = models.CharField(_("Status"), max_length=20, choices=STATUS_CHOICES, default="requested")
    refund_amount = MoneyField(
        _("Refund Amount"), max_digits=20, decimal_places=2,
        default=0, default_currency=DEFAULT_CURRENCY, currency_choices=CURRENCY_CHOICES
    )
    credit_note = models.OneToOneField(
        "accounting.Invoice", on_delete=models.SET_NULL, null=True, blank=True, related_name="sales_return"
    )
    transaction_doc = models.ForeignKey(
        "accounting.TransactionDoc", on_delete=models.SET_NULL, null=True, blank=True, related_name="sales_returns"
    )

    class Meta:
        verbose_name = _("Sales Return")
        verbose_name_plural = _("Sales Returns")
        ordering = ["-return_date"]

    def __str__(self):
        return f"RET-{self.reference}"


class SalesReturnLine(TenantAwareModel):
    sales_return = models.ForeignKey(SalesReturn, on_delete=models.CASCADE, related_name="lines")
    so_line = models.ForeignKey(SalesOrderLine, on_delete=models.PROTECT, related_name="return_lines")
    quantity_returned = models.DecimalField(_("Qty Returned"), max_digits=14, decimal_places=4)
    condition = models.CharField(
        _("Condition"), max_length=20,
        choices=[("good", "Good"), ("damaged", "Damaged"), ("unsellable", "Unsellable")],
        default="good"
    )

    class Meta:
        verbose_name = _("Return Line")
        verbose_name_plural = _("Return Lines")

    def __str__(self):
        return f"{self.sales_return} — {self.so_line.product.name} x {self.quantity_returned}"


# ─────────────────────────────────────────────────────────────────────────────
# Commission
# ─────────────────────────────────────────────────────────────────────────────

class CommissionRule(TenantAwareModel):
    """Defines the commission structure for a sales team or individual."""
    name = models.CharField(_("Rule Name"), max_length=100, unique=True)
    commission_rate_percent = models.DecimalField(_("Commission Rate %"), max_digits=5, decimal_places=2)
    applies_to = models.CharField(
        _("Applies To"), max_length=20,
        choices=[("team", "Sales Team"), ("individual", "Individual Staff")],
        default="individual"
    )
    team = models.ForeignKey(
        "crm.SaleTeam", on_delete=models.CASCADE, null=True, blank=True, related_name="commission_rules"
    )
    staff = models.ForeignKey(
        "party.StaffProfile", on_delete=models.CASCADE, null=True, blank=True, related_name="commission_rules"
    )

    class Meta:
        verbose_name = _("Commission Rule")
        verbose_name_plural = _("Commission Rules")

    def __str__(self):
        return self.name


class CommissionRecord(TenantAwareModel):
    STATUS_CHOICES = [
        ("pending", _("Pending")),
        ("paid", _("Paid")),
        ("cancelled", _("Cancelled")),
    ]

    rule = models.ForeignKey(CommissionRule, on_delete=models.PROTECT, related_name="records")
    staff = models.ForeignKey("party.StaffProfile", on_delete=models.PROTECT, related_name="commissions")
    sales_order = models.ForeignKey(SalesOrder, on_delete=models.PROTECT, related_name="commission_records")
    base_amount = MoneyField(
        _("Base Amount"), max_digits=20, decimal_places=2,
        default=0, default_currency=DEFAULT_CURRENCY, currency_choices=CURRENCY_CHOICES
    )
    commission_amount = MoneyField(
        _("Commission Amount"), max_digits=20, decimal_places=2,
        default=0, default_currency=DEFAULT_CURRENCY, currency_choices=CURRENCY_CHOICES
    )
    status = models.CharField(_("Status"), max_length=20, choices=STATUS_CHOICES, default="pending")
    period = models.DateField(_("Period"))

    class Meta:
        verbose_name = _("Commission Record")
        verbose_name_plural = _("Commission Records")
        ordering = ["-period"]

    def __str__(self):
        return f"{self.staff} — {self.commission_amount} commission on SO-{self.sales_order.reference}"
