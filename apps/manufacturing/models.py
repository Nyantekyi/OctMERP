"""
apps/manufacturing/models.py

Manufacturing / Production management for the ERP.

Covers:
  - Bill of Materials (BOM) + components
  - Work Centers and Routings
  - Production / Work Orders
  - Quality control checks
  - Scrap records
"""

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from djmoney.models.fields import MoneyField

from apps.common.models import TenantAwareModel, DEFAULT_CURRENCY, CURRENCY_CHOICES


# ─────────────────────────────────────────────────────────────────────────────
# Bill of Materials (BOM)
# ─────────────────────────────────────────────────────────────────────────────

class BillOfMaterials(TenantAwareModel):
    """
    Recipe for producing/assembling a finished product variant.
    Multiple BOMs can exist for the same product (different methods).
    """
    BOM_TYPE_CHOICES = [
        ("manufacture", _("Manufacture")),
        ("kit", _("Kit / Assembly")),
        ("subcontracting", _("Sub-contracting")),
    ]

    name = models.CharField(_("BOM Name"), max_length=200, blank=True)
    product = models.ForeignKey("inventory.Product", on_delete=models.PROTECT, related_name="boms")
    variant = models.ForeignKey(
        "inventory.ProductVariant", on_delete=models.PROTECT, null=True, blank=True, related_name="boms"
    )
    quantity = models.DecimalField(_("Quantity Produced"), max_digits=14, decimal_places=4, default=1)
    unit = models.ForeignKey("inventory.Unit", on_delete=models.PROTECT, related_name="boms")
    bom_type = models.CharField(_("BOM Type"), max_length=20, choices=BOM_TYPE_CHOICES, default="manufacture")
    branch = models.ForeignKey("department.Branch", on_delete=models.PROTECT, related_name="boms")
    version = models.PositiveSmallIntegerField(_("Version"), default=1)
    is_default = models.BooleanField(_("Default BOM?"), default=False)
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = _("Bill of Materials")
        verbose_name_plural = _("Bills of Materials")
        ordering = ["product", "-version"]

    def __str__(self):
        return f"BOM — {self.variant or self.product} v{self.version}"


class BOMComponent(TenantAwareModel):
    """Single raw material / sub-assembly line within a BOM."""
    bom = models.ForeignKey(BillOfMaterials, on_delete=models.CASCADE, related_name="components")
    component = models.ForeignKey("inventory.ProductVariant", on_delete=models.PROTECT, related_name="bom_usages")
    quantity = models.DecimalField(_("Quantity"), max_digits=14, decimal_places=4)
    unit = models.ForeignKey("inventory.Unit", on_delete=models.PROTECT, related_name="bom_components")
    scrap_percent = models.DecimalField(
        _("Expected Scrap %"), max_digits=5, decimal_places=2, default=0,
        help_text=_("Extra material to account for production waste.")
    )
    is_optional = models.BooleanField(_("Optional Component?"), default=False)
    notes = models.CharField(_("Notes"), max_length=255, blank=True)

    class Meta:
        verbose_name = _("BOM Component")
        verbose_name_plural = _("BOM Components")
        unique_together = ("bom", "component")

    def __str__(self):
        return f"{self.bom} — {self.component} x {self.quantity} {self.unit}"

    @property
    def quantity_with_scrap(self):
        from decimal import Decimal
        return self.quantity * (1 + self.scrap_percent / Decimal("100"))


# ─────────────────────────────────────────────────────────────────────────────
# Work Center
# ─────────────────────────────────────────────────────────────────────────────

class WorkCenter(TenantAwareModel):
    """
    Physical or logical production station (machine, team, station).
    Tracks capacity and cost.
    """
    name = models.CharField(_("Work Center Name"), max_length=100)
    branch = models.ForeignKey("department.Branch", on_delete=models.PROTECT, related_name="work_centers")
    capacity_per_hour = models.DecimalField(
        _("Capacity per Hour"), max_digits=10, decimal_places=4, default=1
    )
    cost_per_hour = MoneyField(
        _("Cost per Hour"), max_digits=20, decimal_places=2,
        default=0, default_currency=DEFAULT_CURRENCY, currency_choices=CURRENCY_CHOICES
    )
    default_operator = models.ForeignKey(
        "party.StaffProfile", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="operated_work_centers"
    )
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = _("Work Center")
        verbose_name_plural = _("Work Centers")
        unique_together = ("branch", "name")
        ordering = ["branch", "name"]

    def __str__(self):
        return f"{self.name} @ {self.branch}"


# ─────────────────────────────────────────────────────────────────────────────
# Routing
# ─────────────────────────────────────────────────────────────────────────────

class Routing(TenantAwareModel):
    """Ordered set of operations (steps) used in producing a BOM."""
    name = models.CharField(_("Routing Name"), max_length=100)
    bom = models.ForeignKey(
        BillOfMaterials, on_delete=models.CASCADE, related_name="routings"
    )

    class Meta:
        verbose_name = _("Routing")
        verbose_name_plural = _("Routings")

    def __str__(self):
        return f"{self.name} for {self.bom}"


class RoutingStep(TenantAwareModel):
    """One operation in a Routing."""
    routing = models.ForeignKey(Routing, on_delete=models.CASCADE, related_name="steps")
    name = models.CharField(_("Operation Name"), max_length=100)
    work_center = models.ForeignKey(WorkCenter, on_delete=models.PROTECT, related_name="routing_steps")
    sequence = models.PositiveSmallIntegerField(_("Sequence"), default=10)
    duration_minutes = models.DecimalField(_("Duration (mins)"), max_digits=8, decimal_places=2, default=0)
    instructions = models.TextField(_("Work Instructions"), blank=True)

    class Meta:
        verbose_name = _("Routing Step")
        verbose_name_plural = _("Routing Steps")
        ordering = ["routing", "sequence"]

    def __str__(self):
        return f"{self.routing} — Step {self.sequence}: {self.name}"


# ─────────────────────────────────────────────────────────────────────────────
# Production / Work Order
# ─────────────────────────────────────────────────────────────────────────────

class WorkOrder(TenantAwareModel):
    """
    A manufacturing/production job order.  Creates StockMoves on completion.
    """
    STATUS_CHOICES = [
        ("draft", _("Draft")),
        ("confirmed", _("Confirmed")),
        ("in_progress", _("In Progress")),
        ("done", _("Done")),
        ("cancelled", _("Cancelled")),
    ]

    reference = models.CharField(_("Work Order Ref"), max_length=50, unique=True)
    bom = models.ForeignKey(BillOfMaterials, on_delete=models.PROTECT, related_name="work_orders")
    routing = models.ForeignKey(
        Routing, on_delete=models.SET_NULL, null=True, blank=True, related_name="work_orders"
    )
    quantity_planned = models.DecimalField(_("Planned Quantity"), max_digits=14, decimal_places=4)
    quantity_produced = models.DecimalField(_("Quantity Produced"), max_digits=14, decimal_places=4, default=0)
    unit = models.ForeignKey("inventory.Unit", on_delete=models.PROTECT, related_name="work_orders")
    branch = models.ForeignKey("department.Branch", on_delete=models.PROTECT, related_name="work_orders")
    scheduled_start = models.DateTimeField(_("Scheduled Start"), null=True, blank=True)
    scheduled_end = models.DateTimeField(_("Scheduled End"), null=True, blank=True)
    actual_start = models.DateTimeField(_("Actual Start"), null=True, blank=True)
    actual_end = models.DateTimeField(_("Actual End"), null=True, blank=True)
    status = models.CharField(_("Status"), max_length=20, choices=STATUS_CHOICES, default="draft")
    responsible = models.ForeignKey(
        "party.StaffProfile", on_delete=models.SET_NULL, null=True, blank=True, related_name="work_orders"
    )
    # Originating Sales Order (make-to-order)
    sales_order = models.ForeignKey(
        "sales.SalesOrder", on_delete=models.SET_NULL, null=True, blank=True, related_name="work_orders"
    )
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = _("Work Order")
        verbose_name_plural = _("Work Orders")
        ordering = ["-scheduled_start"]

    def __str__(self):
        return f"WO-{self.reference}"

    def clean(self):
        if self.scheduled_end and self.scheduled_start and self.scheduled_end < self.scheduled_start:
            raise ValidationError(_("Scheduled end must be after scheduled start."))


class WorkOrderLine(TenantAwareModel):
    """Component consumption record for a Work Order."""
    work_order = models.ForeignKey(WorkOrder, on_delete=models.CASCADE, related_name="lines")
    bom_component = models.ForeignKey(
        BOMComponent, on_delete=models.PROTECT, related_name="work_order_lines"
    )
    quantity_required = models.DecimalField(_("Qty Required"), max_digits=14, decimal_places=4)
    quantity_consumed = models.DecimalField(_("Qty Consumed"), max_digits=14, decimal_places=4, default=0)
    lot = models.ForeignKey(
        "inventory.ItemLot", on_delete=models.SET_NULL, null=True, blank=True, related_name="work_order_lines"
    )

    class Meta:
        verbose_name = _("Work Order Line")
        verbose_name_plural = _("Work Order Lines")

    def __str__(self):
        return f"{self.work_order} — {self.bom_component.component}"


# ─────────────────────────────────────────────────────────────────────────────
# Quality Check
# ─────────────────────────────────────────────────────────────────────────────

class QualityCheck(TenantAwareModel):
    RESULT_CHOICES = [
        ("pass", _("Pass")),
        ("fail", _("Fail")),
        ("pending", _("Pending")),
    ]

    work_order = models.ForeignKey(WorkOrder, on_delete=models.CASCADE, related_name="quality_checks")
    check_name = models.CharField(_("Check Name"), max_length=100)
    description = models.TextField(blank=True)
    result = models.CharField(_("Result"), max_length=10, choices=RESULT_CHOICES, default="pending")
    checked_by = models.ForeignKey(
        "party.StaffProfile", on_delete=models.SET_NULL, null=True, blank=True, related_name="quality_checks"
    )
    checked_at = models.DateTimeField(_("Checked At"), null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = _("Quality Check")
        verbose_name_plural = _("Quality Checks")
        ordering = ["work_order", "check_name"]

    def __str__(self):
        return f"{self.work_order} — {self.check_name}: {self.result}"


# ─────────────────────────────────────────────────────────────────────────────
# Scrap
# ─────────────────────────────────────────────────────────────────────────────

class ScrapRecord(TenantAwareModel):
    """Records materials written off as scrap during or after production."""
    REASON_CHOICES = [
        ("defective", _("Defective Material")),
        ("quality_fail", _("Quality Check Failure")),
        ("expired", _("Expired")),
        ("damaged", _("Damaged")),
        ("other", _("Other")),
    ]

    variant = models.ForeignKey("inventory.ProductVariant", on_delete=models.PROTECT, related_name="scrap_records")
    lot = models.ForeignKey(
        "inventory.ItemLot", on_delete=models.SET_NULL, null=True, blank=True, related_name="scrap_records"
    )
    work_order = models.ForeignKey(
        WorkOrder, on_delete=models.SET_NULL, null=True, blank=True, related_name="scrap_records"
    )
    branch = models.ForeignKey("department.Branch", on_delete=models.PROTECT, related_name="scrap_records")
    quantity = models.DecimalField(_("Quantity Scrapped"), max_digits=14, decimal_places=4)
    unit = models.ForeignKey("inventory.Unit", on_delete=models.PROTECT, related_name="scrap_records")
    scrap_date = models.DateField(_("Scrap Date"), default=timezone.now)
    reason = models.CharField(_("Reason"), max_length=20, choices=REASON_CHOICES, default="other")
    detail = models.TextField(blank=True)
    scrapped_by = models.ForeignKey(
        "party.StaffProfile", on_delete=models.PROTECT, related_name="scrap_records"
    )
    transaction_doc = models.ForeignKey(
        "accounting.TransactionDoc", on_delete=models.SET_NULL, null=True, blank=True, related_name="scrap_records"
    )

    class Meta:
        verbose_name = _("Scrap Record")
        verbose_name_plural = _("Scrap Records")
        ordering = ["-scrap_date"]

    def __str__(self):
        return f"Scrap {self.quantity} × {self.variant} on {self.scrap_date}"
