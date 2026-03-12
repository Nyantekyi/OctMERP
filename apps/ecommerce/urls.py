from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    StoreViewSet, StoreCategoryViewSet,
    CartViewSet, CartItemViewSet,
    WishlistViewSet, WishlistItemViewSet,
    CouponViewSet, CouponUsageViewSet,
    ProductReviewViewSet,
    EcomOrderViewSet, EcomOrderLineViewSet, EcomPaymentViewSet,
)

app_name = "ecommerce"

router = DefaultRouter()
router.register("stores", StoreViewSet, basename="store")
router.register("store-categories", StoreCategoryViewSet, basename="store-category")
router.register("carts", CartViewSet, basename="cart")
router.register("cart-items", CartItemViewSet, basename="cart-item")
router.register("wishlists", WishlistViewSet, basename="wishlist")
router.register("wishlist-items", WishlistItemViewSet, basename="wishlist-item")
router.register("coupons", CouponViewSet, basename="coupon")
router.register("coupon-usages", CouponUsageViewSet, basename="coupon-usage")
router.register("reviews", ProductReviewViewSet, basename="product-review")
router.register("orders", EcomOrderViewSet, basename="ecom-order")
router.register("order-lines", EcomOrderLineViewSet, basename="ecom-order-line")
router.register("payments", EcomPaymentViewSet, basename="ecom-payment")

urlpatterns = [path("", include(router.urls))]

