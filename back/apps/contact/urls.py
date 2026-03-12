from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.contact.api.views import AddressTypeViewSet, AddressViewSet, CityViewSet, ContactViewSet, CountryViewSet, DocumentTypeViewSet, DocumentViewSet, EmailTypeViewSet, EmailViewSet, PhoneTypeViewSet, PhoneViewSet, StateViewSet, WebsiteViewSet, WebTypeViewSet

router = DefaultRouter()
router.register("countries", CountryViewSet, basename="country")
router.register("states", StateViewSet, basename="state")
router.register("cities", CityViewSet, basename="city")
router.register("address-types", AddressTypeViewSet, basename="address-type")
router.register("phone-types", PhoneTypeViewSet, basename="phone-type")
router.register("email-types", EmailTypeViewSet, basename="email-type")
router.register("web-types", WebTypeViewSet, basename="web-type")
router.register("phones", PhoneViewSet, basename="phone")
router.register("addresses", AddressViewSet, basename="address")
router.register("emails", EmailViewSet, basename="email")
router.register("websites", WebsiteViewSet, basename="website")
router.register("contacts", ContactViewSet, basename="contact")
router.register("document-types", DocumentTypeViewSet, basename="document-type")
router.register("documents", DocumentViewSet, basename="document")

urlpatterns = [path("", include(router.urls))]
