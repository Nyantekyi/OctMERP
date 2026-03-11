"""
apps/invplan/models.py

Inventory Planning: order documents (purchase/transfer/adjustment/return),
Carrier management, Terms & Conditions, and Transfer documents.
This is the central hub for all physical inventory movement documents.
"""

import uuid
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from djmoney.models.fields import MoneyField

from apps.common.models import TenantAwareModel, DEFAULT_CURRENCY, CURRENCY_CHOICES


# ─────────────────────────────────────────────────────────────────────────────
# Terms & Conditions
# ─────────────────────────────────────────────────────────────────────────────

class TermsAndCondition(TenantAwareModel):
    code = models.CharField(_("Code"), max_length=50, unique=True)
    exchangeable = models.BooleanField(default=False)
    warranty_included = models.BooleanField(default=False)
    defective_returns_allowed = models.BooleanField(default=False)
    delivery_insurance_provided = models.BooleanField(default=False)
    cod_allowed = models.BooleanField(_("COD Allowed"), default=False)
    cancellation_policy_available = models.BooleanField(default=False)
    free_shipping_available = models.BooleanField(default=False)
    return_window_days = models.PositiveIntegerField(_("Return Window (days)"), default=0)

    class Meta:
        verbose_name = _("Terms & Condition")

    def __str__(self):
        return self.code


# ─────────────────────────────────────────────────────────────────────────────
# Inventory Condition
# ─────────────────────────────────────────────────────────────────────────────

class InventoryCondition(TenantAwareModel):
    name = models.CharField(max_length=50, unique=True)
    # e.g. good / broken / damaged / partial_shipment / overage

    class Meta:
        verbose_name = _("Inventory Condition")

    def __str__(self):
        return self.name


# ─────────────────────────────────────────────────────────────────────────────
# Carrier
# ─────────────────────────────────────────────────────────────────────────────

class Carrier(TenantAwareModel):
    name = models.CharField(_("Carrier Name"), max_length=100, unique=True)
    description = models.TextField(blank=True)
    carrier_account = models.ForeignKey(
        "accounting.Account", on_delete=models.SET_NULL, null=True, blank=True,
        editable=False, related_name="invplan_carrier_payable"
    )

    class Meta:
        verbose_name = _("Carrier")

    def __str__(self):
        return self.name


# ─────────────────────────────────────────────────────────────────────────────
# Order Document  (base for ALL inventory movements)
# ─────────────────────────────────────────────────────────────────────────────

class OrderDocument(TenantAwareModel):
    ORDER_TYPE_CHOICES = [
        ("order_document", _("General Order")),
        ("purchase_order", _("Purchase Order")),
        ("sales_order", _("Sales Order")),
        ("transfer_order", _("Transfer Order")),
        ("adjustment_order", _("Adjustment Order")),
        ("return_order", _("Return Order")),
    ]
    STATUS_CHOICES = [
        ("pending", _("Pending")),
        ("approved", _("Approved")),
        ("fulfilled", _("Fulfilled")),
        ("canceled", _("Canceled")),
    ]

    ordertype = models.CharField(_("Order Type"), max_length=30, choices=ORDER_TYPE_CHOICES)
    title = models.CharField(_("Document No."), max_length=50, editable=False)
    source_document = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.SET_NULL, related_name="children"
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    branch = models.ForeignKey("department.Branch", on_delete=models.PROTECT, related_name="order_documents")
    staff = models.ForeignKey(
        "party.CustomUser", on_delete=models.PROTECT, related_name="created_order_documents"
    )
    vendor = models.ForeignKey(
        "party.SupplierProfile", on_delete=models.PROTECT,
        null=True, blank=True, related_name="order_documents"
    )
    client = models.ForeignKey(
        "party.ClientProfile", on_delete=models.PROTECT,
        null=True, blank=True, related_name="order_documents"
    )
    sourcebranch = models.ForeignKey(
        "department.Branch", on_delete=models.PROTECT,
        null=True, blank=True, related_name="transfer_source_documents"
    )
    carrier = models.ForeignKey(
        Carrier, on_delete=models.SET_NULL, null=True, blank=True, related_name="order_documents"
    )
    terms = models.ForeignKey(
        TermsAndCondition, on_delete=models.SET_NULL, null=True, blank=True
    )
    order_amount = MoneyField(
        max_digits=20, decimal_places=2, default=0,
        default_currency=DEFAULT_CURRENCY, currency_choices=CURRENCY_CHOICES
    )
    expected_delivery_date = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = _("Order Document")
        unique_together = ("title", "branch", "ordertype")

    def __str__(self):
        return f"{self.title} ({self.ordertype})"

    def clean(self):
        if self.ordertype in ("purchase_order", "return_order") and not self.vendor:
            raise ValidationError(_("Vendor is required for purchase/return orders."))
        if self.ordertype == "sales_order" and not self.client:
            raise ValidationError(_("Client is required for sales orders."))
        if self.ordertype == "transfer_order" and not self.sourcebranch:
            raise ValidationError(_("Source branch is required for transfer orders."))

    def save(self, *args, **kwargs):
        if not self.title:
            prefix_map = {
                "purchase_order": "PO",
                "sales_order": "SO",
                "transfer_order": "TR",
                "adjustment_order": "ADJ",
                "return_order": "RET",
                "order_document": "ORD",
            }
            prefix = prefix_map.get(self.ordertype, "ORD")
            count = OrderDocument.objects.filter(
                ordertype=self.ordertype, branch=self.branch
            ).count() + 1
            date_str = timezone.now().strftime("%Y%m%d")
            self.title = f"{prefix}_{date_str}_{count:04d}"
        super().save(*args, **kwargs)


class OrderDocumentAttachment(TenantAwareModel):
    order_document = models.ForeignKey(
        OrderDocument, on_delete=models.CASCADE, related_name="attachments"
    )
    file_url = models.CharField(_("File URL"), max_length=500, blank=True)
    description = models.CharField(max_length=255, blank=True)

    class Meta:
        verbose_name = _("Order Document Attachment")

    def __str__(self):
        return f"{self.order_document} — {self.file_url}"


class OrderDocumentDetail(TenantAwareModel):
    order = models.ForeignKey(OrderDocument, on_delete=models.CASCADE, related_name="lines")
    item = models.ForeignKey("inventory.Product", on_delete=models.PROTECT, related_name="order_lines")
    uom = models.ForeignKey("inventory.UnitOfMeasure", on_delete=models.PROTECT)
    unit_cost_price = MoneyField(
        max_digits=20, decimal_places=2, default=0,
        default_currency=DEFAULT_CURRENCY, currency_choices=CURRENCY_CHOICES
    )
    qty = models.PositiveIntegerField(_("Quantity"), default=1)
    qty_base = models.PositiveIntegerField(_("Qty (Base Units)"), editable=False, default=0)
    line_total = MoneyField(
        max_digits=20, decimal_places=2, default=0,
        default_currency=DEFAULT_CURRENCY, currency_choices=CURRENCY_CHOICES,
        editable=False
    )

    class Meta:
        verbose_name = _("Order Line")

    def save(self, *args, **kwargs):
        self.qty_base = self.qty * self.uom.conversion_rate
        self.line_total = self.unit_cost_price * self.qty
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.order} — {self.item} × {self.qty}"


# ─────────────────────────────────────────────────────────────────────────────
# Transfer Inventory Document
# ─────────────────────────────────────────────────────────────────────────────

class TransferInventoryDocument(TenantAwareModel):
    STATUS_CHOICES = [
        ("pending", _("Pending")),
        ("transit", _("In Transit")),
        ("accepted", _("Accepted")),
        ("partial_accept", _("Partially Accepted")),
        ("rejected", _("Rejected")),
        ("cancel", _("Cancelled")),
    ]

    transfer_number = models.CharField(_("Transfer No."), max_length=50, unique=True)
    line_number = models.PositiveIntegerField(default=1)
    strict = models.BooleanField(
        _("Strict Transfer"), default=True,
        help_text=_("If True, in-qty must exactly match out-qty.")
    )
    order_document = models.ManyToManyField(OrderDocument, blank=True, related_name="transfers")
    in_branch = models.ForeignKey(
        "department.Branch", on_delete=models.PROTECT, related_name="transfers_in"
    )
    out_branch = models.ForeignKey(
        "department.Branch", on_delete=models.PROTECT, related_name="transfers_out"
    )
    return_inventory_document = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.SET_NULL, related_name="return_docs"
    )
    is_return = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    in_staff = models.ForeignKey(
        "party.CustomUser", on_delete=models.PROTECT,
        null=True, blank=True, related_name="transfer_receipts"
    )
    out_staff = models.ForeignKey(
        "party.CustomUser", on_delete=models.PROTECT,
        null=True, blank=True, related_name="transfer_dispatches"
    )
    delivery_staff = models.ForeignKey(
        "party.CustomUser", on_delete=models.PROTECT,
        null=True, blank=True, related_name="transfer_deliveries"
    )
    outcartoncount = models.PositiveIntegerField(_("Out Carton Count"), default=0)
    incartoncount = models.PositiveIntegerField(_("In Carton Count"), default=0)
    transfer_in_stockvaluation = MoneyField(
        max_digits=20, decimal_places=2, default=0,
        default_currency=DEFAULT_CURRENCY, currency_choices=CURRENCY_CHOICES
    )
    transfer_out_stockvaluation = MoneyField(
        max_digits=20, decimal_places=2, default=0,
        default_currency=DEFAULT_CURRENCY, currency_choices=CURRENCY_CHOICES
    )

    class Meta:
        verbose_name = _("Transfer Inventory Document")
        unique_together = ("transfer_number", "in_branch", "out_branch")

    def save(self, *args, **kwargs):
        if not self.transfer_number:
            ts = timezone.now().strftime("%Y%m%d_%H%M%S")
            count = TransferInventoryDocument.objects.count() + 1
            self.transfer_number = f"TR_{ts}_{count:04d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.transfer_number
