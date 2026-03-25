from rest_framework.routers import DefaultRouter

from .views import (
    AddressTypeViewSet,
    AddressViewSet,
    CityViewSet,
    ContactViewSet,
    CountryViewSet,
    EmailTypeViewSet,
    EmailViewSet,
    PhoneTypeViewSet,
    PhoneViewSet,
    StateViewSet,
    WebsiteTypeViewSet,
    WebsiteViewSet,
)

router = DefaultRouter()
router.register('countries', CountryViewSet, basename='country')
router.register('states', StateViewSet, basename='state')
router.register('cities', CityViewSet, basename='city')
router.register('address-types', AddressTypeViewSet, basename='address-type')
router.register('phone-types', PhoneTypeViewSet, basename='phone-type')
router.register('email-types', EmailTypeViewSet, basename='email-type')
router.register('website-types', WebsiteTypeViewSet, basename='website-type')
router.register('phones', PhoneViewSet, basename='phone')
router.register('addresses', AddressViewSet, basename='address')
router.register('emails', EmailViewSet, basename='email')
router.register('websites', WebsiteViewSet, basename='website')
router.register('contacts', ContactViewSet, basename='contact')

urlpatterns = router.urls