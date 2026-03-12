"""
apps/department/models.py

Organisational hierarchy below Company:
  Company → Department → Branch → Shift / Room / Shelfing
"""

from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _
from djmoney.models.fields import MoneyField

from apps.common.models import TenantAwareModel, DEFAULT_CURRENCY


class Department(TenantAwareModel):
    DEPARTMENT_TYPE_CHOICES = [
        ("Wholesale Unit", _("Wholesale Unit")),
        ("Retail Unit", _("Retail Unit")),
        ("Manufacturing Unit", _("Manufacturing Unit")),
    ]

    name = models.CharField(_("Name"), max_length=50)
    code = models.CharField(
        _("Department Code"), max_length=10, unique=True, blank=True,
        help_text=_("Short unique identifier for this department (e.g. FIN, OPS, MFG).")
    )
    departmenttype = models.CharField(_("Type"), max_length=50, choices=DEPARTMENT_TYPE_CHOICES)
    description = models.TextField(blank=True, null=True)
    staff = models.ForeignKey(
        "party.CustomUser", on_delete=models.PROTECT,
        related_name="managed_departments", verbose_name=_("Manager")
    )
    base_markup = models.DecimalField(_("Base Markup %"), max_digits=5, decimal_places=2, default=0)
    is_marked_up_from = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.PROTECT,
        related_name="markup_children", verbose_name=_("Marked up from")
    )

    # Sale configuration
    is_saledepartment = models.BooleanField(_("Is Sale Dept?"), default=False)
    is_onlinesaledepartment = models.BooleanField(_("Is Online Sale Dept?"), default=False)
    defaultonlinedepartment = models.BooleanField(_("Default Online?"), default=False)
    is_creditsale_allowed = models.BooleanField(_("Credit Sale Allowed?"), default=False)

    class Meta:
        verbose_name = _("Department")
        verbose_name_plural = _("Departments")
        unique_together = ("departmenttype", "name")

    def __str__(self):
        return f"{self.name} ({self.departmenttype})"

    def clean(self):
        if self.is_marked_up_from and self.is_marked_up_from == self:
            raise ValidationError(_("A department cannot be marked up from itself."))
        if self.is_onlinesaledepartment and not self.is_saledepartment:
            raise ValidationError(_("An online-sale department must also be a sale department."))
        if self.is_creditsale_allowed and not self.is_saledepartment:
            raise ValidationError(_("Credit sale requires a sale department."))

    def save(self, *args, **kwargs):
        if self.defaultonlinedepartment:
            Department.objects.exclude(pk=self.pk).filter(defaultonlinedepartment=True).update(
                defaultonlinedepartment=False
            )
        super().save(*args, **kwargs)


class Branch(TenantAwareModel):
    department = models.ForeignKey(Department, on_delete=models.PROTECT, related_name="branches")
    name = models.CharField(_("Branch Name"), max_length=50)
    code = models.CharField(
        _("Branch Code"), max_length=10, unique=True, blank=True,
        help_text=_("Short unique identifier for this branch (e.g. HQ, KSI, ACC).")
    )
    staff = models.ForeignKey(
        "party.CustomUser", on_delete=models.PROTECT,
        related_name="managed_branches", verbose_name=_("Branch Manager")
    )
    address = models.ForeignKey(
        "contact.Address", on_delete=models.PROTECT,
        null=True, blank=True, related_name="branches"
    )
    is_warehouse = models.BooleanField(_("Is Warehouse?"), default=False)
    warehouse_unit = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.PROTECT,
        limit_choices_to={"is_warehouse": True},
        related_name="served_branches"
    )
    branchaccount = models.ManyToManyField(
        "accounting.Account", blank=True, related_name="branch_accounts"
    )
    sale_tax = models.ManyToManyField(
        "accounting.Tax", blank=True, related_name="sale_branches",
        help_text=_("Default taxes applied at this branch for taxable items")
    )
    avatar = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        verbose_name = _("Branch")
        verbose_name_plural = _("Branches")
        unique_together = ("name", "department")

    def __str__(self):
        return f"{self.name} — {self.department}"


class Shift(TenantAwareModel):
    SHIFT_TYPES = [
        ("Morning Shift", _("Morning Shift")),
        ("Afternoon Shift", _("Afternoon Shift")),
        ("Evening Shift", _("Evening Shift")),
        ("Night Shift", _("Night Shift")),
    ]

    shift_types = models.CharField(_("Shift Type"), max_length=50, choices=SHIFT_TYPES)
    start_time = models.TimeField(_("Start Time"))
    end_time = models.TimeField(_("End Time"))
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name="shifts")
    staff = models.ForeignKey(
        "party.CustomUser", on_delete=models.PROTECT, related_name="created_shifts"
    )
    break_duration_minutes = models.PositiveIntegerField(_("Break Duration (min)"), default=0)

    class Meta:
        verbose_name = _("Shift")
        verbose_name_plural = _("Shifts")
        unique_together = ("shift_types", "department")

    def __str__(self):
        return f"{self.shift_types} — {self.department}"

    def clean(self):
        if self.start_time and self.end_time and self.start_time >= self.end_time:
            raise ValidationError(_("Start time must be before end time."))


class Room(TenantAwareModel):
    COST_RATE_CHOICES = [
        ("fixed", _("Fixed")),
        ("hourly", _("Hourly")),
        ("daily", _("Daily")),
        ("weekly", _("Weekly")),
        ("monthly", _("Monthly")),
        ("none", _("No Cost")),
    ]
    STATUS_CHOICES = [
        ("available", _("Available")),
        ("unavailable", _("Unavailable")),
    ]

    name = models.CharField(_("Room Name"), max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    cost_rate = models.CharField(max_length=10, choices=COST_RATE_CHOICES, default="none")
    assigned_cost = MoneyField(
        max_digits=10, decimal_places=2, default=0, default_currency=DEFAULT_CURRENCY
    )
    staff = models.ForeignKey(
        "party.CustomUser", on_delete=models.PROTECT, related_name="managed_rooms"
    )
    location = models.ForeignKey(
        "contact.Address", on_delete=models.PROTECT, null=True, blank=True, related_name="rooms"
    )
    floor_number = models.CharField(max_length=10, null=True, blank=True, default="0")
    capacity = models.PositiveIntegerField(_("Capacity"), default=0)
    restricted_access = models.BooleanField(_("Restricted Access"), default=False)
    activities = ArrayField(models.CharField(max_length=100), blank=True, default=list)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="available")
    assigned_branch = models.ManyToManyField(Branch, blank=True, related_name="rooms")
    assigned_staff = models.ManyToManyField(
        "party.CustomUser", blank=True, related_name="assigned_rooms"
    )

    class Meta:
        verbose_name = _("Room")

    def __str__(self):
        return self.name


class Shelfing(TenantAwareModel):
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name="shelves")
    room = models.ForeignKey(Room, on_delete=models.CASCADE, null=True, blank=True, related_name="shelves")
    shelf = models.CharField(_("Shelf Code"), max_length=50)

    class Meta:
        verbose_name = _("Shelf")
        verbose_name_plural = _("Shelving")
        unique_together = ("branch", "shelf")

    def __str__(self):
        return f"{self.shelf} @ {self.branch}"
