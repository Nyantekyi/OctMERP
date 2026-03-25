from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from addons.models import TimeStampedUUIDMixin


class Country(TimeStampedUUIDMixin):
    name = models.CharField(_('Name'), max_length=100, unique=True, db_index=True)
    iso3 = models.CharField(_('ISO3'), max_length=3, blank=True, null=True, unique=True)
    iso2 = models.CharField(_('ISO2'), max_length=2, blank=True, null=True, unique=True)
    numeric_code = models.CharField(_('Numeric Code'), max_length=6, unique=True)
    phone_code = models.CharField(_('Phone Code'), max_length=5, blank=True, null=True)
    currency = models.CharField(_('Currency'), max_length=3, blank=True, null=True)
    currency_name = models.CharField(_('Currency Name'), max_length=50, blank=True, null=True)
    lat = models.DecimalField(_('Latitude'), max_digits=10, decimal_places=8, blank=True, null=True)
    lon = models.DecimalField(_('Longitude'), max_digits=11, decimal_places=8, blank=True, null=True)

    class Meta:
        verbose_name = _('Country')
        verbose_name_plural = _('Countries')
        ordering = ('name',)

    def __str__(self):
        return self.name


class State(TimeStampedUUIDMixin):
    country = models.ForeignKey(Country, verbose_name=_('Country'), on_delete=models.CASCADE, related_name='states')
    name = models.CharField(_('State'), max_length=150)
    state_code = models.CharField(_('State Code'), max_length=10, blank=True, null=True)
    lat = models.DecimalField(_('Latitude'), max_digits=11, decimal_places=8, blank=True, null=True)
    lon = models.DecimalField(_('Longitude'), max_digits=11, decimal_places=8, blank=True, null=True)

    class Meta:
        verbose_name = _('State')
        verbose_name_plural = _('States')
        ordering = ('country__name', 'name')
        constraints = [
            models.UniqueConstraint(fields=('country', 'name'), name='uq_contact_state_country_name')
        ]

    def __str__(self):
        return self.name


class City(TimeStampedUUIDMixin):
    name = models.CharField(_('City'), max_length=150)
    state = models.ForeignKey(State, verbose_name=_('State'), on_delete=models.CASCADE, related_name='cities')
    lat = models.DecimalField(_('Latitude'), max_digits=11, decimal_places=8, blank=True, null=True)
    lon = models.DecimalField(_('Longitude'), max_digits=11, decimal_places=8, blank=True, null=True)

    class Meta:
        verbose_name = _('City')
        verbose_name_plural = _('Cities')
        ordering = ('state__country__name', 'state__name', 'name')
        constraints = [
            models.UniqueConstraint(fields=('state', 'name'), name='uq_contact_city_state_name')
        ]

    def __str__(self):
        return self.name


class NamedContactType(TimeStampedUUIDMixin):
    name = models.CharField(max_length=50, unique=True)

    class Meta:
        abstract = True
        ordering = ('name',)

    def __str__(self):
        return self.name


class AddressType(NamedContactType):
    class Meta(NamedContactType.Meta):
        verbose_name = _('Address Type')
        verbose_name_plural = _('Address Types')


class PhoneType(NamedContactType):
    class Meta(NamedContactType.Meta):
        verbose_name = _('Phone Type')
        verbose_name_plural = _('Phone Types')


class EmailType(NamedContactType):
    class Meta(NamedContactType.Meta):
        verbose_name = _('Email Type')
        verbose_name_plural = _('Email Types')


class WebsiteType(NamedContactType):
    class Meta(NamedContactType.Meta):
        verbose_name = _('Website Type')
        verbose_name_plural = _('Website Types')


class Phone(TimeStampedUUIDMixin):
    phone_type = models.ForeignKey(
        PhoneType,
        verbose_name=_('Phone Type'),
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='phones',
    )
    phone = models.CharField(
        _('Phone'),
        max_length=50,
        validators=[RegexValidator(regex=r'^\+?[0-9 ()-]{5,50}$', message=_('Enter a valid phone number.'))],
    )
    is_whatsapp = models.BooleanField(_('Is WhatsApp'), default=False)

    class Meta:
        verbose_name = _('Phone')
        verbose_name_plural = _('Phones')
        ordering = ('phone',)

    def __str__(self):
        return self.phone


class Address(TimeStampedUUIDMixin):
    address_type = models.ForeignKey(
        AddressType,
        verbose_name=_('Address Type'),
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='addresses',
    )
    line = models.CharField(_('Line 1'), max_length=255)
    line_2 = models.CharField(_('Line 2'), max_length=255, blank=True, null=True)
    city = models.ForeignKey(City, verbose_name=_('City'), on_delete=models.CASCADE, related_name='addresses')
    postal_code = models.CharField(_('Postal Code'), max_length=30, blank=True, null=True)
    custom_fields = models.JSONField(_('Custom Fields'), blank=True, default=dict)

    class Meta:
        verbose_name = _('Address')
        verbose_name_plural = _('Addresses')
        ordering = ('city__state__country__name', 'city__state__name', 'city__name', 'line')

    def __str__(self):
        return f'{self.city.name} - {self.line}'


class Email(TimeStampedUUIDMixin):
    email = models.EmailField(verbose_name=_('Email'), unique=True)
    email_type = models.ForeignKey(
        EmailType,
        verbose_name=_('Email Type'),
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='emails',
    )

    class Meta:
        verbose_name = _('Email')
        verbose_name_plural = _('Emails')
        ordering = ('email',)

    def __str__(self):
        return self.email


class Website(TimeStampedUUIDMixin):
    website = models.URLField(verbose_name=_('Website'), unique=True)
    website_type = models.ForeignKey(
        WebsiteType,
        verbose_name=_('Website Type'),
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='websites',
    )

    class Meta:
        verbose_name = _('Website')
        verbose_name_plural = _('Websites')
        ordering = ('website',)

    def __str__(self):
        return self.website


class Contact(TimeStampedUUIDMixin):
    ALLOWED_MODELS = {'phone', 'address', 'website', 'email'}

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, editable=False)
    contact_id = models.UUIDField(editable=False)
    contact_object = GenericForeignKey('content_type', 'contact_id')
    label = models.CharField(_('Label'), max_length=100, blank=True, null=True)
    is_verified = models.BooleanField(_('Is Verified'), default=False)
    is_primary = models.BooleanField(_('Is Primary'), default=False)
    related_contacts = models.ManyToManyField('self', blank=True, verbose_name=_('Related Contacts'))

    class Meta:
        verbose_name = _('Contact')
        verbose_name_plural = _('Contacts')
        ordering = ('content_type__model', 'created_at')
        indexes = [
            models.Index(fields=('content_type', 'contact_id'), name='ix_contact_lookup'),
        ]
        constraints = [
            models.UniqueConstraint(fields=('content_type', 'contact_id'), name='uq_contact_target')
        ]

    def __str__(self):
        return f'{self.content_type.model}: {self.contact_object}'

    def clean(self):
        super().clean()
        if self.content_type_id and self.content_type.model not in self.ALLOWED_MODELS:
            raise ValidationError({'content_type': _('Invalid contact type: %(model)s') % {'model': self.content_type.model}})


webType = WebsiteType