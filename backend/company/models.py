from autoslug import AutoSlugField
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from django_countries.fields import CountryField
from django_tenants.models import DomainMixin, TenantMixin
from djmoney.models.fields import CurrencyField

from addons.models import AddressMixin, CompanyMixin, PhoneNumberMixin, SocialMediaMixin, TimeStampedUUIDMixin


class CurrencyChoices(models.TextChoices):
    GHS = 'GHS', _('Ghanaian Cedi')
    USD = 'USD', _('US Dollar')
    EUR = 'EUR', _('Euro')
    GBP = 'GBP', _('British Pound')


class Industry(TimeStampedUUIDMixin):
    name = models.CharField(max_length=255, unique=True, db_index=True)
    description = models.TextField(blank=True, null=True)
    additional_info = models.JSONField(blank=True, default=dict)

    class Meta:
        ordering = ('name',)
        indexes = [models.Index(fields=('name',), name='ix_industry_name')]

    def __str__(self):
        return self.name


class PaymentClass(TimeStampedUUIDMixin):
    name = models.CharField(max_length=80, unique=True, db_index=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ('name',)
        indexes = [models.Index(fields=('name',), name='ix_payment_class_name')]

    def __str__(self):
        return self.name


class BusinessType(TimeStampedUUIDMixin):
    name = models.CharField(max_length=100, unique=True, db_index=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ('name',)
        indexes = [models.Index(fields=('name',), name='ix_business_type_name')]

    def __str__(self):
        return self.name


class Company(TenantMixin, CompanyMixin, AddressMixin, SocialMediaMixin, TimeStampedUUIDMixin):
    slug = AutoSlugField(populate_from='name', unique=True, always_update=False)
    industry = models.ForeignKey(
        Industry,
        verbose_name=_('Industry'),
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='companies',
    )
    trade_country = CountryField(_('Primary Trade Country'), blank=True, null=True)
    is_active = models.BooleanField(default=True, db_index=True)
    payment_class = models.ForeignKey(
        PaymentClass,
        verbose_name=_('Payment Class'),
        on_delete=models.PROTECT,
        related_name='companies',
    )
    business_type = models.ForeignKey(
        BusinessType,
        verbose_name=_('Business Type'),
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='companies',
    )
    default_currency = CurrencyField(
        _('Default Currency'),
        max_length=3,
        choices=CurrencyChoices.choices,
        default=CurrencyChoices.GHS,
        editable=False,
    )
    additional_info = models.JSONField(blank=True, default=dict)
    contacts = models.ManyToManyField('contact.Contact', blank=True, related_name='companies')

    auto_create_schema = True
    auto_drop_schema = False

    class Meta:
        ordering = ('name',)
        indexes = [
            models.Index(fields=('is_active',), name='ix_company_active'),
            models.Index(fields=('trade_country',), name='ix_company_country'),
            models.Index(fields=('schema_name',), name='ix_company_schema'),
        ]

    def __str__(self):
        return self.name

    def _ensure_schema_name(self):
        if self.name and not self.schema_name:
            self.schema_name = slugify(self.name).replace('-', '_')[:63]
        if self.schema_name:
            self.schema_name = self.schema_name.replace('-', '_')

    def clean(self):
        self._ensure_schema_name()
        super().clean()
        if self.pk:
            previous = Company.objects.filter(pk=self.pk).values('default_currency', 'schema_name').first()
            if previous and previous['default_currency'] != self.default_currency:
                raise ValidationError({'default_currency': _('Default currency cannot be changed after creation.')})
            if previous and previous['schema_name'] != self.schema_name:
                raise ValidationError({'schema_name': _('Schema name cannot be changed after creation.')})

    def save(self, *args, **kwargs):
        self._ensure_schema_name()
        self.full_clean()
        return super().save(*args, **kwargs)


class Domain(DomainMixin, TimeStampedUUIDMixin):
    class Meta:
        ordering = ('domain',)

    def __str__(self):
        return self.domain