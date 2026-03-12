from apps.common.api import build_model_viewset
from apps.company.api.serializers import BusinessTypeSerializer, CompanySerializer, DomainSerializer, IndustrySerializer, PaymentClassSerializer
from apps.company.models import BusinessType, Company, Domain, Industry, PaymentClass

IndustryViewSet = build_model_viewset(Industry, IndustrySerializer, search_fields=("name",))
PaymentClassViewSet = build_model_viewset(PaymentClass, PaymentClassSerializer, search_fields=("name",))
BusinessTypeViewSet = build_model_viewset(BusinessType, BusinessTypeSerializer, search_fields=("name",))
CompanyViewSet = build_model_viewset(Company, CompanySerializer, search_fields=("name", "slug"), filterset_fields=("industry", "payment", "business_type"))
DomainViewSet = build_model_viewset(Domain, DomainSerializer, search_fields=("domain",), filterset_fields=("company", "is_primary"))
