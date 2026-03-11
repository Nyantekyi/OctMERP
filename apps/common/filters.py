"""
apps/common/filters.py

Reusable filter base classes and mixins for DRF + django-filter.
"""

import django_filters
from django.db import models


class TenantAwareModelFilterSet(django_filters.FilterSet):
    """
    Base FilterSet for TenantAwareModel subclasses.
    Provides standard is_active / is_archived / created_at range filters.
    """
    is_active = django_filters.BooleanFilter(field_name="is_active")
    is_archived = django_filters.BooleanFilter(field_name="is_archived")
    created_after = django_filters.DateTimeFilter(field_name="created_at", lookup_expr="gte")
    created_before = django_filters.DateTimeFilter(field_name="created_at", lookup_expr="lte")

    class Meta:
        abstract = True
