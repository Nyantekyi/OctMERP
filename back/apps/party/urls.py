from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.party.api.views import ClientViewSet, OccupationViewSet, StaffViewSet, UserViewSet, VendorViewSet

router = DefaultRouter()
router.register("users", UserViewSet, basename="user")
router.register("occupations", OccupationViewSet, basename="occupation")
router.register("staff", StaffViewSet, basename="staff")
router.register("clients", ClientViewSet, basename="client")
router.register("vendors", VendorViewSet, basename="vendor")

urlpatterns = [path("", include(router.urls))]
