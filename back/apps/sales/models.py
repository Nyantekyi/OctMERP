from decimal import Decimal

from django.apps import apps
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from djmoney.models.fields import MoneyField
from djmoney.money import Money

from apps.common.models import CompanyMixin, activearchlockedMixin, createdtimestamp_uid


default_currency = "GHS"


class PriceList(createdtimestamp_uid, activearchlockedMixin, CompanyMixin):
    name = models.CharField(max_length=150)
    is_default = models.BooleanField(default=False)
    valid_from = models.DateField(null=True, blank=True)
    valid_to = models.DateField(null=True, blank=True)

    class Meta:
        unique_together = (("company", "name"),)

    def __str__(self):
        return self.name


class Tender_Repository(createdtimestamp_uid, activearchlockedMixin, CompanyMixin):
    """Payment/tender methods inspired by the reference models naming convention."""

    name = models.CharField(max_length=100)
    code = models.CharField(max_length=40)
    is_default = models.BooleanField(default=False)
    supported_channels = ArrayField(models.CharField(max_length=40), blank=True, default=list)

    class Meta:
        unique_together = (("company", "code"),)

    def __str__(self):
        return self.name


class Quotation(createdtimestamp_uid, activearchlockedMixin, CompanyMixin):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        SENT = "sent", "Sent"
        ACCEPTED = "accepted", "Accepted"
        REJECTED = "rejected", "Rejected"

    quote_number = models.CharField(max_length=60)
    client = models.ForeignKey("party.Client", null=True, blank=True, on_delete=models.SET_NULL, related_name="quotations")
    prospect = models.ForeignKey("crm.Prospect", null=True, blank=True, on_delete=models.SET_NULL, related_name="quotations")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    valid_until = models.DateField(null=True, blank=True)
    subtotal = MoneyField(max_digits=14, decimal_places=2, default=0, default_currency=default_currency)
    tax = MoneyField(max_digits=14, decimal_places=2, default=0, default_currency=default_currency)
    total = MoneyField(max_digits=14, decimal_places=2, default=0, default_currency=default_currency)
    assigned_to = models.ForeignKey("party.Staff", null=True, blank=True, on_delete=models.SET_NULL, related_name="managed_quotations")
    tags = ArrayField(models.CharField(max_length=40), blank=True, default=list)

    class Meta:
        unique_together = (("company", "quote_number"),)

    def __str__(self):
        return self.quote_number

    def recalculate_totals(self):
        lines = self.lines.all()
        if not lines.exists():
            zero = Money(0, default_currency)
            self.subtotal = zero
            self.tax = zero
            self.total = zero
            self.save(update_fields=["subtotal", "tax", "total", "updated_at"])
            return

        subtotal = sum((line.line_total.amount for line in lines), Decimal("0.00"))
        tax = Money(0, default_currency)
        self.subtotal = Money(subtotal, default_currency)
        self.tax = tax
        self.total = self.subtotal + self.tax
        self.save(update_fields=["subtotal", "tax", "total", "updated_at"])


class QuotationLine(createdtimestamp_uid):
    quotation = models.ForeignKey(Quotation, on_delete=models.CASCADE, related_name="lines")
    product = models.ForeignKey("inventory.Product", on_delete=models.PROTECT, related_name="quotation_lines")
    variant = models.ForeignKey("inventory.ProductVariant", null=True, blank=True, on_delete=models.SET_NULL, related_name="quotation_lines")
    quantity = models.DecimalField(max_digits=14, decimal_places=3)
    unit_price = MoneyField(max_digits=14, decimal_places=2, default=0, default_currency=default_currency)
    discount = MoneyField(max_digits=14, decimal_places=2, default=0, default_currency=default_currency)
    line_total = MoneyField(max_digits=14, decimal_places=2, default=0, default_currency=default_currency)

    def save(self, *args, **kwargs):
        unit_amount = self.unit_price.amount if self.unit_price else Decimal("0.00")
        discount_amount = self.discount.amount if self.discount else Decimal("0.00")
        line_amount = (self.quantity or Decimal("0.00")) * unit_amount - discount_amount
        self.line_total = Money(max(line_amount, Decimal("0.00")), default_currency)
        super().save(*args, **kwargs)


class SalesOrder(createdtimestamp_uid, activearchlockedMixin, CompanyMixin):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        CONFIRMED = "confirmed", "Confirmed"
        DELIVERED = "delivered", "Delivered"
        CANCELLED = "cancelled", "Cancelled"

    order_number = models.CharField(max_length=60)
    quotation = models.ForeignKey(Quotation, null=True, blank=True, on_delete=models.SET_NULL, related_name="sales_orders")
    client = models.ForeignKey("party.Client", null=True, blank=True, on_delete=models.SET_NULL, related_name="sales_orders")
    branch = models.ForeignKey("department.Branch", null=True, blank=True, on_delete=models.SET_NULL, related_name="sales_orders")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    ordered_on = models.DateField(auto_now_add=True)
    subtotal = MoneyField(max_digits=14, decimal_places=2, default=0, default_currency=default_currency)
    tax = MoneyField(max_digits=14, decimal_places=2, default=0, default_currency=default_currency)
    total = MoneyField(max_digits=14, decimal_places=2, default=0, default_currency=default_currency)
    sales_rep = models.ForeignKey("party.Staff", null=True, blank=True, on_delete=models.SET_NULL, related_name="sales_orders")
    payment_terms = models.CharField(max_length=120, blank=True)
    tender_method = models.ForeignKey(
        Tender_Repository,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="sales_orders",
    )
    payment_channels = ArrayField(models.CharField(max_length=40), blank=True, default=list)
    tags = ArrayField(models.CharField(max_length=40), blank=True, default=list)

    class Meta:
        unique_together = (("company", "order_number"),)

    def __str__(self):
        return self.order_number

    def recalculate_totals(self):
        lines = self.lines.all()
        if not lines.exists():
            zero = Money(0, default_currency)
            self.subtotal = zero
            self.tax = zero
            self.total = zero
            self.save(update_fields=["subtotal", "tax", "total", "updated_at"])
            return

        subtotal = sum((line.line_total.amount for line in lines), Decimal("0.00"))
        tax = Money(0, default_currency)
        self.subtotal = Money(subtotal, default_currency)
        self.tax = tax
        self.total = self.subtotal + self.tax
        self.save(update_fields=["subtotal", "tax", "total", "updated_at"])


class SalesOrderLine(createdtimestamp_uid):
    order = models.ForeignKey(SalesOrder, on_delete=models.CASCADE, related_name="lines")
    product = models.ForeignKey("inventory.Product", on_delete=models.PROTECT, related_name="sales_lines")
    variant = models.ForeignKey("inventory.ProductVariant", null=True, blank=True, on_delete=models.SET_NULL, related_name="sales_lines")
    quantity = models.DecimalField(max_digits=14, decimal_places=3)
    unit_price = MoneyField(max_digits=14, decimal_places=2, default=0, default_currency=default_currency)
    discount = MoneyField(max_digits=14, decimal_places=2, default=0, default_currency=default_currency)
    line_total = MoneyField(max_digits=14, decimal_places=2, default=0, default_currency=default_currency)

    def save(self, *args, **kwargs):
        unit_amount = self.unit_price.amount if self.unit_price else Decimal("0.00")
        discount_amount = self.discount.amount if self.discount else Decimal("0.00")
        line_amount = (self.quantity or Decimal("0.00")) * unit_amount - discount_amount
        self.line_total = Money(max(line_amount, Decimal("0.00")), default_currency)
        super().save(*args, **kwargs)


class Delivery(createdtimestamp_uid, activearchlockedMixin):
    class DeliveryStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        IN_TRANSIT = "in_transit", "In transit"
        DELIVERED = "delivered", "Delivered"
        FAILED = "failed", "Failed"

    sales_order = models.ForeignKey(SalesOrder, on_delete=models.CASCADE, related_name="deliveries")
    delivery_number = models.CharField(max_length=80)
    shipped_on = models.DateField(null=True, blank=True)
    delivered_on = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=DeliveryStatus.choices, default=DeliveryStatus.PENDING)
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = (("sales_order", "delivery_number"),)

    def __str__(self):
        return self.delivery_number


class SalesReturn(createdtimestamp_uid, activearchlockedMixin):
    class ReturnStatus(models.TextChoices):
        REQUESTED = "requested", "Requested"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        RECEIVED = "received", "Received"

    sales_order = models.ForeignKey(SalesOrder, on_delete=models.CASCADE, related_name="returns")
    client = models.ForeignKey("party.Client", null=True, blank=True, on_delete=models.SET_NULL, related_name="sales_returns")
    status = models.CharField(max_length=20, choices=ReturnStatus.choices, default=ReturnStatus.REQUESTED)
    reason = models.TextField(blank=True)
    return_amount = MoneyField(max_digits=14, decimal_places=2, default=0, default_currency=default_currency)
    items_summary = ArrayField(models.CharField(max_length=120), blank=True, default=list)


@receiver(post_save, sender=QuotationLine)
def update_quotation_totals_on_line_save(sender, instance, **kwargs):
    instance.quotation.recalculate_totals()


@receiver(post_delete, sender=QuotationLine)
def update_quotation_totals_on_line_delete(sender, instance, **kwargs):
    instance.quotation.recalculate_totals()


@receiver(post_save, sender=SalesOrderLine)
def update_sales_order_totals_on_line_save(sender, instance, **kwargs):
    instance.order.recalculate_totals()


@receiver(post_delete, sender=SalesOrderLine)
def update_sales_order_totals_on_line_delete(sender, instance, **kwargs):
    instance.order.recalculate_totals()


@receiver(post_save, sender=Delivery)
def create_stock_moves_for_delivery(sender, instance, created, **kwargs):
    """Create OUT stock moves when a delivery is marked delivered."""
    if instance.status != Delivery.DeliveryStatus.DELIVERED:
        return

    warehouse_model = apps.get_model("inventory", "Warehouse")
    stock_move_model = apps.get_model("inventory", "StockMove")
    warehouse = warehouse_model.objects.filter(branch=instance.sales_order.branch).first()
    if warehouse is None:
        return

    for line in instance.sales_order.lines.select_related("product", "variant"):
        stock_move_model.objects.get_or_create(
            product=line.product,
            variant=line.variant,
            warehouse=warehouse,
            move_type="out",
            reference=f"DEL-{instance.delivery_number}",
            defaults={
                "quantity": line.quantity,
                "notes": f"Auto move from delivery {instance.delivery_number}",
            },
        )


@receiver(post_save, sender=SalesReturn)
def create_stock_moves_for_return(sender, instance, created, **kwargs):
    """Create RETURN stock moves when return is received."""
    if instance.status != SalesReturn.ReturnStatus.RECEIVED:
        return

    stock_move_model = apps.get_model("inventory", "StockMove")
    warehouse_model = apps.get_model("inventory", "Warehouse")
    warehouse = warehouse_model.objects.filter(branch=instance.sales_order.branch).first()
    if warehouse is None:
        return

    for line in instance.sales_order.lines.select_related("product", "variant"):
        stock_move_model.objects.get_or_create(
            product=line.product,
            variant=line.variant,
            warehouse=warehouse,
            move_type="return",
            reference=f"RET-{instance.pk}",
            defaults={
                "quantity": line.quantity,
                "notes": f"Auto move from sales return {instance.pk}",
            },
        )
