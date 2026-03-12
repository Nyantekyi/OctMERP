from apps.common.api import build_model_serializer
from apps.sales.models import Delivery, PriceList, Quotation, QuotationLine, SalesOrder, SalesOrderLine, SalesReturn, Tender_Repository

QuotationLineSerializer = build_model_serializer(QuotationLine, read_only_fields=("line_total",))
SalesOrderLineSerializer = build_model_serializer(SalesOrderLine, read_only_fields=("line_total",))

PriceListSerializer = build_model_serializer(PriceList)
TenderRepositorySerializer = build_model_serializer(Tender_Repository)
QuotationSerializer = build_model_serializer(
    Quotation,
    nested_serializers={
        "lines": {
            "serializer": QuotationLineSerializer,
            "many": True,
            "required": False,
        }
    },
)
SalesOrderSerializer = build_model_serializer(
    SalesOrder,
    nested_serializers={
        "lines": {
            "serializer": SalesOrderLineSerializer,
            "many": True,
            "required": False,
        }
    },
)
DeliverySerializer = build_model_serializer(Delivery)
SalesReturnSerializer = build_model_serializer(SalesReturn)
