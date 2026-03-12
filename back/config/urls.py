from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/v1/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/v1/auth/", include("apps.party.api.auth_urls")),
    path("api/v1/contact/", include("apps.contact.urls")),
    path("api/v1/company/", include("apps.company.urls")),
    path("api/v1/party/", include("apps.party.urls")),
    path("api/v1/department/", include("apps.department.urls")),
    path("api/v1/accounts/", include("apps.accounts.urls")),
    path("api/v1/hrm/", include("apps.hrm.urls")),
    path("api/v1/crm/", include("apps.crm.urls")),
    path("api/v1/inventory/", include("apps.inventory.urls")),
    path("api/v1/sales/", include("apps.sales.urls")),
]
