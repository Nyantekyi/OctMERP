from django.core.exceptions import ValidationError
from django.db import models
from djmoney.models.fields import MoneyField

from apps.common.models import activearchlockedMixin, createdtimestamp_uid


class Department(createdtimestamp_uid, activearchlockedMixin):
    choice = (
        ("Wholesale Unit", "Wholesale Unit"),
        ("Retail Unit", "Retail Unit"),
        ("Manufacturing Unit", "Manufacturing Unit"),
    )

    name = models.CharField(max_length=100)
    departmenttype = models.CharField(max_length=50, choices=choice)
    description = models.TextField(blank=True)
    staff = models.ForeignKey("party.User", null=True, blank=True, on_delete=models.SET_NULL, related_name="managed_departments")
    base_markup = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    is_marked_up_from = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL, related_name="markup_children")
    is_saledepartment = models.BooleanField(default=False)
    is_onlinesaledepartment = models.BooleanField(default=False)
    defaultonlinedepartment = models.BooleanField(default=False)
    is_creditsale_allowed = models.BooleanField(default=False)

    class Meta:
        unique_together = (("name", "departmenttype"),)

    def clean(self):
        if self.is_marked_up_from_id and self.is_marked_up_from_id == self.pk:
            raise ValidationError("You cannot assign the same department as its own parent.")
        if self.is_onlinesaledepartment and not self.is_saledepartment:
            raise ValidationError("An online sale department must also be a sale department.")
        if self.defaultonlinedepartment and not self.is_onlinesaledepartment:
            raise ValidationError("Default online department must be an online sale department.")

    def save(self, *args, **kwargs):
        if self.defaultonlinedepartment:
            Department.objects.exclude(pk=self.pk).update(defaultonlinedepartment=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Shift(createdtimestamp_uid, activearchlockedMixin):
    shift_types = models.CharField(max_length=50)
    start_time = models.TimeField()
    end_time = models.TimeField()
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name="shifts")
    staff = models.ForeignKey("party.User", null=True, blank=True, on_delete=models.SET_NULL, related_name="created_shifts")

    def clean(self):
        if self.start_time and self.end_time and self.start_time >= self.end_time:
            raise ValidationError("Shift start time must be before end time.")

    def __str__(self):
        return f"{self.shift_types}"


class Branch(createdtimestamp_uid, activearchlockedMixin):
    department = models.ForeignKey(Department, on_delete=models.PROTECT, related_name="branches")
    name = models.CharField(max_length=100)
    staff = models.ForeignKey("party.User", null=True, blank=True, on_delete=models.SET_NULL, related_name="managed_branches")
    address = models.ForeignKey("contact.Address", null=True, blank=True, on_delete=models.SET_NULL, related_name="branches")
    is_warehouse = models.BooleanField(default=False)
    warehouse_unit = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL, related_name="served_branches")
    branchaccount = models.ManyToManyField("accounts.Account", blank=True, related_name="branches")
    sale_tax = models.ManyToManyField("accounts.Tax", blank=True, related_name="branches")
    avatar = models.CharField(max_length=255, blank=True)

    class Meta:
        unique_together = (("department", "name"),)

    def __str__(self):
        return self.name


class Room(createdtimestamp_uid, activearchlockedMixin):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    cost_rate = models.CharField(max_length=20, default="none")
    assigned_cost = MoneyField(max_digits=12, decimal_places=2, default=0, default_currency="GHS")
    staff = models.ForeignKey("party.User", null=True, blank=True, on_delete=models.SET_NULL, related_name="managed_rooms")
    location = models.ForeignKey("contact.Address", null=True, blank=True, on_delete=models.SET_NULL, related_name="rooms")
    floor_number = models.CharField(max_length=10, blank=True)
    capacity = models.PositiveIntegerField(default=0)
    restricted_access = models.BooleanField(default=False)
    status = models.CharField(max_length=20, default="available")
    assigned_branch = models.ManyToManyField(Branch, blank=True, related_name="rooms")
    assigned_staff = models.ManyToManyField("party.Staff", blank=True, related_name="roomassignedstaff")

    def __str__(self):
        return self.name


class Shelfing(createdtimestamp_uid, activearchlockedMixin):
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name="branchshelf")
    room = models.ForeignKey(Room, null=True, blank=True, on_delete=models.SET_NULL, related_name="shelves")
    shelf = models.CharField(max_length=50)

    class Meta:
        unique_together = (("branch", "shelf"),)

    def __str__(self):
        return self.shelf
