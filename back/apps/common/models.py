import uuid

from django.conf import settings
from django.db import models


class createdtimestamp_uid(models.Model):
    """Base abstract model providing UUID primary key, created_at and updated_at timestamps."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


# Backward-compat alias
createtimstam_uid = createdtimestamp_uid


class activearchlockedMixin(models.Model):
    """Soft-delete state mixin — active/archived/locked lifecycle flags."""
    is_active = models.BooleanField(default=True)
    is_archived = models.BooleanField(default=False)
    is_locked = models.BooleanField(default=False)

    class Meta:
        abstract = True


class CompanyMixin(models.Model):
    """Associates a record with a tenant Company. Used when the model lives in a
    shared or cross-tenant scheme and needs its own company FK column."""
    company = models.ForeignKey(
        "company.Company",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="%(app_label)s_%(class)s_records",
    )

    class Meta:
        abstract = True


class UserStampedMixin(models.Model):
    """Adds created_by and updated_by audit fields to any model."""
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    class Meta:
        abstract = True


# Backward-compat alias
UserStampedModel = UserStampedMixin


class StatusMixin(models.Model):
    """Generic status + status_reason mixin for workflow-driven models."""
    status = models.CharField(max_length=30, default="draft")
    status_reason = models.TextField(blank=True)

    class Meta:
        abstract = True


class NoteMixin(models.Model):
    """Adds a freeform notes field."""
    notes = models.TextField(blank=True)

    class Meta:
        abstract = True
