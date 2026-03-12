from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.sales.api.views import DeliveryViewSet, PriceListViewSet, QuotationLineViewSet, QuotationViewSet, SalesOrderLineViewSet, SalesOrderViewSet, SalesReturnViewSet, TenderRepositoryViewSet

router = DefaultRouter()
router.register("price-lists", PriceListViewSet, basename="sales-price-list")
router.register("tender-repository", TenderRepositoryViewSet, basename="sales-tender-repository")
router.register("quotations", QuotationViewSet, basename="sales-quotation")
router.register("quotation-lines", QuotationLineViewSet, basename="sales-quotation-line")
router.register("orders", SalesOrderViewSet, basename="sales-order")
router.register("order-lines", SalesOrderLineViewSet, basename="sales-order-line")
router.register("deliveries", DeliveryViewSet, basename="sales-delivery")
router.register("returns", SalesReturnViewSet, basename="sales-return")

urlpatterns = [path("", include(router.urls))]
