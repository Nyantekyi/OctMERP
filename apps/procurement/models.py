"""
apps/procurement/models.py

Purchase & Procurement management for the ERP.

Covers:
  - Purchase Requisitions (internal demand)
  - Request for Quotation (RFQ) sent to suppliers
  - Purchase Orders (PO) with approval workflow
  - Goods Receipt Notes (GRN) 
  - Vendor contracts & framework agreements
  - Supplier evaluation
"""

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from djmoney.models.fields import MoneyField

from apps.common.models import TenantAwareModel, DEFAULT_CURRENCY, CURRENCY_CHOICES


# ─────────────────────────────────────────────────────────────────────────────
# Purchase Requisition
# ─────────────────────────────────────────────────────────────────────────────

class PurchaseRequisition(TenantAwareModel):
    STATUS_CHOICES = [
        ("draft", _("Draft")),
        ("submitted", _("Submitted")),
        ("approved", _("Approved")),
        ("rejected", _("Rejected")),
        ("rfq_sent", _("RFQ Sent")),
        ("po_created", _("PO Created")),
        ("cancelled", _("Cancelled")),
    ]

    reference = models.CharField(_("Reference"), max_length=50, unique=True)
    branch = models.ForeignKey(
        "department.Branch", on_delete=models.PROTECT, related_name="purchase_requisitions"
    )
    department = models.ForeignKey(
        "department.Department", on_delete=models.PROTECT, related_name="purchase_requisitions"
    )
    requested_by = models.ForeignKey(
        "party.StaffProfile", on_delete=models.PROTECT, related_name="purchase_requisitions_made"
    )
    request_date = models.DateField(_("Request Date"), default=timezone.now)
    required_by_date = models.DateField(_("Required By"), null=True, blank=True)
    status = models.CharField(_("Status"), max_length=20, choices=STATUS_CHOICES, default="draft")
    approved_by = models.ForeignKey(
        "party.StaffProfile", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="approved_requisitions"
    )
    approval_date = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    budget_request = models.ForeignKey(
        "accounting.BudgetRequest", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="procurement_requisitions"
    )

    class Meta:
        verbose_name = _("Purchase Requisition")
        verbose_name_plural = _("Purchase Requisitions")
        ordering = ["-request_date"]

    def __str__(self):
        return f"PR-{self.reference}"

    def save(self, *args, **kwargs):
        if self.status == "approved" and not self.approval_date:
            self.approval_date = timezone.now()
        super().save(*args, **kwargs)


class PurchaseRequisitionLine(TenantAwareModel):
    requisition = models.ForeignKey(PurchaseRequisition, on_delete=models.CASCADE, related_name="lines")
    product = models.ForeignKey(
        "inventory.Product", on_delete=models.PROTECT, related_name="requisition_lines"
    )
    variant = models.ForeignKey(
        "inventory.ProductVariant", on_delete=models.PROTECT, null=True, blank=True, related_name="requisition_lines"
    )
    quantity = models.DecimalField(_("Quantity"), max_digits=14, decimal_places=4)
    unit = models.ForeignKey("inventory.Unit", on_delete=models.PROTECT, related_name="requisition_lines")
    estimated_unit_price = MoneyField(
        _("Estimated Unit Price"), max_digits=20, decimal_places=2,
        null=True, blank=True, default_currency=DEFAULT_CURRENCY, currency_choices=CURRENCY_CHOICES
    )
    preferred_supplier = models.ForeignKey(
        "party.SupplierProfile", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="requisition_lines"
    )
    description = models.CharField(_("Description"), max_length=255, blank=True)

    class Meta:
        verbose_name = _("Requisition Line")
        verbose_name_plural = _("Requisition Lines")

    def __str__(self):
        return f"{self.requisition} — {self.product.name} x {self.quantity}"


# ─────────────────────────────────────────────────────────────────────────────
# Request For Quotation (RFQ)
# ─────────────────────────────────────────────────────────────────────────────

class RFQ(TenantAwareModel):
    """
    Supplier-facing request for pricing.
    One RFQ is typically created per supplier from a single requisition.
    """
    STATUS_CHOICES = [
        ("draft", _("Draft")),
        ("sent", _("Sent to Supplier")),
        ("received", _("Quotation Received")),
        ("rejected", _("Rejected")),
        ("po_created", _("PO Created")),
        ("cancelled", _("Cancelled")),
    ]

    reference = models.CharField(_("RFQ Reference"), max_length=50, unique=True)
    requisition = models.ForeignKey(
        PurchaseRequisition, on_delete=models.SET_NULL, null=True, blank=True, related_name="rfqs"
    )
    supplier = models.ForeignKey("party.SupplierProfile", on_delete=models.PROTECT, related_name="rfqs")
    branch = models.ForeignKey("department.Branch", on_delete=models.PROTECT, related_name="rfqs")
    issued_date = models.DateField(_("Issued Date"), default=timezone.now)
    response_deadline = models.DateField(_("Response Deadline"), null=True, blank=True)
    status = models.CharField(_("Status"), max_length=20, choices=STATUS_CHOICES, default="draft")
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = _("RFQ")
        verbose_name_plural = _("RFQs")
        ordering = ["-issued_date"]

    def __str__(self):
        return f"RFQ-{self.reference} to {self.supplier}"


class RFQLine(TenantAwareModel):
    rfq = models.ForeignKey(RFQ, on_delete=models.CASCADE, related_name="lines")
    product = models.ForeignKey("inventory.Product", on_delete=models.PROTECT, related_name="rfq_lines")
    variant = models.ForeignKey(
        "inventory.ProductVariant", on_delete=models.PROTECT, null=True, blank=True, related_name="rfq_lines"
    )
    quantity = models.DecimalField(_("Quantity"), max_digits=14, decimal_places=4)
    unit = models.ForeignKey("inventory.Unit", on_delete=models.PROTECT, related_name="rfq_lines")
    quoted_unit_price = MoneyField(
        _("Quoted Unit Price"), max_digits=20, decimal_places=2,
        null=True, blank=True, default_currency=DEFAULT_CURRENCY, currency_choices=CURRENCY_CHOICES
    )
    lead_time_days = models.PositiveSmallIntegerField(_("Lead Time (days)"), default=0)
    remarks = models.CharField(_("Remarks"), max_length=255, blank=True)

    class Meta:
        verbose_name = _("RFQ Line")
        verbose_name_plural = _("RFQ Lines")

    def __str__(self):
        return f"{self.rfq} — {self.product.name} x {self.quantity}"


# ─────────────────────────────────────────────────────────────────────────────
# Purchase Order
# ─────────────────────────────────────────────────────────────────────────────

class PurchaseOrder(TenantAwareModel):
    STATUS_CHOICES = [
        ("draft", _("Draft")),
        ("submitted", _("Submitted for Approval")),
        ("approved", _("Approved")),
        ("sent", _("Sent to Supplier")),
        ("partial", _("Partially Received")),
        ("received", _("Fully Received")),
        ("closed", _("Closed")),
        ("cancelled", _("Cancelled")),
    ]

    reference = models.CharField(_("PO Number"), max_length=50, unique=True)
    rfq = models.ForeignKey(
        RFQ, on_delete=models.SET_NULL, null=True, blank=True, related_name="purchase_orders"
    )
    requisition = models.ForeignKey(
        PurchaseRequisition, on_delete=models.SET_NULL, null=True, blank=True, related_name="purchase_orders"
    )
    supplier = models.ForeignKey("party.SupplierProfile", on_delete=models.PROTECT, related_name="purchase_orders")
    branch = models.ForeignKey("department.Branch", on_delete=models.PROTECT, related_name="purchase_orders")
    order_date = models.DateField(_("Order Date"), default=timezone.now)
    expected_delivery_date = models.DateField(_("Expected Delivery"), null=True, blank=True)
    status = models.CharField(_("Status"), max_length=20, choices=STATUS_CHOICES, default="draft")
    approved_by = models.ForeignKey(
        "party.StaffProfile", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="approved_purchase_orders"
    )
    terms_and_conditions = models.TextField(blank=True)
    currency = models.CharField(_("Currency"), max_length=3, default=DEFAULT_CURRENCY, choices=CURRENCY_CHOICES)
    subtotal = MoneyField(
        _("Subtotal"), max_digits=20, decimal_places=2,
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
    bill = models.OneToOneField(
        "accounting.Bill", on_delete=models.SET_NULL, null=True, blank=True, related_name="purchase_order"
    )

    class Meta:
        verbose_name = _("Purchase Order")
        verbose_name_plural = _("Purchase Orders")
        ordering = ["-order_date"]

    def __str__(self):
        return f"PO-{self.reference}"


class PurchaseOrderLine(TenantAwareModel):
    order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name="lines")
    product = models.ForeignKey("inventory.Product", on_delete=models.PROTECT, related_name="po_lines")
    variant = models.ForeignKey(
        "inventory.ProductVariant", on_delete=models.PROTECT, null=True, blank=True, related_name="po_lines"
    )
    quantity_ordered = models.DecimalField(_("Qty Ordered"), max_digits=14, decimal_places=4)
    quantity_received = models.DecimalField(_("Qty Received"), max_digits=14, decimal_places=4, default=0)
    unit = models.ForeignKey("inventory.Unit", on_delete=models.PROTECT, related_name="po_lines")
    unit_price = MoneyField(
        _("Unit Price"), max_digits=20, decimal_places=2,
        default=0, default_currency=DEFAULT_CURRENCY, currency_choices=CURRENCY_CHOICES
    )
    tax = models.ForeignKey(
        "accounting.Tax", on_delete=models.SET_NULL, null=True, blank=True, related_name="po_lines"
    )
    line_total = MoneyField(
        _("Line Total"), max_digits=20, decimal_places=2,
        default=0, default_currency=DEFAULT_CURRENCY, currency_choices=CURRENCY_CHOICES, editable=False
    )
    shelf = models.ForeignKey(
        "department.Shelfing", on_delete=models.SET_NULL, null=True, blank=True, related_name="po_lines"
    )

    class Meta:
        verbose_name = _("PO Line")
        verbose_name_plural = _("PO Lines")

    def save(self, *args, **kwargs):
        self.line_total = self.unit_price * self.quantity_ordered
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.order} — {self.product.name} x {self.quantity_ordered}"

    @property
    def quantity_pending(self):
        return max(0, self.quantity_ordered - self.quantity_received)


# ─────────────────────────────────────────────────────────────────────────────
# Goods Receipt Note (GRN)
# ─────────────────────────────────────────────────────────────────────────────

class GoodsReceiptNote(TenantAwareModel):
    """
    Records the physical receipt of goods against a Purchase Order.
    Creates StockMove entries on validation.
    """
    STATUS_CHOICES = [
        ("draft", _("Draft")),
        ("validated", _("Validated")),
        ("cancelled", _("Cancelled")),
    ]

    reference = models.CharField(_("GRN Reference"), max_length=50, unique=True)
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.PROTECT, related_name="grns")
    received_by = models.ForeignKey(
        "party.StaffProfile", on_delete=models.PROTECT, related_name="grns_received"
    )
    received_date = models.DateField(_("Received Date"), default=timezone.now)
    supplier_delivery_note = models.CharField(_("Supplier Delivery Note No."), max_length=100, blank=True)
    status = models.CharField(_("Status"), max_length=20, choices=STATUS_CHOICES, default="draft")
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = _("Goods Receipt Note")
        verbose_name_plural = _("Goods Receipt Notes")
        ordering = ["-received_date"]

    def __str__(self):
        return f"GRN-{self.reference}"


class GRNLine(TenantAwareModel):
    grn = models.ForeignKey(GoodsReceiptNote, on_delete=models.CASCADE, related_name="lines")
    po_line = models.ForeignKey(PurchaseOrderLine, on_delete=models.PROTECT, related_name="grn_lines")
    quantity_received = models.DecimalField(_("Qty Received"), max_digits=14, decimal_places=4)
    quantity_rejected = models.DecimalField(_("Qty Rejected"), max_digits=14, decimal_places=4, default=0)
    lot = models.ForeignKey(
        "inventory.ItemLot", on_delete=models.SET_NULL, null=True, blank=True, related_name="grn_lines"
    )
    shelf = models.ForeignKey(
        "department.Shelfing", on_delete=models.SET_NULL, null=True, blank=True, related_name="grn_lines"
    )
    remarks = models.CharField(_("Remarks"), max_length=255, blank=True)

    class Meta:
        verbose_name = _("GRN Line")
        verbose_name_plural = _("GRN Lines")

    def __str__(self):
        return f"{self.grn} — {self.po_line.product.name} x {self.quantity_received}"


# ─────────────────────────────────────────────────────────────────────────────
# Vendor Contract
# ─────────────────────────────────────────────────────────────────────────────

class VendorContract(TenantAwareModel):
    """Framework agreement or long-term contract with a supplier."""
    STATUS_CHOICES = [
        ("draft", _("Draft")),
        ("active", _("Active")),
        ("expired", _("Expired")),
        ("terminated", _("Terminated")),
    ]

    reference = models.CharField(_("Contract Reference"), max_length=100, unique=True)
    supplier = models.ForeignKey("party.SupplierProfile", on_delete=models.PROTECT, related_name="vendor_contracts")
    department = models.ForeignKey(
        "department.Department", on_delete=models.PROTECT, related_name="vendor_contracts"
    )
    start_date = models.DateField(_("Start Date"))
    end_date = models.DateField(_("End Date"), null=True, blank=True)
    value = MoneyField(
        _("Contract Value"), max_digits=20, decimal_places=2,
        null=True, blank=True, default_currency=DEFAULT_CURRENCY, currency_choices=CURRENCY_CHOICES
    )
    status = models.CharField(_("Status"), max_length=20, choices=STATUS_CHOICES, default="draft")
    terms = models.TextField(_("Terms and Conditions"), blank=True)
    payment_terms_days = models.PositiveSmallIntegerField(_("Payment Terms (days)"), default=30)
    document = models.FileField(_("Contract Document"), upload_to="vendor_contracts/%Y/", null=True, blank=True)

    class Meta:
        verbose_name = _("Vendor Contract")
        verbose_name_plural = _("Vendor Contracts")
        ordering = ["-start_date"]

    def __str__(self):
        return f"Contract {self.reference} — {self.supplier}"

    def clean(self):
        if self.end_date and self.end_date < self.start_date:
            raise ValidationError(_("End date must be after start date."))


class SupplierEvaluation(TenantAwareModel):
    """Periodic quality/performance score for a supplier."""
    supplier = models.ForeignKey("party.SupplierProfile", on_delete=models.CASCADE, related_name="evaluations")
    evaluated_by = models.ForeignKey(
        "party.StaffProfile", on_delete=models.PROTECT, related_name="supplier_evaluations"
    )
    evaluation_date = models.DateField(_("Evaluation Date"), default=timezone.now)
    quality_score = models.PositiveSmallIntegerField(
        _("Quality Score (1–5)"), choices=[(i, str(i)) for i in range(1, 6)]
    )
    delivery_score = models.PositiveSmallIntegerField(
        _("Delivery Score (1–5)"), choices=[(i, str(i)) for i in range(1, 6)]
    )
    price_score = models.PositiveSmallIntegerField(
        _("Price Competitiveness (1–5)"), choices=[(i, str(i)) for i in range(1, 6)]
    )
    communication_score = models.PositiveSmallIntegerField(
        _("Communication (1–5)"), choices=[(i, str(i)) for i in range(1, 6)]
    )
    comments = models.TextField(blank=True)

    class Meta:
        verbose_name = _("Supplier Evaluation")
        verbose_name_plural = _("Supplier Evaluations")
        ordering = ["-evaluation_date"]

    def __str__(self):
        return f"Evaluation of {self.supplier} on {self.evaluation_date}"

    @property
    def overall_score(self):
        return (self.quality_score + self.delivery_score + self.price_score + self.communication_score) / 4
