"""
apps/ecommerce/models.py

Online store / e-commerce module for the ERP.

Covers:
  - Store configuration
  - Shopping cart & cart items
  - Wishlists
  - Coupons & discount codes
  - Product reviews & ratings
  - E-commerce orders (separate from B2B SalesOrder)
  - Online order fulfilment
"""

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from djmoney.models.fields import MoneyField

from apps.common.models import TenantAwareModel, DEFAULT_CURRENCY, CURRENCY_CHOICES


# ─────────────────────────────────────────────────────────────────────────────
# Store
# ─────────────────────────────────────────────────────────────────────────────

class Store(TenantAwareModel):
    """
    Online store configuration.
    Multiple departments can have their own store front within the same tenant.
    """
    name = models.CharField(_("Store Name"), max_length=100, unique=True)
    slug = models.SlugField(_("Slug"), max_length=100, unique=True)
    department = models.OneToOneField(
        "department.Department", on_delete=models.PROTECT, related_name="ecom_store"
    )
    description = models.TextField(blank=True)
    logo = models.ImageField(upload_to="store_logos/", null=True, blank=True)
    banner = models.ImageField(upload_to="store_banners/", null=True, blank=True)
    primary_color = models.CharField(_("Primary Color"), max_length=7, default="#2563EB")
    currency = models.CharField(_("Store Currency"), max_length=3, default=DEFAULT_CURRENCY, choices=CURRENCY_CHOICES)
    is_open = models.BooleanField(_("Store Open?"), default=True)
    meta_title = models.CharField(_("SEO Title"), max_length=70, blank=True)
    meta_description = models.CharField(_("SEO Description"), max_length=160, blank=True)
    allowed_countries = models.ManyToManyField(
        "contact.Country", blank=True, verbose_name=_("Ships To"), related_name="ecom_stores"
    )
    default_pricelist = models.ForeignKey(
        "inventory.Pricelist", on_delete=models.SET_NULL, null=True, blank=True, related_name="ecom_stores"
    )

    class Meta:
        verbose_name = _("E-Commerce Store")
        verbose_name_plural = _("E-Commerce Stores")
        ordering = ["name"]

    def __str__(self):
        return self.name


class StoreCategory(TenantAwareModel):
    """Storefront category (may differ from inventory ProductCategory)."""
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="store_categories")
    name = models.CharField(_("Category Name"), max_length=100)
    slug = models.SlugField(max_length=100)
    parent = models.ForeignKey("self", on_delete=models.SET_NULL, null=True, blank=True, related_name="subcategories")
    product_category = models.ForeignKey(
        "inventory.ProductCategory", on_delete=models.SET_NULL, null=True, blank=True, related_name="store_categories"
    )
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to="store_categories/", null=True, blank=True)
    order = models.PositiveSmallIntegerField(default=0)
    is_visible = models.BooleanField(default=True)

    class Meta:
        verbose_name = _("Store Category")
        verbose_name_plural = _("Store Categories")
        unique_together = ("store", "slug")
        ordering = ["store", "order", "name"]

    def __str__(self):
        return f"{self.store.name} / {self.name}"


# ─────────────────────────────────────────────────────────────────────────────
# Cart
# ─────────────────────────────────────────────────────────────────────────────

class Cart(TenantAwareModel):
    """
    Persistent shopping cart.  Can belong to a logged-in client or
    a session-identified anonymous visitor.
    """
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="carts")
    client = models.ForeignKey(
        "party.ClientProfile", on_delete=models.SET_NULL, null=True, blank=True, related_name="carts"
    )
    session_key = models.CharField(_("Session Key"), max_length=100, blank=True)
    applied_coupon = models.ForeignKey(
        "Coupon", on_delete=models.SET_NULL, null=True, blank=True, related_name="applied_carts"
    )
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = _("Cart")
        verbose_name_plural = _("Carts")
        ordering = ["-updated_at"]

    def __str__(self):
        return f"Cart {self.id} ({self.client or self.session_key})"

    @property
    def subtotal(self):
        from djmoney.money import Money
        total = Money(0, DEFAULT_CURRENCY)
        for item in self.items.all():
            total += item.line_total
        return total


class CartItem(TenantAwareModel):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    variant = models.ForeignKey("inventory.ProductVariant", on_delete=models.PROTECT, related_name="cart_items")
    quantity = models.PositiveIntegerField(_("Quantity"), default=1)
    unit_price = MoneyField(
        _("Unit Price at Add Time"), max_digits=20, decimal_places=2,
        default=0, default_currency=DEFAULT_CURRENCY, currency_choices=CURRENCY_CHOICES
    )

    class Meta:
        verbose_name = _("Cart Item")
        verbose_name_plural = _("Cart Items")
        unique_together = ("cart", "variant")

    def __str__(self):
        return f"{self.cart} — {self.variant} x {self.quantity}"

    @property
    def line_total(self):
        return self.unit_price * self.quantity


# ─────────────────────────────────────────────────────────────────────────────
# Wishlist
# ─────────────────────────────────────────────────────────────────────────────

class Wishlist(TenantAwareModel):
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="wishlists")
    client = models.ForeignKey("party.ClientProfile", on_delete=models.CASCADE, related_name="wishlists")
    name = models.CharField(_("List Name"), max_length=100, default=_("My Wishlist"))
    is_public = models.BooleanField(_("Public?"), default=False)

    class Meta:
        verbose_name = _("Wishlist")
        verbose_name_plural = _("Wishlists")
        unique_together = ("client", "name")

    def __str__(self):
        return f"{self.client} — {self.name}"


class WishlistItem(TenantAwareModel):
    wishlist = models.ForeignKey(Wishlist, on_delete=models.CASCADE, related_name="items")
    variant = models.ForeignKey("inventory.ProductVariant", on_delete=models.PROTECT, related_name="wishlist_items")
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Wishlist Item")
        verbose_name_plural = _("Wishlist Items")
        unique_together = ("wishlist", "variant")

    def __str__(self):
        return f"{self.wishlist} — {self.variant}"


# ─────────────────────────────────────────────────────────────────────────────
# Coupons
# ─────────────────────────────────────────────────────────────────────────────

class Coupon(TenantAwareModel):
    DISCOUNT_TYPE_CHOICES = [
        ("percent", _("Percentage Off")),
        ("fixed", _("Fixed Amount Off")),
        ("free_shipping", _("Free Shipping")),
    ]

    code = models.CharField(_("Coupon Code"), max_length=30, unique=True)
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="coupons")
    discount_type = models.CharField(_("Discount Type"), max_length=20, choices=DISCOUNT_TYPE_CHOICES)
    discount_value = models.DecimalField(_("Discount Value"), max_digits=10, decimal_places=2, default=0)
    min_order_amount = MoneyField(
        _("Minimum Order Amount"), max_digits=20, decimal_places=2,
        null=True, blank=True, default_currency=DEFAULT_CURRENCY, currency_choices=CURRENCY_CHOICES
    )
    max_discount_amount = MoneyField(
        _("Maximum Discount Amount"), max_digits=20, decimal_places=2,
        null=True, blank=True, default_currency=DEFAULT_CURRENCY, currency_choices=CURRENCY_CHOICES
    )
    valid_from = models.DateTimeField(_("Valid From"), null=True, blank=True)
    valid_to = models.DateTimeField(_("Valid To"), null=True, blank=True)
    usage_limit = models.PositiveIntegerField(_("Total Usage Limit"), null=True, blank=True)
    usage_limit_per_client = models.PositiveIntegerField(_("Use Limit per Client"), default=1)
    times_used = models.PositiveIntegerField(_("Times Used"), default=0, editable=False)

    class Meta:
        verbose_name = _("Coupon")
        verbose_name_plural = _("Coupons")
        ordering = ["code"]

    def __str__(self):
        return self.code

    @property
    def is_valid(self):
        now = timezone.now()
        if self.valid_from and now < self.valid_from:
            return False
        if self.valid_to and now > self.valid_to:
            return False
        if self.usage_limit and self.times_used >= self.usage_limit:
            return False
        return True


class CouponUsage(TenantAwareModel):
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE, related_name="usages")
    client = models.ForeignKey("party.ClientProfile", on_delete=models.CASCADE, related_name="coupon_usages")
    order = models.ForeignKey("EcomOrder", on_delete=models.CASCADE, related_name="coupon_usages")
    used_at = models.DateTimeField(auto_now_add=True)
    discount_applied = MoneyField(
        _("Discount Applied"), max_digits=20, decimal_places=2,
        default=0, default_currency=DEFAULT_CURRENCY, currency_choices=CURRENCY_CHOICES
    )

    class Meta:
        verbose_name = _("Coupon Usage")
        verbose_name_plural = _("Coupon Usages")
        unique_together = ("coupon", "order")

    def __str__(self):
        return f"{self.coupon.code} used by {self.client}"


# ─────────────────────────────────────────────────────────────────────────────
# Product Review
# ─────────────────────────────────────────────────────────────────────────────

class ProductReview(TenantAwareModel):
    STATUS_CHOICES = [
        ("pending", _("Pending Moderation")),
        ("approved", _("Approved")),
        ("rejected", _("Rejected")),
    ]

    product = models.ForeignKey("inventory.Product", on_delete=models.CASCADE, related_name="reviews")
    variant = models.ForeignKey(
        "inventory.ProductVariant", on_delete=models.SET_NULL, null=True, blank=True, related_name="reviews"
    )
    client = models.ForeignKey("party.ClientProfile", on_delete=models.CASCADE, related_name="product_reviews")
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="reviews")
    rating = models.PositiveSmallIntegerField(
        _("Rating"), validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    title = models.CharField(_("Review Title"), max_length=100, blank=True)
    body = models.TextField(_("Review Body"))
    status = models.CharField(_("Status"), max_length=20, choices=STATUS_CHOICES, default="pending")
    is_verified_purchase = models.BooleanField(_("Verified Purchase?"), default=False)

    class Meta:
        verbose_name = _("Product Review")
        verbose_name_plural = _("Product Reviews")
        unique_together = ("product", "client")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.product.name} — {self.rating}★ by {self.client}"


# ─────────────────────────────────────────────────────────────────────────────
# E-Commerce Order
# ─────────────────────────────────────────────────────────────────────────────

class EcomOrder(TenantAwareModel):
    STATUS_CHOICES = [
        ("pending_payment", _("Pending Payment")),
        ("payment_received", _("Payment Received")),
        ("processing", _("Processing")),
        ("shipped", _("Shipped")),
        ("delivered", _("Delivered")),
        ("cancelled", _("Cancelled")),
        ("refunded", _("Refunded")),
        ("failed", _("Failed")),
    ]

    order_number = models.CharField(_("Order Number"), max_length=50, unique=True)
    store = models.ForeignKey(Store, on_delete=models.PROTECT, related_name="ecom_orders")
    client = models.ForeignKey(
        "party.ClientProfile", on_delete=models.SET_NULL, null=True, blank=True, related_name="ecom_orders"
    )
    guest_email = models.EmailField(_("Guest Email"), blank=True)
    status = models.CharField(_("Status"), max_length=25, choices=STATUS_CHOICES, default="pending_payment")
    # Shipping address (denormalised for immutability)
    ship_to_name = models.CharField(_("Ship To Name"), max_length=200, blank=True)
    ship_to_line1 = models.CharField(_("Address Line 1"), max_length=255, blank=True)
    ship_to_line2 = models.CharField(_("Address Line 2"), max_length=255, blank=True)
    ship_to_city = models.ForeignKey(
        "contact.City", on_delete=models.SET_NULL, null=True, blank=True, related_name="ecom_orders"
    )
    ship_to_postal = models.CharField(_("Postal Code"), max_length=20, blank=True)
    ship_to_country = models.ForeignKey(
        "contact.Country", on_delete=models.SET_NULL, null=True, blank=True, related_name="ecom_orders"
    )
    pricelist = models.ForeignKey(
        "inventory.Pricelist", on_delete=models.SET_NULL, null=True, blank=True, related_name="ecom_orders"
    )
    coupon = models.ForeignKey(
        Coupon, on_delete=models.SET_NULL, null=True, blank=True, related_name="ecom_orders"
    )
    subtotal = MoneyField(
        _("Subtotal"), max_digits=20, decimal_places=2,
        default=0, default_currency=DEFAULT_CURRENCY, currency_choices=CURRENCY_CHOICES
    )
    shipping_cost = MoneyField(
        _("Shipping Cost"), max_digits=20, decimal_places=2,
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
    invoice = models.OneToOneField(
        "accounting.Invoice", on_delete=models.SET_NULL, null=True, blank=True, related_name="ecom_order"
    )
    # Converted to internal Sales Order after payment
    sales_order = models.OneToOneField(
        "sales.SalesOrder", on_delete=models.SET_NULL, null=True, blank=True, related_name="ecom_order"
    )
    placed_at = models.DateTimeField(_("Placed At"), default=timezone.now)
    notes = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(_("Client IP"), null=True, blank=True)

    class Meta:
        verbose_name = _("E-Commerce Order")
        verbose_name_plural = _("E-Commerce Orders")
        ordering = ["-placed_at"]

    def __str__(self):
        return f"ECOM-{self.order_number}"


class EcomOrderLine(TenantAwareModel):
    order = models.ForeignKey(EcomOrder, on_delete=models.CASCADE, related_name="lines")
    variant = models.ForeignKey("inventory.ProductVariant", on_delete=models.PROTECT, related_name="ecom_order_lines")
    quantity = models.PositiveIntegerField(_("Quantity"))
    unit_price = MoneyField(
        _("Unit Price"), max_digits=20, decimal_places=2,
        default=0, default_currency=DEFAULT_CURRENCY, currency_choices=CURRENCY_CHOICES
    )
    discount_percent = models.DecimalField(_("Discount %"), max_digits=5, decimal_places=2, default=0)
    line_total = MoneyField(
        _("Line Total"), max_digits=20, decimal_places=2,
        default=0, default_currency=DEFAULT_CURRENCY, currency_choices=CURRENCY_CHOICES, editable=False
    )

    class Meta:
        verbose_name = _("E-Com Order Line")
        verbose_name_plural = _("E-Com Order Lines")

    def save(self, *args, **kwargs):
        from decimal import Decimal
        self.line_total = self.unit_price * self.quantity * (1 - self.discount_percent / Decimal("100"))
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.order} — {self.variant} x {self.quantity}"


# ─────────────────────────────────────────────────────────────────────────────
# Payment Record (online gateway)
# ─────────────────────────────────────────────────────────────────────────────

class EcomPayment(TenantAwareModel):
    STATUS_CHOICES = [
        ("pending", _("Pending")),
        ("success", _("Success")),
        ("failed", _("Failed")),
        ("refunded", _("Refunded")),
    ]
    GATEWAY_CHOICES = [
        ("stripe", "Stripe"),
        ("paystack", "Paystack"),
        ("flutterwave", "Flutterwave"),
        ("braintree", "Braintree"),
        ("mobile_money", "Mobile Money"),
        ("other", "Other"),
    ]

    order = models.ForeignKey(EcomOrder, on_delete=models.CASCADE, related_name="ecom_payments")
    gateway = models.CharField(_("Payment Gateway"), max_length=20, choices=GATEWAY_CHOICES)
    gateway_reference = models.CharField(_("Gateway Reference"), max_length=200, blank=True)
    amount = MoneyField(
        _("Amount"), max_digits=20, decimal_places=2,
        default=0, default_currency=DEFAULT_CURRENCY, currency_choices=CURRENCY_CHOICES
    )
    status = models.CharField(_("Status"), max_length=20, choices=STATUS_CHOICES, default="pending")
    gateway_response = models.JSONField(_("Gateway Response"), default=dict, blank=True)
    paid_at = models.DateTimeField(_("Paid At"), null=True, blank=True)

    class Meta:
        verbose_name = _("E-Com Payment")
        verbose_name_plural = _("E-Com Payments")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.gateway}: {self.amount} ({self.status})"
