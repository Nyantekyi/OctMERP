import uuid

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.contrib.postgres.fields import ArrayField
from django.core.validators import RegexValidator
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from apps.common.models import activearchlockedMixin, createdtimestamp_uid


# ---------------------------------------------------------------------------
# Lookup tables
# ---------------------------------------------------------------------------

class Occupation(createdtimestamp_uid, activearchlockedMixin):
    """ISCO-08 occupations — auto-seeded on Company creation."""
    name = models.CharField(max_length=255, unique=True)
    definition = models.TextField(blank=True)
    task = models.TextField(blank=True)

    def __str__(self):
        return self.name


class religion(createdtimestamp_uid):
    """Religious affiliation lookup (for HR / patient profiles)."""
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class id_type(createdtimestamp_uid):
    """National ID type, e.g. National ID Card, Passport, Driver's License."""
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


# ---------------------------------------------------------------------------
# User
# ---------------------------------------------------------------------------

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Users must have an email address.")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_admin", True)
        extra_fields.setdefault("user_type", "staff")
        return self.create_user(email, password, **extra_fields)


class User(createdtimestamp_uid, PermissionsMixin, AbstractBaseUser):
    class UserType(models.TextChoices):
        STAFF = "staff", "Staff"
        CLIENT = "client", "Client"
        SUPPLIER = "supplier", "Supplier"
        AGENT = "agent", "Agent"

    class AuthProvider(models.TextChoices):
        EMAIL = "email", "Email"
        GOOGLE = "google", "Google"
        FACEBOOK = "facebook", "Facebook"
        BASE_AUTH = "base_auth", "Base Auth"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(
        "company.Company", null=True, blank=True, on_delete=models.SET_NULL, related_name="users"
    )
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150, blank=True)
    user_type = models.CharField(max_length=20, choices=UserType.choices, default=UserType.STAFF)
    phone = models.CharField(max_length=30, blank=True)

    # Access flags
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    is_client = models.BooleanField(default=False)
    is_vendor = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)

    auth_provider = models.CharField(
        max_length=20, choices=AuthProvider.choices, default=AuthProvider.EMAIL
    )
    date_joined = models.DateTimeField(default=timezone.now)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name"]

    objects = UserManager()

    def __str__(self):
        return self.email

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def full_name(self):
        return self.get_full_name()


class PasswordReset(createdtimestamp_uid):
    """One-time password-reset token."""
    email = models.EmailField()
    token = models.CharField(max_length=255, unique=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"PasswordReset({self.email})"


# ---------------------------------------------------------------------------
# Profile
# ---------------------------------------------------------------------------

class Profile(createdtimestamp_uid, activearchlockedMixin):
    """Extended personal profile — OneToOne → User, auto-created on post_save."""
    class Gender(models.TextChoices):
        MALE = "male", "Male"
        FEMALE = "female", "Female"
        OTHER = "other", "Other"
        PREFER_NOT = "prefer_not", "Prefer not to say"

    class MaritalStatus(models.TextChoices):
        SINGLE = "single", "Single"
        MARRIED = "married", "Married"
        DIVORCED = "divorced", "Divorced"
        WIDOWED = "widowed", "Widowed"

    class EducationLevel(models.TextChoices):
        NONE = "none", "None"
        PRIMARY = "primary", "Primary"
        SECONDARY = "secondary", "Secondary"
        TERTIARY = "tertiary", "Tertiary"
        POSTGRAD = "postgrad", "Postgraduate"

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    profile_picture = models.CharField(max_length=500, blank=True)
    gender = models.CharField(max_length=15, choices=Gender.choices, blank=True)
    marital_status = models.CharField(max_length=15, choices=MaritalStatus.choices, blank=True)
    education_level = models.CharField(max_length=15, choices=EducationLevel.choices, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    date_of_death = models.DateField(null=True, blank=True)
    occupation = models.ManyToManyField(Occupation, blank=True)
    religion = models.ForeignKey(religion, null=True, blank=True, on_delete=models.SET_NULL)
    bio = models.TextField(blank=True)
    contact = models.ManyToManyField("contact.Contact", blank=True)

    class Meta:
        permissions = [
            ("can_view_other_profile", "Can view other user profiles"),
            ("can_edit_other_profile", "Can edit other user profiles"),
        ]

    def __str__(self):
        return f"Profile({self.user.email})"


class national(createdtimestamp_uid):
    """National identity document record per user."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="national_ids")
    id_type = models.ForeignKey(id_type, on_delete=models.PROTECT, related_name="national_records")
    national_id = models.CharField(max_length=100)
    issue_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)

    class Meta:
        unique_together = (("user", "id_type", "national_id"),)

    def __str__(self):
        return f"{self.id_type} – {self.national_id}"


# ---------------------------------------------------------------------------
# Groups
# ---------------------------------------------------------------------------

class ClientGroup(createdtimestamp_uid, activearchlockedMixin):
    company = models.ForeignKey(
        "company.Company", null=True, blank=True, on_delete=models.SET_NULL, related_name="client_groups"
    )
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    class Meta:
        unique_together = (("company", "name"),)

    def __str__(self):
        return self.name


class StaffGroup(createdtimestamp_uid, activearchlockedMixin):
    company = models.ForeignKey(
        "company.Company", null=True, blank=True, on_delete=models.SET_NULL, related_name="staff_groups"
    )
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_an_associate_group_of = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.SET_NULL, related_name="associate_groups"
    )

    class Meta:
        unique_together = (("company", "name"),)

    def __str__(self):
        return self.name


# ---------------------------------------------------------------------------
# Profiles by user type
# ---------------------------------------------------------------------------

class Staff(createdtimestamp_uid, activearchlockedMixin):
    """Internal employee profile — linked to a User with is_staff=True."""
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        ARCHIVED = "archived", "Archived"
        LOCKED = "locked", "Locked"
        DELETED = "deleted", "Deleted"

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="staff")
    staffgroup = models.ForeignKey(
        StaffGroup, null=True, blank=True, on_delete=models.SET_NULL, related_name="members"
    )
    occupation = models.ForeignKey(
        Occupation, null=True, blank=True, on_delete=models.SET_NULL, related_name="staff_members"
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    employee_id = models.CharField(max_length=50, blank=True)

    # Branch / department assignments
    branches = models.ManyToManyField("department.Branch", blank=True, related_name="staff_members")
    # departments auto-derived from branches, but stored for quick lookup
    departments = models.ManyToManyField("department.Department", blank=True, related_name="staff_members")

    # Manager flags
    managerial_status = models.BooleanField(default=False)
    managed_by = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="subordinates",
        limit_choices_to={"managerial_status": True},
    )

    # Auto-created ledger accounts (via signal)
    staffaccount = models.ForeignKey(
        "accounts.Account",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="payroll_staff",
    )
    credit_sale_account = models.ForeignKey(
        "accounts.Account",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="credit_sale_staff",
    )
    contact = models.ManyToManyField("contact.Contact", blank=True)

    class Meta:
        permissions = [
            ("can_switch_branch", "Can switch active branch"),
        ]

    def __str__(self):
        return self.user.get_full_name() or self.user.email

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Auto-sync departments from branches
        if self.pk:
            dept_ids = self.branches.values_list("department_id", flat=True)
            self.departments.set(dept_ids)


class Client(createdtimestamp_uid, activearchlockedMixin):
    """Customer profile — linked to a User with is_client=True."""
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        ARCHIVED = "archived", "Archived"
        LOCKED = "locked", "Locked"
        DELETED = "deleted", "Deleted"

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="client")
    department = models.ForeignKey(
        "department.Department",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="clients",
        limit_choices_to={"is_saledepartment": True},
    )
    is_organization = models.BooleanField(default=False)
    client_group = models.ForeignKey(
        ClientGroup, null=True, blank=True, on_delete=models.SET_NULL, related_name="clients"
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    expiration_date = models.DateField(null=True, blank=True)
    loyalty_points = models.PositiveIntegerField(default=0)
    is_creditsale_allowed = models.BooleanField(default=False)

    # Auto-created ledger account
    client_account = models.ForeignKey(
        "accounts.Account",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="client_ar",
    )
    contact = models.ManyToManyField("contact.Contact", blank=True)
    # Family / related clients (e.g. for medical/household records)
    parents = models.ManyToManyField("self", symmetrical=True, blank=True)

    def __str__(self):
        return self.user.get_full_name() or self.user.email


class Vendor(createdtimestamp_uid, activearchlockedMixin):
    """Vendor / supplier profile — may or may not have a User login."""
    class VendorType(models.TextChoices):
        SERVICE_PROVIDER = "service_provider", "Service Provider"
        MANUFACTURER = "manufacturer", "Manufacturer"
        SUPPLIER = "supplier", "Supplier"
        DISTRIBUTOR = "distributor", "Distributor"
        WHOLESALER = "wholesaler", "Wholesaler"

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        ARCHIVED = "archived", "Archived"
        LOCKED = "locked", "Locked"
        DELETED = "deleted", "Deleted"

    company = models.ForeignKey(
        "company.Company", null=True, blank=True, on_delete=models.SET_NULL, related_name="vendors"
    )
    vendorname = models.CharField(max_length=255)
    vendortype = models.CharField(
        max_length=30, choices=VendorType.choices, default=VendorType.SUPPLIER
    )
    user = models.OneToOneField(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="vendor",
        limit_choices_to={"is_vendor": True},
    )
    department = models.ForeignKey(
        "department.Department", null=True, blank=True, on_delete=models.SET_NULL, related_name="vendors"
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)

    # Auto-created ledger account (Accounts Payable) via signal
    vendoraccount = models.OneToOneField(
        "accounts.Account",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="vendor_ap",
    )
    contact = models.ManyToManyField("contact.Contact", blank=True)

    class Meta:
        unique_together = (("company", "vendorname"),)

    def __str__(self):
        return self.vendorname


class AgentProfile(createdtimestamp_uid, activearchlockedMixin):
    """AI agent profile — autonomous entity operating on behalf of the company."""
    class AgentType(models.TextChoices):
        MONITOR = "monitor", "Monitor"
        EXECUTOR = "executor", "Executor"
        ANALYST = "analyst", "Analyst"
        ASSISTANT = "assistant", "Assistant"

    class AgentStatus(models.TextChoices):
        ACTIVE = "active", "Active"
        PAUSED = "paused", "Paused"
        ERROR = "error", "Error"

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="agent_profile")
    agent_type = models.CharField(max_length=20, choices=AgentType.choices, default=AgentType.ASSISTANT)
    capabilities = models.JSONField(default=list, blank=True)
    assigned_modules = models.JSONField(default=list, blank=True)
    status = models.CharField(max_length=10, choices=AgentStatus.choices, default=AgentStatus.ACTIVE)
    api_key = models.CharField(max_length=255, unique=True, blank=True)

    def __str__(self):
        return f"Agent({self.user.email})"


# ---------------------------------------------------------------------------
# Signals
# ---------------------------------------------------------------------------

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Auto-create a Profile whenever a new User is saved."""
    if created:
        Profile.objects.get_or_create(user=instance)

