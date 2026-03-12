from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    POSConfigViewSet, POSSessionViewSet, POSOrderViewSet,
    POSOrderLineViewSet, POSPaymentViewSet, CashDrawerEventViewSet,
)

app_name = "pos"

router = DefaultRouter()
router.register("configs", POSConfigViewSet, basename="pos-config")
router.register("sessions", POSSessionViewSet, basename="pos-session")
router.register("orders", POSOrderViewSet, basename="pos-order")
router.register("order-lines", POSOrderLineViewSet, basename="pos-order-line")
router.register("payments", POSPaymentViewSet, basename="pos-payment")
router.register("cash-events", CashDrawerEventViewSet, basename="cash-event")

urlpatterns = [path("", include(router.urls))]

