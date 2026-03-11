"""
apps/common/models.py

Abstract base models shared across the entire ERP.
All tenant-scoped models must inherit from TenantAwareModel.
Non-tenant lookup tables (Country, State, City) use TimeStampedModel.
"""

import uuid
from django.db import models
from django.db.models import UUIDField
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from simple_history.models import HistoricalRecords


class TimeStampedModel(models.Model):
    """
    Lightweight base for shared, non-tenant lookup tables
    (e.g. Country, State, City, Industry).
    """
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class TenantAwareModel(models.Model):
    """
    Base class for every tenant-scoped model.
    Provides UUID primary key, audit timestamps, soft-delete flags,
    and a reference back to the user who created the record.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_("ID"),
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))
    is_active = models.BooleanField(default=True, verbose_name=_("Is Active"))
    is_archived = models.BooleanField(default=False, verbose_name=_("Is Archived"))
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        verbose_name=_("Created By"),
        editable=False,
    )
    history = HistoricalRecords(
        history_id_field=UUIDField(editable=False),
        inherit=True,
    )

    class Meta:
        abstract = True


# ──────────────────────────────────────────────────────────────────────────────
# Currency constants used across all financial apps
# ──────────────────────────────────────────────────────────────────────────────

DEFAULT_CURRENCY = "GHS"
ALLOWED_CURRENCIES = ["GHS", "USD", "EUR", "GBP", "JPY"]
CURRENCY_CHOICES = [(c, c) for c in ALLOWED_CURRENCIES]
