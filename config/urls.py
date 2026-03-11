"""
config/urls.py — Root URL configuration.

Public (shared) routes are registered here.
Tenant-specific routes are included via the tenant URL pattern.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

# ── Public schema routes ──────────────────────────────────────────────────────
public_urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/auth/", include("apps.party.urls.auth")),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]

# ── Tenant-scoped routes ──────────────────────────────────────────────────────
urlpatterns = [
    path("admin/", admin.site.urls),

    # Auth
    path("api/v1/auth/", include("apps.party.urls.auth")),

    # ERP modules
    path("api/v1/party/", include("apps.party.urls.party")),
    path("api/v1/hr/", include("apps.hr.urls")),
    path("api/v1/accounting/", include("apps.accounting.urls")),
    path("api/v1/inventory/", include("apps.inventory.urls")),
    path("api/v1/invplan/", include("apps.invplan.urls")),
    path("api/v1/procurement/", include("apps.procurement.urls")),
    path("api/v1/sales/", include("apps.sales.urls")),
    path("api/v1/crm/", include("apps.crm.urls")),
    path("api/v1/ecommerce/", include("apps.ecommerce.urls")),
    path("api/v1/pos/", include("apps.pos.urls")),
    path("api/v1/manufacturing/", include("apps.manufacturing.urls")),
    path("api/v1/logistics/", include("apps.logistics.urls")),
    path("api/v1/assets/", include("apps.assets.urls")),
    path("api/v1/projects/", include("apps.projects.urls")),
    path("api/v1/reporting/", include("apps.reporting.urls")),
    path("api/v1/notifications/", include("apps.notifications.urls")),
    path("api/v1/agents/", include("apps.agents.urls")),
    path("api/v1/workflow/", include("apps.workflow.urls")),
    path("api/v1/department/", include("apps.department.urls")),

    # OpenAPI
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns
