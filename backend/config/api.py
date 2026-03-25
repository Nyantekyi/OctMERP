from rest_framework.decorators import api_view
from rest_framework.permissions import AllowAny
from rest_framework.decorators import permission_classes
from rest_framework.response import Response


@api_view(["GET"])
@permission_classes([AllowAny])
def api_root(request):
    tenant = getattr(request, 'tenant', None)
    return Response(
        {
            "name": "ERP backend",
            "status": "ok",
            "tenant": {
                "id": str(tenant.id) if tenant else None,
                "name": getattr(tenant, 'name', None),
                "schema_name": getattr(tenant, 'schema_name', None),
            },
            "endpoints": {
                "health": request.build_absolute_uri("health/"),
                "admin": request.build_absolute_uri("../admin/"),
                "auth_login": request.build_absolute_uri("auth/login/"),
                "company_api": request.build_absolute_uri("company/companies/"),
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