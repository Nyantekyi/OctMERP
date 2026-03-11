"""
apps/inventory/models.py

Inventory, product catalog, warehousing, and stock management.

Covers:
  - Units of measure with conversion
  - Manufacturers and product categories
  - Product + variant + barcode catalog
  - Price lists
  - Lot / serial tracking
  - Stock moves, adjustments, and reorder rules
"""

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Sum
from django.utils.translation import gettext_lazy as _
from djmoney.models.fields import MoneyField

from apps.common.models import TenantAwareModel, DEFAULT_CURRENCY, CURRENCY_CHOICES


# ─────────────────────────────────────────────────────────────────────────────
# Units of Measure
# ─────────────────────────────────────────────────────────────────────────────

class UnitCategory(TenantAwareModel):
    """Groups related units (e.g. Weight, Volume, Length, Quantity)."""
    name = models.CharField(_("Category"), max_length=50, unique=True)

    class Meta:
        verbose_name = _("Unit Category")
        verbose_name_plural = _("Unit Categories")
        ordering = ["name"]

    def __str__(self):
        return self.name


class Unit(TenantAwareModel):
    """
    Base reference unit (always ratio=1.0) in a UnitCategory.
    Each category must have exactly one base unit.
    """
    name = models.CharField(_("Unit Name"), max_length=50, unique=True)
    symbol = models.CharField(_("Symbol"), max_length=10, blank=True)
    category = models.ForeignKey(UnitCategory, on_delete=models.PROTECT, related_name="units")
    is_base = models.BooleanField(
        _("Is Base Unit?"), default=False,
        help_text=_("Only one base unit allowed per category.")
    )

    class Meta:
        verbose_name = _("Unit")
        verbose_name_plural = _("Units")
        ordering = ["category", "name"]

    def __str__(self):
        return f"{self.name} ({self.symbol})" if self.symbol else self.name


class UnitOfMeasure(TenantAwareModel):
    """Conversion rule: 1 unit = ratio × base_unit of the same category."""
    unit = models.OneToOneField(Unit, on_delete=models.CASCADE, related_name="conversion")
    base_unit = models.ForeignKey(Unit, on_delete=models.PROTECT, related_name="derived_units")
    ratio = models.DecimalField(
        _("Ratio to Base"), max_digits=20, decimal_places=8, default=1,
        help_text=_("1 of this unit = ratio × base unit")
    )

    class Meta:
        verbose_name = _("Unit of Measure")
        verbose_name_plural = _("Units of Measure")

    def __str__(self):
        return f"1 {self.unit} = {self.ratio} {self.base_unit}"

    def clean(self):
        if self.unit.category != self.base_unit.category:
            raise ValidationError(_("Unit and base unit must be in the same category."))
        if self.ratio <= 0:
            raise ValidationError(_("Ratio must be greater than zero."))

    def to_base(self, quantity):
        return quantity * self.ratio

    def from_base(self, base_quantity):
        return base_quantity / self.ratio


# ─────────────────────────────────────────────────────────────────────────────
# Manufacturer
# ─────────────────────────────────────────────────────────────────────────────

class Manufacturer(TenantAwareModel):
    name = models.CharField(_("Manufacturer"), max_length=200, unique=True)
    country = models.ForeignKey(
        "contact.Country", on_delete=models.SET_NULL, null=True, blank=True, related_name="manufacturers"
    )
    website = models.URLField(blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = _("Manufacturer")
        verbose_name_plural = _("Manufacturers")
        ordering = ["name"]

    def __str__(self):
        return self.name


# ─────────────────────────────────────────────────────────────────────────────
# Product Catalog
# ─────────────────────────────────────────────────────────────────────────────

class ProductCategory(TenantAwareModel):
    """Hierarchical product category tree."""
    name = models.CharField(_("Category Name"), max_length=100)
    parent = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, blank=True, related_name="subcategories"
    )
    description = models.TextField(blank=True)
    icon = models.CharField(_("Icon slug"), max_length=50, blank=True)
    image = models.ImageField(upload_to="category_images/", null=True, blank=True)

    class Meta:
        verbose_name = _("Product Category")
        verbose_name_plural = _("Product Categories")
        unique_together = ("name", "parent")
        ordering = ["name"]

    def __str__(self):
        if self.parent:
            return f"{self.parent} / {self.name}"
        return self.name


class VariantType(TenantAwareModel):
    """Defines a product attribute dimension (e.g. Color, Size, Material)."""
    name = models.CharField(_("Attribute Name"), max_length=50, unique=True)
    display_as = models.CharField(
        _("Display As"), max_length=20,
        choices=[("dropdown", "Dropdown"), ("swatch", "Colour Swatch"), ("radio", "Radio Buttons")],
        default="dropdown"
    )

    class Meta:
        verbose_name = _("Variant Type")
        verbose_name_plural = _("Variant Types")
        ordering = ["name"]

    def __str__(self):
        return self.name


class VariantValue(TenantAwareModel):
    """A possible value for a VariantType (e.g. Red, XL, Cotton)."""
    variant_type = models.ForeignKey(VariantType, on_delete=models.CASCADE, related_name="values")
    name = models.CharField(_("Value"), max_length=100)
    color_hex = models.CharField(_("Colour Hex"), max_length=7, blank=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        verbose_name = _("Variant Value")
        verbose_name_plural = _("Variant Values")
        unique_together = ("variant_type", "name")
        ordering = ["variant_type", "order", "name"]

    def __str__(self):
        return f"{self.variant_type.name}: {self.name}"


class Product(TenantAwareModel):
    """
    Master product / SKU template.
    Physical variants (color/size combos) live in ProductVariant.
    """
    PRODUCT_TYPE_CHOICES = [
        ("storable", _("Storable Product")),
        ("consumable", _("Consumable")),
        ("service", _("Service")),
        ("digital", _("Digital / Download")),
    ]

    name = models.CharField(_("Product Name"), max_length=255)
    internal_reference = models.CharField(_("Internal Reference"), max_length=100, blank=True)
    description = models.TextField(blank=True)
    short_description = models.CharField(_("Short Description"), max_length=512, blank=True)
    product_type = models.CharField(_("Product Type"), max_length=20, choices=PRODUCT_TYPE_CHOICES, default="storable")
    category = models.ForeignKey(ProductCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name="products")
    manufacturer = models.ForeignKey(Manufacturer, on_delete=models.SET_NULL, null=True, blank=True, related_name="products")
    unit = models.ForeignKey(Unit, on_delete=models.PROTECT, verbose_name=_("Sales Unit"), related_name="products")
    purchase_unit = models.ForeignKey(
        Unit, on_delete=models.PROTECT, null=True, blank=True,
        verbose_name=_("Purchase Unit"), related_name="purchased_products"
    )
    variant_types = models.ManyToManyField(VariantType, blank=True, related_name="products")
    image = models.ImageField(upload_to="product_images/", null=True, blank=True)
    # Pricing
    sales_price = MoneyField(
        _("Sales Price"), max_digits=20, decimal_places=2,
        default=0, default_currency=DEFAULT_CURRENCY, currency_choices=CURRENCY_CHOICES
    )
    cost_price = MoneyField(
        _("Cost Price"), max_digits=20, decimal_places=2,
        default=0, default_currency=DEFAULT_CURRENCY, currency_choices=CURRENCY_CHOICES
    )
    tax = models.ForeignKey(
        "accounting.Tax", on_delete=models.SET_NULL, null=True, blank=True, related_name="products"
    )
    # Inventory settings (only relevant for storable)
    can_be_sold = models.BooleanField(_("Can Be Sold?"), default=True)
    can_be_purchased = models.BooleanField(_("Can Be Purchased?"), default=True)
    track_inventory = models.BooleanField(_("Track Inventory?"), default=True)
    min_stock_warning = models.DecimalField(_("Min Stock Warning"), max_digits=10, decimal_places=3, default=0)
    department = models.ForeignKey(
        "department.Department", on_delete=models.PROTECT, related_name="products"
    )

    class Meta:
        verbose_name = _("Product")
        verbose_name_plural = _("Products")
        unique_together = ("name", "department")
        ordering = ["name"]

    def __str__(self):
        return self.name


class ProductVariant(TenantAwareModel):
    """
    A sellable / purchasable instance of a Product with a specific
    combination of attribute values (e.g. Red + XL).
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="variants")
    sku = models.CharField(_("SKU"), max_length=100, unique=True)
    attributes = models.ManyToManyField(VariantValue, blank=True, verbose_name=_("Attribute Values"))
    extra_description = models.CharField(_("Extra Description"), max_length=255, blank=True)
    image = models.ImageField(upload_to="variant_images/", null=True, blank=True)
    # Variant-level price override (if null, falls back to Product.sales_price)
    sales_price_override = MoneyField(
        _("Sales Price Override"), max_digits=20, decimal_places=2,
        null=True, blank=True,
        default_currency=DEFAULT_CURRENCY, currency_choices=CURRENCY_CHOICES
    )
    cost_price_override = MoneyField(
        _("Cost Price Override"), max_digits=20, decimal_places=2,
        null=True, blank=True,
        default_currency=DEFAULT_CURRENCY, currency_choices=CURRENCY_CHOICES
    )
    weight_kg = models.DecimalField(_("Weight (kg)"), max_digits=8, decimal_places=3, default=0)
    is_default = models.BooleanField(_("Default Variant?"), default=False)

    class Meta:
        verbose_name = _("Product Variant")
        verbose_name_plural = _("Product Variants")
        ordering = ["product", "sku"]

    def __str__(self):
        attrs = ", ".join(str(a) for a in self.attributes.all())
        return f"{self.product.name} [{attrs or self.sku}]"

    @property
    def effective_price(self):
        return self.sales_price_override or self.product.sales_price

    @property
    def effective_cost(self):
        return self.cost_price_override or self.product.cost_price


class Barcode(TenantAwareModel):
    BARCODE_TYPE_CHOICES = [
        ("ean13", "EAN-13"),
        ("ean8", "EAN-8"),
        ("upc_a", "UPC-A"),
        ("qr", "QR Code"),
        ("code128", "Code 128"),
        ("other", "Other"),
    ]

    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, related_name="barcodes")
    barcode_type = models.CharField(_("Type"), max_length=20, choices=BARCODE_TYPE_CHOICES, default="ean13")
    value = models.CharField(_("Barcode Value"), max_length=100, unique=True)

    class Meta:
        verbose_name = _("Barcode")
        verbose_name_plural = _("Barcodes")

    def __str__(self):
        return f"{self.barcode_type}: {self.value}"


# ─────────────────────────────────────────────────────────────────────────────
# Pricelist
# ─────────────────────────────────────────────────────────────────────────────

class Pricelist(TenantAwareModel):
    """
    Named pricelist (e.g. Wholesale, Retail, VIP).
    Rules are defined per variant/category in PricelistItem.
    """
    COMPUTATION_CHOICES = [
        ("fixed", _("Fixed Price")),
        ("percent_off", _("% Off Base")),
        ("markup", _("Markup over Cost")),
    ]

    name = models.CharField(_("Pricelist Name"), max_length=100, unique=True)
    currency = models.CharField(_("Currency"), max_length=3, default=DEFAULT_CURRENCY)
    computation = models.CharField(_("Computation Method"), max_length=20, choices=COMPUTATION_CHOICES, default="fixed")
    valid_from = models.DateField(_("Valid From"), null=True, blank=True)
    valid_to = models.DateField(_("Valid To"), null=True, blank=True)
    department = models.ForeignKey(
        "department.Department", on_delete=models.PROTECT, related_name="pricelists", null=True, blank=True
    )

    class Meta:
        verbose_name = _("Pricelist")
        verbose_name_plural = _("Pricelists")
        ordering = ["name"]

    def __str__(self):
        return self.name


class PricelistItem(TenantAwareModel):
    """
    Single rule within a Pricelist: applies to a specific variant or
    an entire product/category with optional quantity breaks.
    """
    pricelist = models.ForeignKey(Pricelist, on_delete=models.CASCADE, related_name="items")
    variant = models.ForeignKey(
        ProductVariant, on_delete=models.CASCADE, null=True, blank=True, related_name="pricelist_items"
    )
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, null=True, blank=True, related_name="pricelist_items"
    )
    category = models.ForeignKey(
        ProductCategory, on_delete=models.CASCADE, null=True, blank=True, related_name="pricelist_items"
    )
    min_quantity = models.DecimalField(_("Min. Quantity"), max_digits=10, decimal_places=3, default=1)
    fixed_price = MoneyField(
        _("Fixed Price"), max_digits=20, decimal_places=2,
        null=True, blank=True,
        default_currency=DEFAULT_CURRENCY, currency_choices=CURRENCY_CHOICES
    )
    percent_discount = models.DecimalField(_("Discount %"), max_digits=5, decimal_places=2, default=0)
    markup_percent = models.DecimalField(_("Markup %"), max_digits=5, decimal_places=2, default=0)

    class Meta:
        verbose_name = _("Pricelist Item")
        verbose_name_plural = _("Pricelist Items")
        ordering = ["pricelist", "min_quantity"]

    def __str__(self):
        target = self.variant or self.product or self.category or "All"
        return f"{self.pricelist} — {target} (min qty {self.min_quantity})"

    def compute_price(self, base_price):
        if self.pricelist.computation == "fixed" and self.fixed_price:
            return self.fixed_price
        elif self.pricelist.computation == "percent_off":
            return base_price * (1 - self.percent_discount / 100)
        elif self.pricelist.computation == "markup":
            return base_price * (1 + self.markup_percent / 100)
        return base_price


# ─────────────────────────────────────────────────────────────────────────────
# Lot / Serial Tracking
# ─────────────────────────────────────────────────────────────────────────────

class ItemLot(TenantAwareModel):
    """
    Represents a physical lot or serial number.
    Use lot_type='serial' for 1-unit serial tracking.
    """
    LOT_TYPE_CHOICES = [("lot", _("Lot")), ("serial", _("Serial Number"))]

    variant = models.ForeignKey(ProductVariant, on_delete=models.PROTECT, related_name="lots")
    lot_number = models.CharField(_("Lot / Serial No."), max_length=100)
    lot_type = models.CharField(_("Type"), max_length=10, choices=LOT_TYPE_CHOICES, default="lot")
    manufacture_date = models.DateField(_("Manufacture Date"), null=True, blank=True)
    expiry_date = models.DateField(_("Expiry Date"), null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = _("Item Lot / Serial")
        verbose_name_plural = _("Item Lots / Serials")
        unique_together = ("variant", "lot_number")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.variant} — Lot {self.lot_number}"


# ─────────────────────────────────────────────────────────────────────────────
# Stock Move
# ─────────────────────────────────────────────────────────────────────────────

class StockMove(TenantAwareModel):
    """
    Records every inventory movement: receipts, dispatches, internal transfers,
    adjustments, returns, scraps.
    """
    MOVE_TYPE_CHOICES = [
        ("receipt", _("Receipt")),
        ("dispatch", _("Dispatch / Sale")),
        ("internal", _("Internal Transfer")),
        ("adjustment", _("Adjustment")),
        ("return", _("Return")),
        ("scrap", _("Scrap / Write-Off")),
        ("production_in", _("Production Input")),
        ("production_out", _("Production Output")),
    ]
    STATE_CHOICES = [
        ("draft", _("Draft")),
        ("confirmed", _("Confirmed")),
        ("done", _("Done")),
        ("cancelled", _("Cancelled")),
    ]

    variant = models.ForeignKey(ProductVariant, on_delete=models.PROTECT, related_name="stock_moves")
    lot = models.ForeignKey(
        ItemLot, on_delete=models.SET_NULL, null=True, blank=True, related_name="stock_moves"
    )
    move_type = models.CharField(_("Move Type"), max_length=20, choices=MOVE_TYPE_CHOICES)
    state = models.CharField(_("State"), max_length=20, choices=STATE_CHOICES, default="draft")
    quantity = models.DecimalField(_("Quantity"), max_digits=14, decimal_places=4)
    unit = models.ForeignKey(Unit, on_delete=models.PROTECT, related_name="stock_moves")
    from_branch = models.ForeignKey(
        "department.Branch", on_delete=models.SET_NULL, null=True, blank=True, related_name="outgoing_moves"
    )
    to_branch = models.ForeignKey(
        "department.Branch", on_delete=models.SET_NULL, null=True, blank=True, related_name="incoming_moves"
    )
    from_shelf = models.ForeignKey(
        "department.Shelfing", on_delete=models.SET_NULL, null=True, blank=True, related_name="outgoing_moves"
    )
    to_shelf = models.ForeignKey(
        "department.Shelfing", on_delete=models.SET_NULL, null=True, blank=True, related_name="incoming_moves"
    )
    unit_cost = MoneyField(
        _("Unit Cost"), max_digits=20, decimal_places=2,
        default=0, default_currency=DEFAULT_CURRENCY, currency_choices=CURRENCY_CHOICES
    )
    move_date = models.DateTimeField(_("Move Date"), default=None, null=True, blank=True)
    reference = models.CharField(_("Reference"), max_length=100, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = _("Stock Move")
        verbose_name_plural = _("Stock Moves")
        ordering = ["-move_date"]

    def __str__(self):
        return f"{self.move_type} — {self.quantity} × {self.variant}"

    def clean(self):
        if self.move_type in ("receipt",) and not self.to_branch:
            raise ValidationError(_("Receipts must have a destination branch."))
        if self.move_type in ("dispatch",) and not self.from_branch:
            raise ValidationError(_("Dispatches must have a source branch."))
        if self.quantity <= 0:
            raise ValidationError(_("Quantity must be positive."))


class StockAdjustment(TenantAwareModel):
    """
    Physical stock-count reconciliation.
    Each line compares expected vs. counted quantity and creates a StockMove.
    """
    STATUS_CHOICES = [
        ("draft", _("Draft")),
        ("validated", _("Validated")),
        ("cancelled", _("Cancelled")),
    ]

    reference = models.CharField(_("Reference"), max_length=100, blank=True)
    branch = models.ForeignKey("department.Branch", on_delete=models.PROTECT, related_name="stock_adjustments")
    count_date = models.DateField(_("Count Date"), default=None, null=True, blank=True)
    status = models.CharField(_("Status"), max_length=20, choices=STATUS_CHOICES, default="draft")
    conducted_by = models.ForeignKey(
        "party.StaffProfile", on_delete=models.PROTECT, related_name="stock_adjustments"
    )
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = _("Stock Adjustment")
        verbose_name_plural = _("Stock Adjustments")
        ordering = ["-count_date"]

    def __str__(self):
        return f"Adjustment {self.reference or self.id} at {self.branch}"


class StockAdjustmentLine(TenantAwareModel):
    adjustment = models.ForeignKey(StockAdjustment, on_delete=models.CASCADE, related_name="lines")
    variant = models.ForeignKey(ProductVariant, on_delete=models.PROTECT, related_name="adjustment_lines")
    lot = models.ForeignKey(ItemLot, on_delete=models.SET_NULL, null=True, blank=True)
    shelf = models.ForeignKey("department.Shelfing", on_delete=models.SET_NULL, null=True, blank=True)
    expected_qty = models.DecimalField(_("Expected Qty"), max_digits=14, decimal_places=4, default=0)
    counted_qty = models.DecimalField(_("Counted Qty"), max_digits=14, decimal_places=4, default=0)
    difference = models.DecimalField(_("Difference"), max_digits=14, decimal_places=4, default=0, editable=False)

    class Meta:
        verbose_name = _("Adjustment Line")
        verbose_name_plural = _("Adjustment Lines")
        unique_together = ("adjustment", "variant", "lot")

    def save(self, *args, **kwargs):
        self.difference = self.counted_qty - self.expected_qty
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.variant} expected={self.expected_qty} counted={self.counted_qty}"


# ─────────────────────────────────────────────────────────────────────────────
# Reorder Rule
# ─────────────────────────────────────────────────────────────────────────────

class ReorderRule(TenantAwareModel):
    """Auto-reorder trigger for a variant at a specific branch."""
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, related_name="reorder_rules")
    branch = models.ForeignKey("department.Branch", on_delete=models.CASCADE, related_name="reorder_rules")
    min_quantity = models.DecimalField(_("Reorder Point"), max_digits=14, decimal_places=4)
    max_quantity = models.DecimalField(_("Max Stock Level"), max_digits=14, decimal_places=4)
    reorder_quantity = models.DecimalField(_("Reorder Quantity"), max_digits=14, decimal_places=4)
    preferred_supplier = models.ForeignKey(
        "party.SupplierProfile", on_delete=models.SET_NULL, null=True, blank=True, related_name="reorder_rules"
    )
    lead_time_days = models.PositiveSmallIntegerField(_("Lead Time (days)"), default=0)

    class Meta:
        verbose_name = _("Reorder Rule")
        verbose_name_plural = _("Reorder Rules")
        unique_together = ("variant", "branch")
        ordering = ["variant"]

    def __str__(self):
        return f"Reorder {self.variant.sku} at {self.branch} when qty < {self.min_quantity}"
