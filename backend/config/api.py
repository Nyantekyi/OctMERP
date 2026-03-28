from company.models import Domain
from rest_framework.decorators import api_view
from rest_framework.decorators import permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


def _serialize_tenant(tenant):
    return {
        "id": str(tenant.id) if tenant else None,
        "name": getattr(tenant, 'name', None),
        "schema_name": getattr(tenant, 'schema_name', None),
    }


def _normalize_domain(value):
    domain = (value or '').strip().lower()
    if '://' in domain:
        domain = domain.split('://', 1)[1]
    domain = domain.split('/', 1)[0]
    domain = domain.split(':', 1)[0]
    return domain


def _domain_candidates(domain):
    normalized = _normalize_domain(domain)
    if not normalized:
        return []
    if normalized.startswith('www.'):
        return [normalized, normalized[4:]]
    return [normalized, f'www.{normalized}']


@api_view(["GET"])
@permission_classes([AllowAny])
def api_root(request):
    tenant = getattr(request, 'tenant', None)
    return Response(
        {
            "name": "ERP backend",
            "status": "ok",
            "tenant": _serialize_tenant(tenant),
            "endpoints": {
                "health": request.build_absolute_uri("health/"),
                "admin": request.build_absolute_uri("../admin/"),
                "auth_login": request.build_absolute_uri("auth/login/"),
                "company_api": request.build_absolute_uri("company/companies/"),
                "tenant_resolve": request.build_absolute_uri("tenant/resolve/"),
            },
        }
    )


@api_view(["GET"])
@permission_classes([AllowAny])
def health_check(request):
    tenant = getattr(request, 'tenant', None)
    return Response(
        {
            "status": "ok",
            "tenant": getattr(tenant, 'schema_name', None),
            "database": "postgresql",
        }
    )


@api_view(["GET"])
@permission_classes([AllowAny])
def resolve_tenant(request):
    requested_domain = _normalize_domain(request.query_params.get('domain'))
    candidates = _domain_candidates(requested_domain)
    resolved_domain = Domain.objects.select_related('tenant').filter(domain__in=candidates).order_by('domain').first() if candidates else None
    tenant = resolved_domain.tenant if resolved_domain else None

    return Response(
        {
            "recognized": resolved_domain is not None,
            "domain": resolved_domain.domain if resolved_domain else requested_domain or None,
            "tenant": _serialize_tenant(tenant),
        }
    )