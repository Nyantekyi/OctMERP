"""apps/ecommerce/serializers.py"""

from apps.common.api import build_model_serializer

from .models import (
    Cart,
    CartItem,
    Coupon,
    CouponUsage,
    EcomOrder,
    EcomOrderLine,
    EcomPayment,
    ProductReview,
    Store,
    StoreCategory,
    Wishlist,
    WishlistItem,
)


def _cart_item_to_representation(serializer, instance, representation):
    total = instance.line_total
    representation["line_total"] = {"amount": str(total.amount), "currency": str(total.currency)}
    return representation


def _coupon_to_representation(serializer, instance, representation):
    representation["is_valid"] = instance.is_valid
    return representation


StoreCategorySerializer = build_model_serializer(
    StoreCategory,
    fields=["id", "store", "name", "slug", "parent", "product_category", "description", "image", "order", "is_visible", "is_active", "created_at", "updated_at"],
)
StoreSerializer = build_model_serializer(
    Store,
    fields=[
        "id", "name", "slug", "department", "description", "logo", "banner",
        "primary_color", "currency", "is_open",
        "meta_title", "meta_description", "allowed_countries",
        "is_active", "created_at", "updated_at",
    ],
)
CartItemSerializer = build_model_serializer(
    CartItem,
    fields=["id", "cart", "variant", "quantity", "unit_price", "unit_price_currency", "line_total", "created_at", "updated_at"],
    to_representation_handler=_cart_item_to_representation,
)
CartSerializer = build_model_serializer(
    Cart,
    fields=["id", "store", "client", "session_key", "applied_coupon", "notes", "items", "is_active", "created_at", "updated_at"],
    nested_serializers={"items": {"serializer": CartItemSerializer, "many": True, "read_only": True, "required": False}},
)
WishlistItemSerializer = build_model_serializer(
    WishlistItem,
    fields=["id", "wishlist", "variant", "added_at", "created_at", "updated_at"],
    read_only_fields=("added_at",),
)
WishlistSerializer = build_model_serializer(
    Wishlist,
    fields=["id", "store", "client", "name", "is_public", "items", "is_active", "created_at", "updated_at"],
    nested_serializers={"items": {"serializer": WishlistItemSerializer, "many": True, "read_only": True, "required": False}},
)
CouponSerializer = build_model_serializer(
    Coupon,
    fields=[
        "id", "code", "store", "discount_type", "discount_value",
        "min_order_amount", "min_order_amount_currency",
        "max_discount_amount", "max_discount_amount_currency",
        "valid_from", "valid_to", "usage_limit", "usage_limit_per_client",
        "times_used", "is_valid", "is_active", "created_at", "updated_at",
    ],
    read_only_fields=("times_used",),
    to_representation_handler=_coupon_to_representation,
)
CouponUsageSerializer = build_model_serializer(
    CouponUsage,
    fields=["id", "coupon", "client", "order", "used_at", "discount_applied", "discount_applied_currency", "created_at", "updated_at"],
    read_only_fields=("used_at",),
)
ProductReviewSerializer = build_model_serializer(
    ProductReview,
    fields=[
        "id", "product", "variant", "client", "store",
        "rating", "title", "body", "status", "is_verified_purchase",
        "is_active", "created_at", "updated_at",
    ],
)
EcomOrderLineSerializer = build_model_serializer(
    EcomOrderLine,
    fields=["id", "order", "variant", "quantity", "unit_price", "unit_price_currency", "discount_percent", "line_total", "line_total_currency", "created_at", "updated_at"],
    read_only_fields=("line_total",),
)
EcomPaymentSerializer = build_model_serializer(
    EcomPayment,
    fields=["id", "order", "gateway", "gateway_reference", "amount", "amount_currency", "status", "gateway_response", "paid_at", "created_at", "updated_at"],
)
EcomOrderSerializer = build_model_serializer(
    EcomOrder,
    fields=[
        "id", "order_number", "store", "client", "guest_email", "status",
        "ship_to_name", "ship_to_line1", "ship_to_line2", "ship_to_city",
        "ship_to_postal", "ship_to_country",
        "coupon",
        "subtotal", "subtotal_currency",
        "shipping_cost", "shipping_cost_currency",
        "discount_amount", "discount_amount_currency",
        "tax_amount", "tax_amount_currency",
        "total_amount", "total_amount_currency",
        "invoice", "sales_order", "placed_at", "notes",
        "lines", "ecom_payments", "is_active", "created_at", "updated_at",
    ],
    read_only_fields=("order_number",),
    nested_serializers={
        "lines": {"serializer": EcomOrderLineSerializer, "many": True, "read_only": True, "required": False},
        "ecom_payments": {"serializer": EcomPaymentSerializer, "many": True, "read_only": True, "required": False},
    },
)
