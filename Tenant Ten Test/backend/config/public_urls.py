from django.contrib import admin
from django.urls import path

from apps.core_shared.views import GlobalAnnouncementListAPIView
from apps.customers.views import CompanyListAPIView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/public/companies/", CompanyListAPIView.as_view(), name="public-companies"),
    path(
        "api/public/shared-announcements/",
        GlobalAnnouncementListAPIView.as_view(),
        name="public-shared-announcements",
    ),
]
