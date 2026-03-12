from apps.common.api import build_model_serializer
from apps.company.models import BusinessType, Company, Domain, Industry, PaymentClass

IndustrySerializer = build_model_serializer(Industry)
PaymentClassSerializer = build_model_serializer(PaymentClass)
BusinessTypeSerializer = build_model_serializer(BusinessType)
CompanySerializer = build_model_serializer(Company, read_only_fields=("schema_name",))
DomainSerializer = build_model_serializer(Domain)
