from apps.common.api import build_model_serializer
from apps.tenancy.models import Tenant, TenantDomain

TenantSerializer = build_model_serializer(Tenant)
TenantDomainSerializer = build_model_serializer(TenantDomain)
