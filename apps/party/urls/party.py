from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.party.views import (
    UserViewSet,
    OccupationViewSet,
    StaffProfileViewSet,
    ClientProfileViewSet,
    SupplierProfileViewSet,
    AgentProfileViewSet,
    ContactPointViewSet,
    AddressViewSet,
    DocumentTypeViewSet,
    DocumentViewSet,
)

app_name = "party"

router = DefaultRouter()
router.register("users", UserViewSet, basename="user")
router.register("occupations", OccupationViewSet, basename="occupation")
router.register("staff-profiles", StaffProfileViewSet, basename="staff-profile")
router.register("client-profiles", ClientProfileViewSet, basename="client-profile")
router.register("supplier-profiles", SupplierProfileViewSet, basename="supplier-profile")
router.register("agent-profiles", AgentProfileViewSet, basename="agent-profile")
router.register("contact-points", ContactPointViewSet, basename="contact-point")
router.register("addresses", AddressViewSet, basename="address")
router.register("document-types", DocumentTypeViewSet, basename="document-type")
router.register("documents", DocumentViewSet, basename="document")

urlpatterns = [path("", include(router.urls))]
