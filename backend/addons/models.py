import uuid

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from django_countries.fields import CountryField
from simple_history.models import HistoricalRecords


class ObjectLevelMixin(models.Model):
    """Restrict generic relations to a known set of preference targets."""

    allowed_models = {
        'itemvariant',
        'variantattribute',
        'manufacturer',
        'productscategory',
    }

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.UUIDField()
    preference_object = GenericForeignKey('content_type', 'object_id')

    class Meta:
        abstract = True

    def __str__(self):
        return f'{self.content_type.model}: {self.preference_object}'

    def clean(self):
        super().clean()
        if self.content_type_id and self.content_type.model not in self.allowed_models:
            raise ValidationError(
                {'content_type': _('Invalid preference type: %(model)s') % {'model': self.content_type.model}}
            )


class LockedManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(status='locked')


class ActiveManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(status='active')


class InactiveManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().exclude(status='active')


class ArchivedManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(status='archived')


class DeletedManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(status='deleted')


class StringUUIDField(models.CharField):
    """CharField-backed UUID storage for historical tables and legacy IDs."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('max_length', 64)
        kwargs.setdefault('blank', True)
        super().__init__(*args, **kwargs)

    def pre_save(self, model_instance, add):
        if add and not getattr(model_instance, self.attname):
            value = str(uuid.uuid4())
            setattr(model_instance, self.attname, value)
            return value
        return super().pre_save(model_instance, add)


class StatusMixin(models.Model):
    class Status(models.TextChoices):
        ARCHIVED = 'archived', _('Archived')
        LOCKED = 'locked', _('Locked')
        DELETED = 'deleted', _('Deleted')
        ACTIVE = 'active', _('Active')

    status = models.CharField(
        _('Status'),
        choices=Status.choices,
        default=Status.ACTIVE,
        max_length=20,
    )

    objects = models.Manager()
    active = ActiveManager()
    inactive = InactiveManager()
    archived = ArchivedManager()
    deleted = DeletedManager()
    locked = LockedManager()

    class Meta:
        abstract = True


class TimeStampedHistoryMixin(models.Model):
    """Created/updated timestamps with simple-history support."""

    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False, null=True, blank=True)
    history = HistoricalRecords(inherit=True)

    class Meta:
        abstract = True


class CompanyMixin(models.Model):
    name = models.CharField(_('Company Legal Name'), max_length=100, unique=True)
    company_logo = models.ImageField(blank=True, null=True)
    trade_name = models.CharField(_('Trade Name'), max_length=100, blank=True, null=True)
    incorporation_date = models.DateField(_('Incorporation Date'), blank=True, null=True)
    description = models.TextField(_('Organization Description Narrative'), blank=True, null=True)
    motto = models.CharField(_('Motto'), max_length=100, blank=True, null=True)

    class Meta:
        abstract = True


class CreatedUUIDMixin(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    id = StringUUIDField(primary_key=True, editable=False)
    history = HistoricalRecords(history_id_field=StringUUIDField(editable=False), inherit=True)

    class Meta:
        abstract = True


class TimeStampedUUIDMixin(models.Model):
    """UUID primary key plus timestamps and history."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False, null=True, blank=True)
    history = HistoricalRecords(history_id_field=StringUUIDField(editable=False), inherit=True)

    class Meta:
        abstract = True

    @property
    def slug(self):
        return slugify(str(self.id))


class SoftDeleteMixin(models.Model):
    deleted = models.BooleanField(_('Deleted'), default=False)
    recycle_bin = models.BooleanField(_('Recycle Bin'), default=False)

    class Meta:
        abstract = True


class PhoneNumberMixin(models.Model):
    phone_regex = RegexValidator(
        regex=r'^(?:\+233)?([0-9]\d{9})$',
        message="Phone number must be entered in the format '+233XXXXXXXXX'.",
    )

    mobile_number = models.CharField(validators=[phone_regex], max_length=16, blank=True, null=True)
    phone = models.CharField(_('Phone'), validators=[phone_regex], max_length=16, blank=True, null=True)

    class Meta:
        abstract = True


class AddressMixin(models.Model):
    address = models.CharField(_('Address Line'), max_length=100, blank=True, null=True)
    city = models.CharField(max_length=255, blank=True, null=True)
    country = CountryField(blank=True, null=True)
    zip_code = models.CharField(max_length=255, blank=True, null=True)
    postal_code = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        abstract = True


class SocialMediaMixin(models.Model):
    instagram = models.URLField(_('Instagram'), blank=True, null=True)
    x_twitter = models.URLField(_('Twitter'), blank=True, null=True)
    facebook = models.URLField(_('Facebook'), blank=True, null=True)
    linkedin = models.URLField(_('LinkedIn'), blank=True, null=True)
    youtube = models.URLField(_('YouTube'), blank=True, null=True)
    pinterest = models.URLField(_('Pinterest'), blank=True, null=True)
    google_plus = models.URLField(_('Google Plus'), blank=True, null=True)

    class Meta:
        abstract = True


class UniqueCodeField(models.SlugField):
    """Generate a short unique slug from the configured source fields."""

    def __init__(self, source_fields, *args, **kwargs):
        self.source_fields = source_fields
        kwargs.setdefault('editable', False)
        super().__init__(*args, **kwargs)

    def pre_save(self, model_instance, add):
        value = getattr(model_instance, self.attname, None)
        if value:
            return super().pre_save(model_instance, add)

        source_values = [str(getattr(model_instance, field, '')) for field in self.source_fields]
        base_value = slugify(' '.join(filter(None, source_values)))[:4] or 'code'
        candidate = base_value
        queryset = model_instance.__class__._default_manager.all()
        if model_instance.pk:
            queryset = queryset.exclude(pk=model_instance.pk)

        count = 1
        while queryset.filter(**{self.name: candidate}).exists():
            candidate = f'{base_value}-{count}'
            count += 1

        setattr(model_instance, self.attname, candidate)
        return candidate


class DiscountMixin(models.Model):
    class DiscountType(models.TextChoices):
        PERCENT = 'percent', _('Percent')
        AMOUNT = 'amount', _('Amount')

    discount_type = models.CharField(_('Discount Type'), choices=DiscountType.choices, max_length=20)
    discount = models.DecimalField(_('Discount'), max_digits=20, decimal_places=2, default=0)

    class Meta:
        abstract = True

    def clean(self):
        super().clean()
        if self.discount < 0:
            raise ValidationError({'discount': _('Discount cannot be negative.')})

        if self.discount_type == self.DiscountType.PERCENT and self.discount > 100:
            raise ValidationError({'discount': _('Percentage discounts must be between 0 and 100.')})


# Backward-compatible aliases for the original schema naming.
obj_level = ObjectLevelMixin
is_lockedManager = LockedManager
is_activeManager = ActiveManager
is_inactiveManager = InactiveManager
is_achivedmanager = ArchivedManager
isdelmanager = DeletedManager
UUIDField = StringUUIDField
activearchlockedMixin = StatusMixin
createdtimestamp = TimeStampedHistoryMixin
createtimstam_uid = CreatedUUIDMixin
createdtimestamp_uid = TimeStampedUUIDMixin
deled = SoftDeleteMixin
phonenumberMixin = PhoneNumberMixin
addressMixin = AddressMixin
socialmedMixin = SocialMediaMixin
discount = DiscountMixin