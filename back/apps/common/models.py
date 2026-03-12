import uuid

from django.conf import settings
from django.db import models


class createdtimestamp_uid(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class createtimstam_uid(createdtimestamp_uid):
    class Meta:
        abstract = True


class activearchlockedMixin(models.Model):
    is_active = models.BooleanField(default=True)
    is_archived = models.BooleanField(default=False)
    is_locked = models.BooleanField(default=False)

    class Meta:
        abstract = True


class CompanyMixin(models.Model):
    company = models.ForeignKey(
        "company.Company",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="%(app_label)s_%(class)s_records",
    )

    class Meta:
        abstract = True


class UserStampedModel(models.Model):
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    class Meta:
        abstract = True
