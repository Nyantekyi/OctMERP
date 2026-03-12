from apps.common.api import build_model_viewset
from apps.tenancy.api.serializers import TenantDomainSerializer, TenantSerializer
from apps.tenancy.models import Tenant, TenantDomain

TenantViewSet = build_model_viewset(Tenant, TenantSerializer, search_fields=("name", "slug", "schema_name"), filterset_fields=("is_active", "on_trial"))
TenantDomainViewSet = build_model_viewset(TenantDomain, TenantDomainSerializer, search_fields=("domain",), filterset_fields=("tenant", "is_primary", "is_active"))
