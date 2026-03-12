import uuid

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone

from apps.common.models import CompanyMixin, activearchlockedMixin, createdtimestamp_uid


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
        extra_fields.setdefault("user_type", User.UserType.STAFF)
        return self.create_user(email, password, **extra_fields)


class Occupation(createdtimestamp_uid, activearchlockedMixin):
    name = models.CharField(max_length=255, unique=True)
    definition = models.TextField(blank=True)
    task = models.TextField(blank=True)

    def __str__(self):
        return self.name


class User(createdtimestamp_uid, PermissionsMixin, AbstractBaseUser):
    class UserType(models.TextChoices):
        STAFF = "staff", "Staff"
        CLIENT = "client", "Client"
        SUPPLIER = "supplier", "Supplier"
        AGENT = "agent", "Agent"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey("company.Company", null=True, blank=True, on_delete=models.SET_NULL, related_name="users")
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150, blank=True)
    user_type = models.CharField(max_length=20, choices=UserType.choices, default=UserType.STAFF)
    phone = models.CharField(max_length=30, blank=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name"]

    objects = UserManager()

    def __str__(self):
        return self.email

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()


class Staff(createdtimestamp_uid, activearchlockedMixin):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="staff")
    occupation = models.ForeignKey(Occupation, null=True, blank=True, on_delete=models.SET_NULL, related_name="staff_members")
    branches = models.ManyToManyField("department.Branch", blank=True, related_name="staff_members")
    is_manager = models.BooleanField(default=False)
    employee_id = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return self.user.get_full_name() or self.user.email


class Client(createdtimestamp_uid, activearchlockedMixin):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="client")
    department = models.ForeignKey("department.Department", null=True, blank=True, on_delete=models.SET_NULL, related_name="clients")
    loyalty_points = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.user.get_full_name() or self.user.email


class Vendor(createdtimestamp_uid, activearchlockedMixin):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="vendor")
    vendorname = models.CharField(max_length=255)
    department = models.ForeignKey("department.Department", null=True, blank=True, on_delete=models.SET_NULL, related_name="vendors")

    class Meta:
        unique_together = (("vendorname", "department"),)

    def __str__(self):
        return self.vendorname
