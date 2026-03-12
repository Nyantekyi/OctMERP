from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    SalesQuotationViewSet, SalesQuotationLineViewSet,
    SalesOrderViewSet, SalesOrderLineViewSet,
    DeliveryViewSet, DeliveryLineViewSet,
    SalesReturnViewSet, SalesReturnLineViewSet,
    CommissionRuleViewSet, CommissionRecordViewSet,
)

app_name = "sales"

router = DefaultRouter()
router.register("quotations", SalesQuotationViewSet, basename="quotation")
router.register("quotation-lines", SalesQuotationLineViewSet, basename="quotation-line")
router.register("orders", SalesOrderViewSet, basename="sales-order")
router.register("order-lines", SalesOrderLineViewSet, basename="so-line")
router.register("deliveries", DeliveryViewSet, basename="delivery")
router.register("delivery-lines", DeliveryLineViewSet, basename="delivery-line")
router.register("returns", SalesReturnViewSet, basename="sales-return")
router.register("return-lines", SalesReturnLineViewSet, basename="return-line")
router.register("commission-rules", CommissionRuleViewSet, basename="commission-rule")
router.register("commissions", CommissionRecordViewSet, basename="commission-record")

urlpatterns = [path("", include(router.urls))]

