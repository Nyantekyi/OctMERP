"""apps/ecommerce/views.py"""

from rest_framework.response import Response

from apps.common.api import build_action_route, build_model_viewset
from apps.common.permissions import IsTenantUser
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
from .serializers import (
    CartItemSerializer,
    CartSerializer,
    CouponSerializer,
    CouponUsageSerializer,
    EcomOrderLineSerializer,
    EcomOrderSerializer,
    EcomPaymentSerializer,
    ProductReviewSerializer,
    StoreCategorySerializer,
    StoreSerializer,
    WishlistItemSerializer,
    WishlistSerializer,
)


def _clear_cart(self, request, *args, **kwargs):
    cart = self.get_object()
    cart.items.all().delete()
    return Response({"success": True, "message": "Cart cleared."})


def _approve_product_review(self, request, *args, **kwargs):
    review = self.get_object()
    review.status = "approved"
    review.save(update_fields=["status", "updated_at"])
    return Response({"success": True, "data": ProductReviewSerializer(review).data})


def _reject_product_review(self, request, *args, **kwargs):
    review = self.get_object()
    review.status = "rejected"
    review.save(update_fields=["status", "updated_at"])
    return Response({"success": True, "data": ProductReviewSerializer(review).data})


def _cancel_ecom_order(self, request, *args, **kwargs):
    order = self.get_object()
    order.status = "cancelled"
    order.save(update_fields=["status", "updated_at"])
    return Response({"success": True, "data": EcomOrderSerializer(order).data})


StoreViewSet = build_model_viewset(
    Store,
    StoreSerializer,
    permission_classes=[IsTenantUser],
    search_fields=["name", "slug"],
    filterset_fields=["is_open", "is_active"],
    select_related_fields=["department"],
)

StoreCategoryViewSet = build_model_viewset(
    StoreCategory,
    StoreCategorySerializer,
    permission_classes=[IsTenantUser],
    filterset_fields=["store", "parent", "is_visible"],
    search_fields=["name"],
    ordering_fields=["order"],
    select_related_fields=["store", "parent"],
)

CartViewSet = build_model_viewset(
    Cart,
    CartSerializer,
    permission_classes=[IsTenantUser],
    filterset_fields=["store", "client"],
    select_related_fields=["store", "client"],
    prefetch_related_fields=["items"],
    extra_routes={"clear": build_action_route("clear", _clear_cart, methods=("post",), detail=True)},
)

CartItemViewSet = build_model_viewset(
    CartItem,
    CartItemSerializer,
    permission_classes=[IsTenantUser],
    filterset_fields=["cart", "variant"],
    select_related_fields=["cart", "variant"],
)

WishlistViewSet = build_model_viewset(
    Wishlist,
    WishlistSerializer,
    permission_classes=[IsTenantUser],
    filterset_fields=["store", "client", "is_public"],
    select_related_fields=["store", "client"],
    prefetch_related_fields=["items"],
)

WishlistItemViewSet = build_model_viewset(
    WishlistItem,
    WishlistItemSerializer,
    permission_classes=[IsTenantUser],
    filterset_fields=["wishlist", "variant"],
    select_related_fields=["wishlist", "variant"],
)

CouponViewSet = build_model_viewset(
    Coupon,
    CouponSerializer,
    permission_classes=[IsTenantUser],
    filterset_fields=["store", "discount_type", "is_active"],
    search_fields=["code"],
    select_related_fields=["store"],
)

CouponUsageViewSet = build_model_viewset(
    CouponUsage,
    CouponUsageSerializer,
    permission_classes=[IsTenantUser],
    filterset_fields=["coupon", "client", "order"],
    select_related_fields=["coupon", "client", "order"],
)

ProductReviewViewSet = build_model_viewset(
    ProductReview,
    ProductReviewSerializer,
    permission_classes=[IsTenantUser],
    filterset_fields=["product", "client", "store", "status", "rating"],
    ordering_fields=["created_at", "rating"],
    select_related_fields=["product", "client", "store"],
    extra_routes={
        "approve": build_action_route("approve", _approve_product_review, methods=("post",), detail=True),
        "reject": build_action_route("reject", _reject_product_review, methods=("post",), detail=True),
    },
)

EcomOrderViewSet = build_model_viewset(
    EcomOrder,
    EcomOrderSerializer,
    permission_classes=[IsTenantUser],
    filterset_fields=["status", "store", "client"],
    search_fields=["order_number"],
    ordering_fields=["placed_at"],
    select_related_fields=["store", "client"],
    prefetch_related_fields=["lines", "ecom_payments"],
    extra_routes={"cancel": build_action_route("cancel", _cancel_ecom_order, methods=("post",), detail=True)},
)

EcomOrderLineViewSet = build_model_viewset(
    EcomOrderLine,
    EcomOrderLineSerializer,
    permission_classes=[IsTenantUser],
    filterset_fields=["order"],
    select_related_fields=["order", "variant"],
)

EcomPaymentViewSet = build_model_viewset(
    EcomPayment,
    EcomPaymentSerializer,
    permission_classes=[IsTenantUser],
    filterset_fields=["order", "gateway", "status"],
    ordering_fields=["created_at"],
    select_related_fields=["order"],
)
