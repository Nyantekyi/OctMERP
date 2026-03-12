"""
apps/ecommerce/serializers.py
"""
from rest_framework import serializers

from .models import (
    Store, StoreCategory, Cart, CartItem,
    Wishlist, WishlistItem, Coupon, CouponUsage,
    ProductReview, EcomOrder, EcomOrderLine, EcomPayment,
)


class StoreCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = StoreCategory
        fields = ["id", "store", "name", "slug", "parent", "product_category", "description", "image", "order", "is_visible", "is_active", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class StoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Store
        fields = [
            "id", "name", "slug", "department", "description", "logo", "banner",
            "primary_color", "currency", "is_open",
            "meta_title", "meta_description", "allowed_countries",
            "is_active", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class CartItemSerializer(serializers.ModelSerializer):
    line_total = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = ["id", "cart", "variant", "quantity", "unit_price", "unit_price_currency", "line_total", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_line_total(self, obj):
        t = obj.line_total
        return {"amount": str(t.amount), "currency": str(t.currency)}


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)

    class Meta:
        model = Cart
        fields = ["id", "store", "client", "session_key", "applied_coupon", "notes", "items", "is_active", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class WishlistItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = WishlistItem
        fields = ["id", "wishlist", "variant", "added_at", "created_at", "updated_at"]
        read_only_fields = ["id", "added_at", "created_at", "updated_at"]


class WishlistSerializer(serializers.ModelSerializer):
    items = WishlistItemSerializer(many=True, read_only=True)

    class Meta:
        model = Wishlist
        fields = ["id", "store", "client", "name", "is_public", "items", "is_active", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class CouponSerializer(serializers.ModelSerializer):
    is_valid = serializers.SerializerMethodField()

    class Meta:
        model = Coupon
        fields = [
            "id", "code", "store", "discount_type", "discount_value",
            "min_order_amount", "min_order_amount_currency",
            "max_discount_amount", "max_discount_amount_currency",
            "valid_from", "valid_to", "usage_limit", "usage_limit_per_client",
            "times_used", "is_valid", "is_active", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "times_used", "created_at", "updated_at"]

    def get_is_valid(self, obj):
        return obj.is_valid


class CouponUsageSerializer(serializers.ModelSerializer):
    class Meta:
        model = CouponUsage
        fields = ["id", "coupon", "client", "order", "used_at", "discount_applied", "discount_applied_currency", "created_at", "updated_at"]
        read_only_fields = ["id", "used_at", "created_at", "updated_at"]


class ProductReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductReview
        fields = [
            "id", "product", "variant", "client", "store",
            "rating", "title", "body", "status", "is_verified_purchase",
            "is_active", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class EcomOrderLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = EcomOrderLine
        fields = ["id", "order", "variant", "quantity", "unit_price", "unit_price_currency", "discount_percent", "line_total", "line_total_currency", "created_at", "updated_at"]
        read_only_fields = ["id", "line_total", "created_at", "updated_at"]


class EcomPaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = EcomPayment
        fields = ["id", "order", "gateway", "gateway_reference", "amount", "amount_currency", "status", "gateway_response", "paid_at", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class EcomOrderSerializer(serializers.ModelSerializer):
    lines = EcomOrderLineSerializer(many=True, read_only=True)
    ecom_payments = EcomPaymentSerializer(many=True, read_only=True)

    class Meta:
        model = EcomOrder
        fields = [
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
        ]
        read_only_fields = ["id", "order_number", "created_at", "updated_at"]
