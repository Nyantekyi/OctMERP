from apps.common.api import build_model_viewset
from apps.sales.api.serializers import DeliverySerializer, PriceListSerializer, QuotationLineSerializer, QuotationSerializer, SalesOrderLineSerializer, SalesOrderSerializer, SalesReturnSerializer, TenderRepositorySerializer
from apps.sales.models import Delivery, PriceList, Quotation, QuotationLine, SalesOrder, SalesOrderLine, SalesReturn, Tender_Repository

PriceListViewSet = build_model_viewset(PriceList, PriceListSerializer, search_fields=("name",), filterset_fields=("company", "is_default", "is_active"), soft_delete=True)
TenderRepositoryViewSet = build_model_viewset(Tender_Repository, TenderRepositorySerializer, search_fields=("name", "code"), filterset_fields=("company", "is_default", "is_active"), soft_delete=True)
QuotationViewSet = build_model_viewset(Quotation, QuotationSerializer, search_fields=("quote_number",), filterset_fields=("company", "status", "client", "prospect", "is_active"), prefetch_related_fields=("lines",), ordering_fields=("created_at", "quote_number"), soft_delete=True)
QuotationLineViewSet = build_model_viewset(QuotationLine, QuotationLineSerializer, filterset_fields=("quotation", "product", "variant"))
SalesOrderViewSet = build_model_viewset(SalesOrder, SalesOrderSerializer, search_fields=("order_number",), filterset_fields=("company", "status", "client", "branch", "is_active"), prefetch_related_fields=("lines",), ordering_fields=("ordered_on", "order_number"), soft_delete=True)
SalesOrderLineViewSet = build_model_viewset(SalesOrderLine, SalesOrderLineSerializer, filterset_fields=("order", "product", "variant"))
DeliveryViewSet = build_model_viewset(Delivery, DeliverySerializer, search_fields=("delivery_number",), filterset_fields=("sales_order", "status", "is_active"), soft_delete=True)
SalesReturnViewSet = build_model_viewset(SalesReturn, SalesReturnSerializer, filterset_fields=("sales_order", "client", "status", "is_active"), soft_delete=True)
