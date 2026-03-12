from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.db.models import Sum
from django.db.models.signals import post_save
from django.dispatch import receiver
from djmoney.models.fields import CurrencyField, MoneyField

from apps.accounts.models import Account, Charts_of_account, Tax, default_currency, allowed_currencies
from apps.common.models import CompanyMixin, activearchlockedMixin, createdtimestamp_uid


# ---------------------------------------------------------------------------
# Catalogue helpers
# ---------------------------------------------------------------------------

class Category(createdtimestamp_uid, activearchlockedMixin, CompanyMixin):
    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=180)
    parent = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.SET_NULL, related_name="children"
    )
    description = models.TextField(blank=True)

    class Meta:
        unique_together = (("company", "slug"),)

    def __str__(self):
        return self.name


class Manufacturer(createdtimestamp_uid, activearchlockedMixin, CompanyMixin):
    name = models.CharField(max_length=200)
    country = models.ForeignKey(
        "contact.Country", null=True, blank=True, on_delete=models.SET_NULL, related_name="manufacturers"
    )
    website = models.URLField(blank=True)

    class Meta:
        unique_together = (("company", "name"),)

    def __str__(self):
        return self.name


class ManufacturerBrand(createdtimestamp_uid, activearchlockedMixin, CompanyMixin):
    manufacturer = models.ForeignKey(Manufacturer, on_delete=models.CASCADE, related_name="brands")
    name = models.CharField(max_length=150)

    class Meta:
        unique_together = (("manufacturer", "name"),)

    def __str__(self):
        return f"{self.manufacturer.name} – {self.name}"


class Brand(createdtimestamp_uid, activearchlockedMixin, CompanyMixin):
    """Generic brand not tied to a manufacturer — kept for backward compatibility."""
    name = models.CharField(max_length=150)
    manufacturer_brand = models.ForeignKey(
        ManufacturerBrand, null=True, blank=True, on_delete=models.SET_NULL, related_name="generic_brands"
    )

    class Meta:
        unique_together = (("company", "name"),)

    def __str__(self):
        return self.name


class UnitOfMeasure(createdtimestamp_uid, activearchlockedMixin, CompanyMixin):
    name = models.CharField(max_length=100)
    abbreviation = models.CharField(max_length=20)

    class Meta:
        unique_together = (("company", "name"),)

    def __str__(self):
        return self.abbreviation


class Form(createdtimestamp_uid, activearchlockedMixin, CompanyMixin):
    """Product form, e.g. Tablet, Capsule, Liquid, Cream."""
    name = models.CharField(max_length=100)

    class Meta:
        unique_together = (("company", "name"),)

    def __str__(self):
        return self.name


class PackSize(createdtimestamp_uid, activearchlockedMixin, CompanyMixin):
    """Pack size descriptor, e.g. 1×10, 1×100, 500 ml."""
    name = models.CharField(max_length=100)
    quantity = models.DecimalField(max_digits=10, decimal_places=3, default=1)
    uom = models.ForeignKey(
        UnitOfMeasure, null=True, blank=True, on_delete=models.SET_NULL, related_name="pack_sizes"
    )

    class Meta:
        unique_together = (("company", "name"),)

    def __str__(self):
        return self.name


# ---------------------------------------------------------------------------
# Product
# ---------------------------------------------------------------------------

class Product(createdtimestamp_uid, activearchlockedMixin, CompanyMixin):
    name = models.CharField(max_length=255)
    sku = models.CharField(max_length=80)
    description = models.TextField(blank=True)
    category = models.ForeignKey(
        Category, null=True, blank=True, on_delete=models.SET_NULL, related_name="products"
    )
    brand = models.ForeignKey(
        Brand, null=True, blank=True, on_delete=models.SET_NULL, related_name="products"
    )
    manufacturer = models.ForeignKey(
        Manufacturer, null=True, blank=True, on_delete=models.SET_NULL, related_name="products"
    )
    uom = models.ForeignKey(
        UnitOfMeasure, null=True, blank=True, on_delete=models.SET_NULL, related_name="products"
    )
    form = models.ForeignKey(
        Form, null=True, blank=True, on_delete=models.SET_NULL, related_name="products"
    )
    pack_size = models.ForeignKey(
        PackSize, null=True, blank=True, on_delete=models.SET_NULL, related_name="products"
    )
    tax = models.ForeignKey(
        Tax, null=True, blank=True, on_delete=models.SET_NULL, related_name="products"
    )
    standard_price = MoneyField(max_digits=14, decimal_places=2, default=0, default_currency=default_currency)
    sale_price = MoneyField(max_digits=14, decimal_places=2, default=0, default_currency=default_currency)
    currency = CurrencyField(default=default_currency)
    is_sellable = models.BooleanField(default=True)
    is_purchasable = models.BooleanField(default=True)
    is_serialised = models.BooleanField(default=False)
    tags = ArrayField(models.CharField(max_length=50), blank=True, default=list)
    # Linked ledger account (created via signal on save)
    account = models.ForeignKey(
        Account, null=True, blank=True, on_delete=models.SET_NULL, related_name="products"
    )

    class Meta:
        unique_together = (("company", "sku"),)

    def __str__(self):
        return self.name


class Barcode(createdtimestamp_uid):
    """One product can have multiple barcodes (EAN-13, UPC, QR, etc.)."""
    class BarcodeType(models.TextChoices):
        EAN13 = "ean13", "EAN-13"
        UPC = "upc", "UPC"
        QR = "qr", "QR Code"
        CODE128 = "code128", "Code 128"
        OTHER = "other", "Other"

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="barcodes")
    value = models.CharField(max_length=120, unique=True)
    barcode_type = models.CharField(max_length=20, choices=BarcodeType.choices, default=BarcodeType.EAN13)

    def __str__(self):
        return self.value


class ProductVariant(createdtimestamp_uid, activearchlockedMixin, CompanyMixin):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="variants")
    code = models.CharField(max_length=80)
    # attributes: e.g. {"colour": "red", "size": "XL"}
    attributes = models.JSONField(default=dict, blank=True)
    extra_price = MoneyField(max_digits=14, decimal_places=2, default=0, default_currency=default_currency)
    tags = ArrayField(models.CharField(max_length=50), blank=True, default=list)

    class Meta:
        unique_together = (("product", "code"),)

    def __str__(self):
        return f"{self.product.name} - {self.code}"


# ---------------------------------------------------------------------------
# Pricing
# ---------------------------------------------------------------------------

class ItemPricingDepartment(createdtimestamp_uid, activearchlockedMixin, CompanyMixin):
    """Overrides the default product price for a specific branch/department."""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="department_prices")
    variant = models.ForeignKey(
        ProductVariant, null=True, blank=True, on_delete=models.SET_NULL, related_name="department_prices"
    )
    branch = models.ForeignKey(
        "department.Branch", null=True, blank=True, on_delete=models.SET_NULL, related_name="item_prices"
    )
    department = models.ForeignKey(
        "department.Department", null=True, blank=True, on_delete=models.SET_NULL, related_name="item_prices"
    )
    selling_price = MoneyField(max_digits=14, decimal_places=2, default=0, default_currency=default_currency)
    markup_percentage = models.DecimalField(max_digits=7, decimal_places=2, default=0)
    allowed_currencies = ArrayField(
        models.CharField(max_length=3),
        blank=True,
        default=list,
    )

    class Meta:
        unique_together = (("product", "variant", "branch", "department"),)
        db_table = "item_pricing_department"
        verbose_name = "item_pricing_department"
        verbose_name_plural = "item_pricing_departments"

    def __str__(self):
        label = self.branch or self.department or "—"
        return f"{self.product.name} @ {label}"


# ---------------------------------------------------------------------------
# Warehouse & Locations
# ---------------------------------------------------------------------------

class Warehouse(createdtimestamp_uid, activearchlockedMixin, CompanyMixin):
    name = models.CharField(max_length=150)
    code = models.CharField(max_length=30)
    branch = models.ForeignKey(
        "department.Branch", null=True, blank=True, on_delete=models.SET_NULL, related_name="warehouses"
    )
    address = models.TextField(blank=True)

    class Meta:
        unique_together = (("company", "code"),)

    def __str__(self):
        return self.name


class WarehouseLocation(createdtimestamp_uid, activearchlockedMixin):
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name="locations")
    code = models.CharField(max_length=50)
    name = models.CharField(max_length=120)

    class Meta:
        unique_together = (("warehouse", "code"),)

    def __str__(self):
        return f"{self.warehouse.code}::{self.code}"


# ---------------------------------------------------------------------------
# Stock / Lot tracking
# ---------------------------------------------------------------------------

class ItemLot(createdtimestamp_uid, activearchlockedMixin):
    """Represents a physical batch/lot of a product received into stock."""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="lots")
    variant = models.ForeignKey(
        ProductVariant, null=True, blank=True, on_delete=models.SET_NULL, related_name="lots"
    )
    lot_number = models.CharField(max_length=120)
    manufacture_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    # Serial numbers for serialised products
    serial_numbers = ArrayField(models.CharField(max_length=100), blank=True, default=list)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.product.sku}::{self.lot_number}"

    class Meta:
        db_table = "item_lot"
        unique_together = (("product", "lot_number"),)


class ItemInventoryLot(createdtimestamp_uid, activearchlockedMixin):
    """Tracks quantity on hand for a specific lot at a warehouse location."""
    lot = models.ForeignKey(ItemLot, on_delete=models.CASCADE, related_name="inventory_entries")
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name="inventory_lots")
    location = models.ForeignKey(
        WarehouseLocation, null=True, blank=True, on_delete=models.SET_NULL, related_name="inventory_lots"
    )
    qty_on_hand = models.DecimalField(max_digits=14, decimal_places=3, default=0)
    qty_reserved = models.DecimalField(max_digits=14, decimal_places=3, default=0)

    class Meta:
        unique_together = (("lot", "warehouse", "location"),)
        db_table = "item_inventory_lot"

    @property
    def qty_available(self):
        return self.qty_on_hand - self.qty_reserved

    def __str__(self):
        return f"{self.lot} @ {self.warehouse.code}"


class StockMove(createdtimestamp_uid):
    class MoveType(models.TextChoices):
        IN = "in", "In"
        OUT = "out", "Out"
        ADJUST = "adjust", "Adjust"
        TRANSFER = "transfer", "Transfer"
        RETURN = "return", "Return"

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="moves")
    variant = models.ForeignKey(
        ProductVariant, null=True, blank=True, on_delete=models.SET_NULL, related_name="moves"
    )
    lot = models.ForeignKey(
        ItemLot, null=True, blank=True, on_delete=models.SET_NULL, related_name="moves"
    )
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name="moves")
    source_location = models.ForeignKey(
        WarehouseLocation, null=True, blank=True, on_delete=models.SET_NULL, related_name="outbound_moves"
    )
    destination_location = models.ForeignKey(
        WarehouseLocation, null=True, blank=True, on_delete=models.SET_NULL, related_name="inbound_moves"
    )
    move_type = models.CharField(max_length=20, choices=MoveType.choices, default=MoveType.IN)
    quantity = models.DecimalField(max_digits=14, decimal_places=3)
    reference = models.CharField(max_length=120, blank=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.move_type} {self.quantity} × {self.product.sku}"

    class Meta:
        db_table = "stock_move"


class ReorderRule(createdtimestamp_uid, activearchlockedMixin):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="reorder_rules")
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name="reorder_rules")
    min_qty = models.DecimalField(max_digits=14, decimal_places=3, default=0)
    max_qty = models.DecimalField(max_digits=14, decimal_places=3, default=0)
    reorder_qty = models.DecimalField(max_digits=14, decimal_places=3, default=0)

    class Meta:
        unique_together = (("product", "warehouse"),)

    def __str__(self):
        return f"Reorder: {self.product.sku} @ {self.warehouse.code}"


class StockAlert(createdtimestamp_uid, activearchlockedMixin):
    class AlertType(models.TextChoices):
        STOCKOUT = "stockout", "Stockout"
        LOW_STOCK = "low_stock", "Low Stock"
        EXPIRY = "expiry", "Expiry"
        OVERSTOCK = "overstock", "Overstock"

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="alerts")
    warehouse = models.ForeignKey(
        Warehouse, null=True, blank=True, on_delete=models.SET_NULL, related_name="alerts"
    )
    alert_type = models.CharField(max_length=30, choices=AlertType.choices)
    message = models.CharField(max_length=300)
    resolved_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.alert_type}: {self.product.sku}"

    class Meta:
        db_table = "stock_alert"


# ---------------------------------------------------------------------------
# Signals — auto-create a Chart-of-Account linked Account for every new Product
# ---------------------------------------------------------------------------

@receiver(post_save, sender=Product)
def create_product_account(sender, instance, created, **kwargs):
    if not created or instance.account_id:
        return
    try:
        inventory_coa = Charts_of_account.objects.get(account_type="asset", name__icontains="inventory")
    except Charts_of_account.DoesNotExist:
        return
    content_type = ContentType.objects.get_for_model(instance)
    account, _ = Account.objects.get_or_create(
        accounttype=inventory_coa,
        content_type=content_type,
        object_id=instance.pk,
        defaults={"name": f"Inventory – {instance.name}"},
    )
    Product.objects.filter(pk=instance.pk).update(account=account)


def _refresh_reorder_alerts(product, warehouse):
    reorder_rule = ReorderRule.objects.filter(product=product, warehouse=warehouse, is_active=True).first()
    if reorder_rule is None:
        return

    stock_summary = ItemInventoryLot.objects.filter(
        lot__product=product,
        warehouse=warehouse,
        is_active=True,
    ).aggregate(total=Sum("qty_on_hand"))
    qty = stock_summary["total"] or 0

    if qty <= 0:
        StockAlert.objects.get_or_create(
            product=product,
            warehouse=warehouse,
            alert_type=StockAlert.AlertType.STOCKOUT,
            message=f"Stock out for {product.sku} in {warehouse.code}",
        )
        return

    if qty < reorder_rule.min_qty:
        StockAlert.objects.get_or_create(
            product=product,
            warehouse=warehouse,
            alert_type=StockAlert.AlertType.LOW_STOCK,
            message=f"Low stock for {product.sku} in {warehouse.code}. Qty={qty}",
        )


@receiver(post_save, sender=StockMove)
def apply_stock_move_to_inventory_lot(sender, instance, created, **kwargs):
    # Apply stock movement only once on creation.
    if not created:
        return

    lot = instance.lot
    if lot is None:
        lot, _ = ItemLot.objects.get_or_create(
            product=instance.product,
            variant=instance.variant,
            lot_number=f"AUTO-{instance.id}",
        )

    if instance.move_type == StockMove.MoveType.TRANSFER:
        if instance.source_location_id:
            source_entry, _ = ItemInventoryLot.objects.get_or_create(
                lot=lot,
                warehouse=instance.warehouse,
                location=instance.source_location,
            )
            source_entry.qty_on_hand = (source_entry.qty_on_hand or 0) - instance.quantity
            source_entry.save(update_fields=["qty_on_hand", "updated_at"])

        if instance.destination_location_id:
            destination_entry, _ = ItemInventoryLot.objects.get_or_create(
                lot=lot,
                warehouse=instance.warehouse,
                location=instance.destination_location,
            )
            destination_entry.qty_on_hand = (destination_entry.qty_on_hand or 0) + instance.quantity
            destination_entry.save(update_fields=["qty_on_hand", "updated_at"])

        _refresh_reorder_alerts(instance.product, instance.warehouse)
        return

    target_location = instance.destination_location if instance.move_type in (
        StockMove.MoveType.IN,
        StockMove.MoveType.RETURN,
        StockMove.MoveType.ADJUST,
    ) else instance.source_location

    inventory_entry, _ = ItemInventoryLot.objects.get_or_create(
        lot=lot,
        warehouse=instance.warehouse,
        location=target_location,
    )

    if instance.move_type in (StockMove.MoveType.IN, StockMove.MoveType.RETURN):
        inventory_entry.qty_on_hand = (inventory_entry.qty_on_hand or 0) + instance.quantity
    elif instance.move_type == StockMove.MoveType.OUT:
        inventory_entry.qty_on_hand = (inventory_entry.qty_on_hand or 0) - instance.quantity
    else:  # ADJUST
        inventory_entry.qty_on_hand = (inventory_entry.qty_on_hand or 0) + instance.quantity

    inventory_entry.save(update_fields=["qty_on_hand", "updated_at"])
    _refresh_reorder_alerts(instance.product, instance.warehouse)
