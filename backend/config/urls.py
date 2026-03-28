from django.contrib import admin
from django.urls import include, path

from .auth_views import CurrentUserView, KnoxLoginAPIView
from .api import api_root, health_check, resolve_tenant
from knox.views import LogoutAllView, LogoutView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', api_root, name='api-root'),
    path('api/health/', health_check, name='health-check'),
    path('api/tenant/resolve/', resolve_tenant, name='tenant-resolve'),
    path('api/auth/login/', KnoxLoginAPIView.as_view(), name='auth-login'),
    path('api/auth/logout/', LogoutView.as_view(), name='auth-logout'),
    path('api/auth/logout-all/', LogoutAllView.as_view(), name='auth-logout-all'),
    path('api/auth/me/', CurrentUserView.as_view(), name='auth-me'),
    path('api/company/', include('company.urls')),
    path('api/contact/', include('contact.urls')),
]
