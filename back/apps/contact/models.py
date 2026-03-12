from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models

from apps.common.models import activearchlockedMixin, createdtimestamp_uid


class Country(createdtimestamp_uid):
    name = models.CharField(max_length=100, unique=True)
    iso3 = models.CharField(max_length=3, blank=True)
    iso2 = models.CharField(max_length=2, blank=True)
    numeric_code = models.CharField(max_length=10, blank=True)
    phone_code = models.CharField(max_length=20, blank=True)
    currency = models.CharField(max_length=3, blank=True)
    currency_name = models.CharField(max_length=50, blank=True)

    class Meta:
        ordering = ("name",)

    def __str__(self):
        return self.name


class State(createdtimestamp_uid):
    country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name="states")
    name = models.CharField(max_length=100)
    state_code = models.CharField(max_length=10, blank=True)

    class Meta:
        unique_together = (("country", "name"),)
        ordering = ("name",)

    def __str__(self):
        return f"{self.name}, {self.country.name}"


class City(createdtimestamp_uid):
    state = models.ForeignKey(State, on_delete=models.CASCADE, related_name="cities")
    name = models.CharField(max_length=100)

    class Meta:
        unique_together = (("state", "name"),)
        ordering = ("name",)

    def __str__(self):
        return f"{self.name}, {self.state.name}"


class AddressType(createdtimestamp_uid, activearchlockedMixin):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class PhoneType(createdtimestamp_uid, activearchlockedMixin):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class EmailType(createdtimestamp_uid, activearchlockedMixin):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class webType(createdtimestamp_uid, activearchlockedMixin):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class Phone(createdtimestamp_uid, activearchlockedMixin):
    phonetype = models.ForeignKey(PhoneType, null=True, blank=True, on_delete=models.SET_NULL, related_name="phones")
    phone = models.CharField(max_length=50)
    is_whatsapp = models.BooleanField(default=False)

    def __str__(self):
        return self.phone


class Address(createdtimestamp_uid, activearchlockedMixin):
    addresstype = models.ForeignKey(AddressType, null=True, blank=True, on_delete=models.SET_NULL, related_name="addresses")
    line = models.CharField(max_length=255)
    city = models.ForeignKey(City, on_delete=models.PROTECT, related_name="addresses")
    postal_code = models.CharField(max_length=20, blank=True)
    landmark = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"{self.line}, {self.city.name}"


class Email(createdtimestamp_uid, activearchlockedMixin):
    email = models.EmailField(unique=True)
    emailType = models.ForeignKey(EmailType, null=True, blank=True, on_delete=models.SET_NULL, related_name="emails")

    def __str__(self):
        return self.email


class Website(createdtimestamp_uid, activearchlockedMixin):
    website = models.URLField(unique=True)
    webtype = models.ForeignKey(webType, null=True, blank=True, on_delete=models.SET_NULL, related_name="websites")

    def __str__(self):
        return self.website


class Contact(createdtimestamp_uid, activearchlockedMixin):
    ALLOWED_MODELS = ["phone", "address", "website", "email"]

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    contact_id = models.UUIDField()
    contactobject = GenericForeignKey("content_type", "contact_id")
    related_contacts = models.ManyToManyField("self", blank=True)

    class Meta:
        unique_together = (("content_type", "contact_id"),)

    def clean(self):
        if self.content_type and self.content_type.model not in self.ALLOWED_MODELS:
            raise ValidationError("Unsupported contact model.")

    def __str__(self):
        return f"{self.content_type} - {self.contact_id}"


class DocumentType(createdtimestamp_uid, activearchlockedMixin):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class Document(createdtimestamp_uid, activearchlockedMixin):
    document_type = models.ForeignKey(DocumentType, on_delete=models.SET_NULL, null=True, blank=True, related_name="documents")
    document_url = models.URLField()
    description = models.TextField(blank=True)
    custom_fields = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return self.document_url
