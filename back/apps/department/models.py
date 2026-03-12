from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from djmoney.models.fields import MoneyField

from apps.common.models import activearchlockedMixin, createdtimestamp_uid


class Department(createdtimestamp_uid, activearchlockedMixin):
    class DepartmentType(models.TextChoices):
        WHOLESALE = "Wholesale Unit", "Wholesale Unit"
        RETAIL = "Retail Unit", "Retail Unit"
        MANUFACTURING = "Manufacturing Unit", "Manufacturing Unit"

    name = models.CharField(max_length=100)
    departmenttype = models.CharField(max_length=50, choices=DepartmentType.choices)
    description = models.TextField(blank=True)
    staff = models.ForeignKey(
        "party.User", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="managed_departments",
    )
    base_markup = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    is_marked_up_from = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.SET_NULL, related_name="markup_children"
    )

    # Sale configuration
    is_saledepartment = models.BooleanField(default=False)
    is_onlinesaledepartment = models.BooleanField(default=False)
    defaultonlinedepartment = models.BooleanField(default=False)
    is_creditsale_allowed = models.BooleanField(default=False)
    contact = models.ManyToManyField("contact.Contact", blank=True, related_name="departments")

    class Meta:
        unique_together = (("name", "departmenttype"),)

    def clean(self):
        if self.is_marked_up_from_id and self.is_marked_up_from_id == self.pk:
            raise ValidationError("A department cannot be its own markup parent.")
        if self.is_onlinesaledepartment and not self.is_saledepartment:
            raise ValidationError("An online sale department must also be a sale department.")
        if self.defaultonlinedepartment and not self.is_onlinesaledepartment:
            raise ValidationError("Default online department must be an online sale department.")
        if self.is_creditsale_allowed and not self.is_saledepartment:
            raise ValidationError("Credit sales can only be enabled for sale departments.")

    def save(self, *args, **kwargs):
        # Only one department can be the default online department
        if self.defaultonlinedepartment:
            Department.objects.exclude(pk=self.pk).update(defaultonlinedepartment=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Shift(createdtimestamp_uid, activearchlockedMixin):
    class ShiftType(models.TextChoices):
        MORNING = "Morning Shift", "Morning Shift"
        AFTERNOON = "Afternoon Shift", "Afternoon Shift"
        EVENING = "Evening Shift", "Evening Shift"
        NIGHT = "Night Shift", "Night Shift"

    shift_types = models.CharField(max_length=50, choices=ShiftType.choices)
    start_time = models.TimeField()
    end_time = models.TimeField()
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name="shifts")
    staff = models.ForeignKey(
        "party.User", null=True, blank=True, on_delete=models.SET_NULL, related_name="created_shifts"
    )
    break_duration_minutes = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = (("shift_types", "department"),)

    def clean(self):
        if self.start_time and self.end_time and self.start_time >= self.end_time:
            raise ValidationError("Shift start time must be before end time.")

    def __str__(self):
        return f"{self.shift_types} – {self.department}"


class Branch(createdtimestamp_uid, activearchlockedMixin):
    department = models.ForeignKey(Department, on_delete=models.PROTECT, related_name="branches")
    name = models.CharField(max_length=100)
    staff = models.ForeignKey(
        "party.User", null=True, blank=True, on_delete=models.SET_NULL, related_name="managed_branches"
    )
    address = models.ForeignKey(
        "contact.Address", null=True, blank=True, on_delete=models.SET_NULL, related_name="branches"
    )
    is_warehouse = models.BooleanField(default=False)
    warehouse_unit = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="served_branches",
        limit_choices_to={"is_warehouse": True},
    )
    # Auto-assigned ledger accounts (via signal below)
    branchaccount = models.ManyToManyField("accounts.Account", blank=True, related_name="branches")
    sale_tax = models.ManyToManyField("accounts.Tax", blank=True, related_name="branches")
    contact = models.ManyToManyField("contact.Contact", blank=True, related_name="branches")
    avatar = models.CharField(max_length=255, blank=True)

    class Meta:
        unique_together = (("department", "name"),)

    def __str__(self):
        return self.name


class Room(createdtimestamp_uid, activearchlockedMixin):
    class CostRate(models.TextChoices):
        NONE = "none", "No Cost"
        FIXED = "fixed", "Fixed"
        HOURLY = "hourly", "Hourly"
        DAILY = "daily", "Daily"
        WEEKLY = "weekly", "Weekly"
        MONTHLY = "monthly", "Monthly"

    class RoomStatus(models.TextChoices):
        AVAILABLE = "available", "Available"
        UNAVAILABLE = "unavailable", "Unavailable"

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    cost_rate = models.CharField(max_length=20, choices=CostRate.choices, default=CostRate.NONE)
    assigned_cost = MoneyField(max_digits=12, decimal_places=2, default=0, default_currency="GHS")
    staff = models.ForeignKey(
        "party.User", null=True, blank=True, on_delete=models.SET_NULL, related_name="managed_rooms"
    )
    location = models.ForeignKey(
        "contact.Address", null=True, blank=True, on_delete=models.SET_NULL, related_name="rooms"
    )
    floor_number = models.CharField(max_length=10, blank=True)
    capacity = models.PositiveIntegerField(default=0)
    restricted_access = models.BooleanField(default=False)
    activities = ArrayField(models.CharField(max_length=100), blank=True, default=list)
    status = models.CharField(max_length=20, choices=RoomStatus.choices, default=RoomStatus.AVAILABLE)
    assigned_branch = models.ManyToManyField(Branch, blank=True, related_name="rooms")
    assigned_staff = models.ManyToManyField("party.Staff", blank=True, related_name="roomassignedstaff")

    def __str__(self):
        return self.name


class Shelfing(createdtimestamp_uid, activearchlockedMixin):
    """Physical shelf / bin location within a branch/room."""
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name="branchshelf")
    room = models.ForeignKey(Room, null=True, blank=True, on_delete=models.SET_NULL, related_name="shelves")
    shelf = models.CharField(max_length=50)

    class Meta:
        unique_together = (("branch", "shelf"),)

    def __str__(self):
        return f"{self.branch} / {self.shelf}"


# ---------------------------------------------------------------------------
# Signals — auto-create ledger accounts for every new Branch
# ---------------------------------------------------------------------------

_BRANCH_ACCOUNTS = [
    "Inventory",
    "Accounts Receivable",
    "Cash and Cash Equivalents",
    "Accounts Payable",
    "Wages Payable",
    "Taxes Payable",
    "Capital",
    "Revenue / Income",
    "Operational Income",
    "Regular Expense",
    "Depreciation Expense",
    "Marketing Expenses",
    "Freight Expense",
    "Cost of Goods Sold",
]


@receiver(post_save, sender=Branch)
def create_branch_accounts(sender, instance, created, **kwargs):
    """Auto-creates one Account per COA type for each new Branch."""
    if not created:
        return

    from django.apps import apps
    from django.contrib.contenttypes.models import ContentType

    Account = apps.get_model("accounts", "Account")
    Charts_of_account = apps.get_model("accounts", "Charts_of_account")
    ct = ContentType.objects.get_for_model(instance)

    created_accounts = []
    for coa_name in _BRANCH_ACCOUNTS:
        try:
            coa = Charts_of_account.objects.get(name__icontains=coa_name.split()[0])
        except Charts_of_account.DoesNotExist:
            continue
        account, _ = Account.objects.get_or_create(
            accounttype=coa,
            content_type=ct,
            object_id=instance.pk,
            defaults={"name": f"{coa_name} – {instance.name}"},
        )
        created_accounts.append(account)

    if created_accounts:
        instance.branchaccount.set(created_accounts)

