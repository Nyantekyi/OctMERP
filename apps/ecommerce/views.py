"""
apps/ecommerce/views.py
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.common.permissions import IsTenantUser, IsManager
from .models import (
    Store, StoreCategory, Cart, CartItem,
    Wishlist, WishlistItem, Coupon, CouponUsage,
    ProductReview, EcomOrder, EcomOrderLine, EcomPayment,
)
from .serializers import (
    StoreSerializer, StoreCategorySerializer,
    CartSerializer, CartItemSerializer,
    WishlistSerializer, WishlistItemSerializer,
    CouponSerializer, CouponUsageSerializer,
    ProductReviewSerializer,
    EcomOrderSerializer, EcomOrderLineSerializer, EcomPaymentSerializer,
)


class StoreViewSet(viewsets.ModelViewSet):
    queryset = Store.objects.select_related("department")
    serializer_class = StoreSerializer
    permission_classes = [IsTenantUser]
    search_fields = ["name", "slug"]
    filterset_fields = ["is_open", "is_active"]


class StoreCategoryViewSet(viewsets.ModelViewSet):
    queryset = StoreCategory.objects.select_related("store", "parent")
    serializer_class = StoreCategorySerializer
    permission_classes = [IsTenantUser]
    filterset_fields = ["store", "parent", "is_visible"]
    search_fields = ["name"]
    ordering_fields = ["order"]


class CartViewSet(viewsets.ModelViewSet):
    queryset = Cart.objects.select_related("store", "client").prefetch_related("items")
    serializer_class = CartSerializer
    permission_classes = [IsTenantUser]
    filterset_fields = ["store", "client"]

    @action(detail=True, methods=["post"])
    def clear(self, request, pk=None):
        cart = self.get_object()
        cart.items.all().delete()
        return Response({"success": True, "message": "Cart cleared."})


class CartItemViewSet(viewsets.ModelViewSet):
    queryset = CartItem.objects.select_related("cart", "variant")
    serializer_class = CartItemSerializer
    permission_classes = [IsTenantUser]
    filterset_fields = ["cart", "variant"]


class WishlistViewSet(viewsets.ModelViewSet):
    queryset = Wishlist.objects.select_related("store", "client").prefetch_related("items")
    serializer_class = WishlistSerializer
    permission_classes = [IsTenantUser]
    filterset_fields = ["store", "client", "is_public"]


class WishlistItemViewSet(viewsets.ModelViewSet):
    queryset = WishlistItem.objects.select_related("wishlist", "variant")
    serializer_class = WishlistItemSerializer
    permission_classes = [IsTenantUser]
    filterset_fields = ["wishlist", "variant"]


class CouponViewSet(viewsets.ModelViewSet):
    queryset = Coupon.objects.select_related("store")
    serializer_class = CouponSerializer
    permission_classes = [IsTenantUser]
    filterset_fields = ["store", "discount_type", "is_active"]
    search_fields = ["code"]


class CouponUsageViewSet(viewsets.ModelViewSet):
    queryset = CouponUsage.objects.select_related("coupon", "client", "order")
    serializer_class = CouponUsageSerializer
    permission_classes = [IsTenantUser]
    filterset_fields = ["coupon", "client", "order"]


class ProductReviewViewSet(viewsets.ModelViewSet):
    queryset = ProductReview.objects.select_related("product", "client", "store")
    serializer_class = ProductReviewSerializer
    permission_classes = [IsTenantUser]
    filterset_fields = ["product", "client", "store", "status", "rating"]
    ordering_fields = ["created_at", "rating"]

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        review = self.get_object()
        review.status = "approved"
        review.save()
        return Response({"success": True, "data": ProductReviewSerializer(review).data})

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        review = self.get_object()
        review.status = "rejected"
        review.save()
        return Response({"success": True, "data": ProductReviewSerializer(review).data})


class EcomOrderViewSet(viewsets.ModelViewSet):
    queryset = EcomOrder.objects.select_related("store", "client").prefetch_related("lines", "ecom_payments")
    serializer_class = EcomOrderSerializer
    permission_classes = [IsTenantUser]
    filterset_fields = ["status", "store", "client"]
    search_fields = ["order_number"]
    ordering_fields = ["placed_at"]

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        order = self.get_object()
        order.status = "cancelled"
        order.save()
        return Response({"success": True, "data": EcomOrderSerializer(order).data})


class EcomOrderLineViewSet(viewsets.ModelViewSet):
    queryset = EcomOrderLine.objects.select_related("order", "variant")
    serializer_class = EcomOrderLineSerializer
    permission_classes = [IsTenantUser]
    filterset_fields = ["order"]


class EcomPaymentViewSet(viewsets.ModelViewSet):
    queryset = EcomPayment.objects.select_related("order")
    serializer_class = EcomPaymentSerializer
    permission_classes = [IsTenantUser]
    filterset_fields = ["order", "gateway", "status"]
    ordering_fields = ["created_at"]
