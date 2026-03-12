"""
Inventory models — follows plan_new.md §8.4 naming conventions.

Key naming decisions aligned to plan:
  unit                    – base unit of measure (tablet, capsule, bottle, strip)
  unitofmeasure           – conversion between units (1 strip = 10 tablets)
  Manufacturer            – kept
  VariantType             – typed variant dimension
  VariantAttribute        – individual values per VariantType
  Item                    – replaces 'Product' (canonical name from plan)
  itemvariant             – specific variant combination
  itemvariantprices       – per-variant per-department price override
  item_pricing_department – per-dept selling price for an item
  selling_rules           – what is allowed in a sale within a department
  ItemLot                 – physical batch / lot record
  StockLotCostValuation   – AVCO cost per lot per department (base currency)
  ItemInventoryLot        – stock-on-hand per lot per branch with inventory_state
  ItemInventoryLotVariant – per-variant qty breakdown within a lot
  StockLedgerEntry        – primary ledger line (replaces StockMove)
  itemInvJournalEntry     – detailed per-lot movement; post_save updates qty
  ReorderRule             – kept
  StockAlert              – kept
"""

from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Sum
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from djmoney.models.fields import MoneyField

from apps.accounts.models import Account, Charts_of_account, Tax, default_currency
from apps.common.models import CompanyMixin, activearchlockedMixin, createdtimestamp_uid


# ===========================================================================
# Unit / UOM
# ===========================================================================

class unit(createdtimestamp_uid, activearchlockedMixin, CompanyMixin):
    """Base unit of measure — the indivisible count (tablet, capsule, ml, kg)."""
    name = models.CharField(max_length=100)
    abr = models.CharField(max_length=20, blank=True)
    is_base_unit = models.BooleanField(default=True)

    class Meta:
        unique_together = (("company", "name"),)

    def __str__(self):
        return self.abr or self.name


class unitofmeasure(createdtimestamp_uid, activearchlockedMixin, CompanyMixin):
    """
    Conversion between units.
    e.g.  converts_from=strip, converts_to=tablet, conversion_rate=10
          meaning 1 strip = 10 tablets.
    """
    converts_to = models.ForeignKey(
        unit, on_delete=models.PROTECT, related_name="as_target_uom"
    )
    converts_from = models.ForeignKey(
        unit, on_delete=models.PROTECT, related_name="as_source_uom"
    )
    conversion_rate = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = (("converts_to", "converts_from", "conversion_rate"),)

    def __str__(self):
        return f"1 {self.converts_from} = {self.conversion_rate} {self.converts_to}"


# ===========================================================================
# Catalogue helpers
# ===========================================================================

class Manufacturer(createdtimestamp_uid, activearchlockedMixin, CompanyMixin):
    class BrandCategory(models.TextChoices):
        PREMIUM = "Premium", "Premium"
        SUPERIOR = "Superior", "Superior"
        REGULAR = "Regular", "Regular"
        VALUE = "ValuePackage", "Value Package"
        LOW_END = "LowEnd", "Low End"

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    brand_category = models.CharField(
        max_length=20, choices=BrandCategory.choices, default=BrandCategory.REGULAR
    )
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


# ===========================================================================
# Variant system
# ===========================================================================

class VariantType(createdtimestamp_uid, activearchlockedMixin, CompanyMixin):
    """
    Defines a typed dimension for product variants.
    Examples: Color, Size (Alpha), Size (Number), Flavor, Capacity.
    """
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    multiselect = models.BooleanField(
        default=False,
        help_text="Allow an item to have multiple values for this variant type",
    )

    class Meta:
        unique_together = (("company", "name"),)

    def save(self, *args, **kwargs):
        self.name = self.name.capitalize()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class VariantAttribute(createdtimestamp_uid, activearchlockedMixin, CompanyMixin):
    """A specific value for a VariantType (e.g. Red, XL, 500ml)."""
    variant_type = models.ForeignKey(
        VariantType, on_delete=models.CASCADE, related_name="attributes"
    )
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    class Meta:
        unique_together = (("variant_type", "name"),)

    def __str__(self):
        return f"{self.variant_type.name}: {self.name}"


# ===========================================================================
# Selling rules
# ===========================================================================

class selling_rules(createdtimestamp_uid, activearchlockedMixin):
    """
    Controls what can/cannot be done when selling items in a department.
    Linked to item_pricing_department for per-SKU overrides.
    """
    department = models.ForeignKey(
        "department.Department", on_delete=models.CASCADE, related_name="selling_rules"
    )
    name = models.CharField(max_length=150)

    # Pricing permissions
    variant_prices_allowed = models.BooleanField(default=False)
    discount_allowed = models.BooleanField(default=True)
    price_entry_required = models.BooleanField(default=False)

    # Item type flags
    service_item_included = models.BooleanField(default=True)
    weight_entry_required = models.BooleanField(default=False)

    # Promotions / restrictions
    coupon_restricted = models.BooleanField(default=False)
    employee_discount_allowed = models.BooleanField(default=False)
    allow_food_stamp = models.BooleanField(default=False)
    tax_exempt = models.BooleanField(default=False)
    tax_excluded_in_prices = models.BooleanField(default=False)
    prohibit_repeat_key = models.BooleanField(default=False)

    # Loyalty / shopper programs
    frequent_shopper_eligibility = models.BooleanField(default=False)
    frequent_shopper_points = models.PositiveIntegerField(default=0)

    # Other
    age_restrictions = models.BooleanField(default=False)
    return_allowed = models.BooleanField(default=True)
    as_product_discount = models.BooleanField(default=False)
    credit_sales_allowed = models.BooleanField(default=False)

    class Meta:
        unique_together = (("name", "department"),)
        db_table = "selling_rules"

    def __str__(self):
        return f"{self.name} @ {self.department}"


# ===========================================================================
# Item  (was 'Product')
# ===========================================================================

class Item(createdtimestamp_uid, activearchlockedMixin, CompanyMixin):
    """
    Core inventory item.  Named 'Item' per plan_new.md convention.
    Replaces the previous 'Product' model.
    """
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        ARCHIVED = "archived", "Archived"
        LOCKED = "locked", "Locked"
        DELETED = "deleted", "Deleted"

    status = models.CharField(max_length=15, choices=Status.choices, default=Status.ACTIVE)
    category = models.ForeignKey(
        Category, null=True, blank=True, on_delete=models.SET_NULL, related_name="items"
    )
    name = models.CharField(max_length=255)
    namestrip = models.SlugField(max_length=300, blank=True, db_index=True)
    brandname = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    manufacturer = models.ForeignKey(
        Manufacturer, null=True, blank=True, on_delete=models.SET_NULL, related_name="items"
    )
    unit = models.ForeignKey(
        unit, null=True, blank=True, on_delete=models.SET_NULL, related_name="items"
    )
    tax = models.ForeignKey(
        Tax, null=True, blank=True, on_delete=models.SET_NULL, related_name="items"
    )
    pictures = ArrayField(models.CharField(max_length=500), blank=True, default=list)
    barcodes = ArrayField(models.CharField(max_length=120), blank=True, default=list)
    sku = models.CharField(max_length=80, blank=True)

    # Variant configuration
    has_variants = models.BooleanField(default=False)
    item_variants_types = models.ManyToManyField(VariantType, blank=True)
    variants_price_allowed = models.BooleanField(default=False)

    # Item type flags
    is_manufactured = models.BooleanField(default=False)
    is_raw_material = models.BooleanField(default=False)
    is_internaluseonly = models.BooleanField(default=False)
    is_serviceitem = models.BooleanField(default=False)
    is_expiry_tracked = models.BooleanField(default=False)
    is_serialised = models.BooleanField(default=False)
    is_purchasable = models.BooleanField(default=True)
    is_sellable = models.BooleanField(default=True)

    substitutebrands = models.ManyToManyField("self", blank=True)
    service_added = models.ManyToManyField(
        "self", blank=True, related_name="services_including"
    , symmetrical=False)
    tags = ArrayField(models.CharField(max_length=50), blank=True, default=list)

    # Linked inventory ledger account (auto-created via signal)
    account = models.ForeignKey(
        Account, null=True, blank=True, on_delete=models.SET_NULL, related_name="items"
    )

    class Meta:
        unique_together = (("company", "sku"),)
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["namestrip"]),
            models.Index(fields=["brandname"]),
        ]
        db_table = "inventory_item"

    def clean(self):
        if self.is_serviceitem and self.barcodes:
            raise ValidationError("Service items cannot have barcodes.")
        if self.has_variants and self.is_serviceitem:
            raise ValidationError("Service items cannot have variants.")

    def save(self, *args, **kwargs):
        if not self.namestrip:
            from django.utils.text import slugify
            self.namestrip = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Barcode(createdtimestamp_uid):
    """Multiple barcode formats per item (EAN-13, UPC, QR, Code128, etc.)."""
    class BarcodeType(models.TextChoices):
        EAN13 = "ean13", "EAN-13"
        UPC = "upc", "UPC"
        QR = "qr", "QR Code"
        CODE128 = "code128", "Code 128"
        OTHER = "other", "Other"

    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name="barcode_records")
    value = models.CharField(max_length=120, unique=True)
    barcode_type = models.CharField(
        max_length=20, choices=BarcodeType.choices, default=BarcodeType.EAN13
    )

    def __str__(self):
        return self.value


# ===========================================================================
# Item variants
# ===========================================================================

class itemvariant(createdtimestamp_uid, activearchlockedMixin, CompanyMixin):
    """A specific variant of an Item (e.g. Red XL T-shirt)."""
    name = models.CharField(max_length=200)
    item = models.ForeignKey(
        Item,
        on_delete=models.CASCADE,
        related_name="variants",
        limit_choices_to={"has_variants": True},
    )
    variant = models.ManyToManyField(VariantAttribute, blank=True)
    pictures = ArrayField(models.CharField(max_length=500), blank=True, default=list)

    class Meta:
        unique_together = (("name", "item"),)
        db_table = "inventory_itemvariant"

    def __str__(self):
        return f"{self.item.name} – {self.name}"


# ===========================================================================
# Pricing
# ===========================================================================

class item_pricing_department(createdtimestamp_uid, activearchlockedMixin, CompanyMixin):
    """Per-department selling price override for an Item."""
    sale_department = models.ForeignKey(
        "department.Department", on_delete=models.CASCADE, related_name="item_prices"
    )
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name="department_prices")
    selling_rules = models.ForeignKey(
        selling_rules, null=True, blank=True, on_delete=models.SET_NULL, related_name="prices"
    )
    selling_price = MoneyField(
        max_digits=14, decimal_places=2, default=0, default_currency=default_currency
    )
    employee_discount = models.DecimalField(max_digits=7, decimal_places=2, default=0)
    uom = models.ForeignKey(
        unitofmeasure, null=True, blank=True, on_delete=models.SET_NULL, related_name="prices"
    )
    markup_percentage = models.DecimalField(max_digits=7, decimal_places=2, default=0)
    allowed_currencies = ArrayField(
        models.CharField(max_length=3), blank=True, default=list
    )

    class Meta:
        unique_together = (("item", "sale_department"),)
        db_table = "item_pricing_department"
        verbose_name = "item_pricing_department"
        verbose_name_plural = "item_pricing_departments"

    def __str__(self):
        return f"{self.item.name} @ {self.sale_department}"


class itemvariantprices(createdtimestamp_uid, activearchlockedMixin):
    """Per-variant price override linked to an item_pricing_department."""
    variant_item = models.ForeignKey(
        itemvariant, on_delete=models.CASCADE, related_name="prices"
    )
    itempricingdepartment = models.ForeignKey(
        item_pricing_department, on_delete=models.CASCADE, related_name="variant_prices"
    )
    selling_price = MoneyField(
        max_digits=14, decimal_places=2, default=0, default_currency=default_currency
    )

    class Meta:
        unique_together = (("variant_item", "itempricingdepartment"),)
        db_table = "inventory_itemvariantprices"

    def __str__(self):
        return f"{self.variant_item} – {self.selling_price}"


# ===========================================================================
# Lot / Batch tracking
# ===========================================================================

class ItemLot(createdtimestamp_uid, activearchlockedMixin):
    """A physical batch/lot of an Item received into stock."""
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        INACTIVE = "inactive", "Inactive"

    status = models.CharField(max_length=15, choices=Status.choices, default=Status.ACTIVE)
    item = models.ForeignKey(
        Item,
        on_delete=models.CASCADE,
        related_name="lots",
        limit_choices_to={"is_serviceitem": False},
    )
    variant = models.ForeignKey(
        itemvariant, null=True, blank=True, on_delete=models.SET_NULL, related_name="lots"
    )
    lot_number = models.CharField(max_length=120)
    manufacturing_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    uom = models.ForeignKey(
        unitofmeasure, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="lot_packs",
        help_text="Pack UOM for this lot (e.g. strip of 10 tablets)",
    )
    serial_numbers = ArrayField(models.CharField(max_length=100), blank=True, default=list)
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = (("item", "lot_number"),)
        db_table = "item_lot"

    def clean(self):
        if self.manufacturing_date and self.expiry_date:
            if self.manufacturing_date >= self.expiry_date:
                raise ValidationError("Manufacturing date must be before expiry date.")
        if self.item_id and self.item.is_expiry_tracked:
            if not self.manufacturing_date or not self.expiry_date:
                raise ValidationError(
                    "Manufacturing and expiry dates are required for expiry-tracked items."
                )

    @property
    def is_expired(self):
        return bool(self.expiry_date and self.expiry_date <= timezone.now().date())

    @property
    def days_to_expiry(self):
        if not self.expiry_date:
            return None
        return (self.expiry_date - timezone.now().date()).days

    @property
    def can_expire(self):
        return self.item.is_expiry_tracked if self.item_id else False

    def __str__(self):
        label = self.item.sku or self.item.name if self.item_id else "?"
        return f"{label}::{self.lot_number}"


class StockLotCostValuation(createdtimestamp_uid):
    """
    AVCO (Average Cost) valuation per lot per department.
    Formula: (QtyOnHand × CurrentCost + QtyReceived × ReceiptCost)
              ÷ (QtyOnHand + QtyReceived)
    Always denominated in company base currency (GHS).
    """
    itemlot = models.ForeignKey(
        ItemLot, on_delete=models.CASCADE, related_name="cost_valuations"
    )
    cost_department = models.ForeignKey(
        "department.Department", on_delete=models.CASCADE, related_name="lot_cost_valuations"
    )
    uom = models.ForeignKey(
        unitofmeasure,
        on_delete=models.PROTECT,
        related_name="cost_valuations",
        limit_choices_to={"conversion_rate": 1},
        help_text="Must be the base unit UOM (conversion_rate=1)",
    )
    cost_price = MoneyField(
        max_digits=14, decimal_places=2, default=0, default_currency=default_currency,
        help_text="Always in company base currency (GHS)",
    )

    class Meta:
        unique_together = (("itemlot", "cost_department"),)
        db_table = "stock_lot_cost_valuation"

    def __str__(self):
        return f"{self.itemlot} cost @ {self.cost_department}"


class ItemInventoryLot(createdtimestamp_uid, activearchlockedMixin):
    """
    Tracks stock quantity per lot per branch per inventory state.
    inventory_state distinguishes sellable OnHand from other states.
    """
    class InventoryState(models.TextChoices):
        ON_HAND = "OnHand", "On Hand"          # sellable / transferable
        ON_ORDER = "OnOrder", "On Order"        # pending delivery
        ON_LAYAWAY = "OnLayaway", "On Layaway"  # partial/full payment reserved
        DAMAGED = "Damaged", "Damaged"          # expired or physically damaged
        ON_HOLD = "OnHold", "On Hold"           # pending inter-branch transfer

    item = models.ForeignKey(
        Item, on_delete=models.CASCADE, related_name="inventory_lots",
        help_text="Auto-set from itemlot.item on save",
    )
    itemlot = models.ForeignKey(ItemLot, on_delete=models.CASCADE, related_name="inventory_entries")
    location = models.ForeignKey(
        "department.Branch", on_delete=models.CASCADE, related_name="inventory_lots"
    )
    shelfnumber = models.ForeignKey(
        "department.Shelfing", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="inventory_lots",
    )
    qty = models.DecimalField(max_digits=14, decimal_places=3, default=0)
    inventory_state = models.CharField(
        max_length=20, choices=InventoryState.choices, default=InventoryState.ON_HAND
    )

    class Meta:
        unique_together = (("itemlot", "location", "inventory_state"),)
        db_table = "item_inventory_lot"

    def save(self, *args, **kwargs):
        # Auto-fill item FK from itemlot
        if self.itemlot_id and not self.item_id:
            self.item = self.itemlot.item
        super().save(*args, **kwargs)

    @property
    def packsizing(self):
        return self.itemlot.uom.conversion_rate if self.itemlot_id and self.itemlot.uom else 1

    @property
    def packname(self):
        return self.itemlot.uom.converts_from if self.itemlot_id and self.itemlot.uom else None

    @property
    def is_itemlot_expired(self):
        return self.itemlot.is_expired if self.itemlot_id else False

    def __str__(self):
        return f"{self.itemlot} @ {self.location} [{self.inventory_state}]"


class ItemInventoryLotVariant(createdtimestamp_uid):
    """Per-variant stock breakdown within an ItemInventoryLot."""
    lot = models.ForeignKey(
        ItemInventoryLot, on_delete=models.CASCADE, related_name="variant_quantities"
    )
    variant = models.ForeignKey(
        itemvariant, on_delete=models.CASCADE, related_name="inventory_quantities"
    )
    qty = models.DecimalField(max_digits=14, decimal_places=3, default=0)

    class Meta:
        unique_together = (("lot", "variant"),)
        db_table = "item_inventory_lot_variant"

    def __str__(self):
        return f"{self.variant} qty={self.qty}"


# ===========================================================================
# Stock ledger  (replaces StockMove)
# ===========================================================================

class StockLedgerEntry(createdtimestamp_uid):
    """
    One entry per branch per inventory transaction.
    The actual per-lot detail lives in itemInvJournalEntry.
    """
    class TransactType(models.TextChoices):
        INCREASE = "Increase", "Increase"
        DECREASE = "Decrease", "Decrease"

    branch = models.ForeignKey(
        "department.Branch", on_delete=models.CASCADE, related_name="stock_ledger_entries"
    )
    transaction = models.ForeignKey(
        "accounts.Transaction",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="stock_ledger_entries",
    )
    stockvaluation = MoneyField(
        max_digits=14, decimal_places=2, default=0, default_currency=default_currency
    )
    transaction_type = models.CharField(
        max_length=10, choices=(("Debit", "Debit"), ("Credit", "Credit"))
    )
    inventorytransacttype = models.CharField(
        max_length=10, choices=TransactType.choices
    )
    # GenericFK — source document (Bill, Transfer, Adjustment, SalesOrder, Return, etc.)
    content_type = models.ForeignKey(
        ContentType, null=True, blank=True, on_delete=models.SET_NULL
    )
    object_id = models.UUIDField(null=True, blank=True)

    class Meta:
        db_table = "stock_ledger_entry"

    def __str__(self):
        return f"{self.inventorytransacttype} {self.stockvaluation} @ {self.branch}"


class itemInvJournalEntry(createdtimestamp_uid):
    """
    Detailed per-lot, per-branch, per-state inventory movement record.
    A post_save signal on this model updates ItemInventoryLot.qty.
    """
    stockledger = models.ForeignKey(
        StockLedgerEntry, on_delete=models.CASCADE, related_name="journal_entries"
    )
    itemlot = models.ForeignKey(ItemLot, on_delete=models.CASCADE, related_name="journal_entries")
    location = models.ForeignKey(
        "department.Branch", on_delete=models.CASCADE, related_name="journal_entries"
    )
    inventory_state = models.CharField(
        max_length=20,
        choices=ItemInventoryLot.InventoryState.choices,
        default=ItemInventoryLot.InventoryState.ON_HAND,
    )
    uom = models.ForeignKey(
        unitofmeasure, on_delete=models.PROTECT, related_name="journal_entries"
    )
    uom_qty = models.DecimalField(max_digits=14, decimal_places=3, default=0)
    # qty = uom.conversion_rate × uom_qty — auto-computed on save
    qty = models.DecimalField(max_digits=14, decimal_places=3, default=0, editable=False)

    # Cost & valuation
    stock_valuation_unit = MoneyField(
        max_digits=14, decimal_places=2, default=0, default_currency=default_currency
    )
    stock_valuation_line = MoneyField(
        max_digits=14, decimal_places=2, default=0, default_currency=default_currency
    )

    # Movement counters (base units)
    beginning_unit_count_base = models.DecimalField(max_digits=14, decimal_places=3, default=0)
    gross_sales_unit_count_base = models.DecimalField(max_digits=14, decimal_places=3, default=0)
    return_unit_count_base = models.DecimalField(max_digits=14, decimal_places=3, default=0)
    received_unit_count_base = models.DecimalField(max_digits=14, decimal_places=3, default=0)
    received_from_vendor_unit_count_base = models.DecimalField(max_digits=14, decimal_places=3, default=0)
    return_to_vendor_unit_count_base = models.DecimalField(max_digits=14, decimal_places=3, default=0)
    transfer_in_unit_count_base = models.DecimalField(max_digits=14, decimal_places=3, default=0)
    transfer_out_unit_count_base = models.DecimalField(max_digits=14, decimal_places=3, default=0)
    increase_adjustment_unit_count_base = models.DecimalField(max_digits=14, decimal_places=3, default=0)
    decrease_adjustment_unit_count_base = models.DecimalField(max_digits=14, decimal_places=3, default=0)

    class Meta:
        unique_together = (("itemlot", "location", "inventory_state", "stockledger", "uom"),)
        db_table = "item_inv_journal_entry"

    def save(self, *args, **kwargs):
        rate = self.uom.conversion_rate if self.uom_id else 1
        self.qty = self.uom_qty * rate
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.itemlot} {self.uom_qty}×{self.uom} @ {self.location}"


# ===========================================================================
# Reorder rules & alerts
# ===========================================================================

class ReorderRule(createdtimestamp_uid, activearchlockedMixin):
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name="reorder_rules")
    branch = models.ForeignKey(
        "department.Branch", on_delete=models.CASCADE, related_name="reorder_rules"
    )
    min_qty = models.DecimalField(max_digits=14, decimal_places=3, default=0)
    max_qty = models.DecimalField(max_digits=14, decimal_places=3, default=0)
    reorder_qty = models.DecimalField(max_digits=14, decimal_places=3, default=0)

    class Meta:
        unique_together = (("item", "branch"),)

    def __str__(self):
        return f"Reorder: {self.item.name} @ {self.branch}"


class StockAlert(createdtimestamp_uid, activearchlockedMixin):
    class AlertType(models.TextChoices):
        STOCKOUT = "stockout", "Stockout"
        LOW_STOCK = "low_stock", "Low Stock"
        EXPIRY = "expiry", "Expiry"
        OVERSTOCK = "overstock", "Overstock"

    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name="alerts")
    branch = models.ForeignKey(
        "department.Branch", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="stock_alerts",
    )
    alert_type = models.CharField(max_length=30, choices=AlertType.choices)
    message = models.CharField(max_length=300)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "stock_alert"

    def __str__(self):
        return f"{self.alert_type}: {self.item.name}"


# ===========================================================================
# Signals
# ===========================================================================

@receiver(post_save, sender=Item)
def create_item_account(sender, instance, created, **kwargs):
    """Auto-creates an inventory Account for every new Item."""
    if not created or instance.account_id:
        return
    try:
        inventory_coa = Charts_of_account.objects.get(
            account_type="Assets", name__icontains="Inventory"
        )
    except Charts_of_account.DoesNotExist:
        return
    content_type = ContentType.objects.get_for_model(instance)
    account, _ = Account.objects.get_or_create(
        accounttype=inventory_coa,
        content_type=content_type,
        object_id=instance.pk,
        defaults={"name": f"Inventory – {instance.name}"},
    )
    Item.objects.filter(pk=instance.pk).update(account=account)


def _refresh_reorder_alerts(item, branch):
    """Check current stock vs ReorderRule and create StockAlert if needed."""
    rule = ReorderRule.objects.filter(item=item, branch=branch, is_active=True).first()
    if rule is None:
        return

    total = ItemInventoryLot.objects.filter(
        item=item,
        location=branch,
        is_active=True,
        inventory_state=ItemInventoryLot.InventoryState.ON_HAND,
    ).aggregate(total=Sum("qty"))["total"] or 0

    if total <= 0:
        StockAlert.objects.get_or_create(
            item=item,
            branch=branch,
            alert_type=StockAlert.AlertType.STOCKOUT,
            defaults={"message": f"Stockout: {item.name} @ {branch.name}"},
        )
    elif total < rule.min_qty:
        StockAlert.objects.get_or_create(
            item=item,
            branch=branch,
            alert_type=StockAlert.AlertType.LOW_STOCK,
            defaults={"message": f"Low stock: {item.name} @ {branch.name}. Qty={total}"},
        )


@receiver(post_save, sender=itemInvJournalEntry)
def update_itemlotinventory(sender, instance, created, **kwargs):
    """
    On new itemInvJournalEntry, update ItemInventoryLot.qty and refresh alerts.
    Raises ValidationError if Decrease would result in negative stock.
    """
    if not created:
        return

    lot_entry, _ = ItemInventoryLot.objects.get_or_create(
        itemlot=instance.itemlot,
        location=instance.location,
        inventory_state=instance.inventory_state,
        defaults={"item": instance.itemlot.item},
    )

    if instance.stockledger.inventorytransacttype == StockLedgerEntry.TransactType.INCREASE:
        lot_entry.qty += instance.qty
    else:  # DECREASE
        if lot_entry.qty < instance.qty:
            raise ValidationError(
                f"Insufficient stock for {instance.itemlot} at {instance.location}. "
                f"Available: {lot_entry.qty}, Requested: {instance.qty}"
            )
        lot_entry.qty -= instance.qty

    lot_entry.save()
    _refresh_reorder_alerts(instance.itemlot.item, instance.location)
