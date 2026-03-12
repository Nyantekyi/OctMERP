"""
apps/party/serializers.py

DRF serializers for User, Profiles, Authentication, and Contact models.
"""

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import (
    Occupation,
    StaffProfile,
    ClientProfile,
    SupplierProfile,
    AgentProfile,
    ContactPoint,
    Address,
    DocumentType,
    Document,
    UserType,
)

User = get_user_model()


# ─────────────────────────────────────────────────────────────────────────────
# Auth Serializers
# ─────────────────────────────────────────────────────────────────────────────

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """JWT with extra claims: user_type, is_manager, groups, permissions."""

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["user_id"] = str(user.id)
        token["email"] = user.email
        token["user_type"] = user.user_type
        token["full_name"] = user.get_full_name()
        token["is_superuser"] = user.is_superuser
        token["is_staff"] = user.is_staff
        # Manager flag (staff only)
        try:
            token["is_manager"] = user.staff_profile.is_manager
        except Exception:
            token["is_manager"] = False
        token["groups"] = list(user.groups.values_list("name", flat=True))
        token["permissions"] = list(
            user.get_all_permissions()
        )
        return token


class RegisterStaffSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["email", "first_name", "last_name", "password", "password_confirm", "phone"]

    def validate(self, data):
        if data["password"] != data.pop("password_confirm"):
            raise serializers.ValidationError({"password_confirm": _("Passwords do not match.")})
        return data

    def create(self, validated_data):
        return User.objects.create_user(
            user_type=UserType.STAFF,
            **validated_data,
        )


class RegisterClientSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["email", "first_name", "last_name", "password", "password_confirm", "phone"]

    def validate(self, data):
        if data["password"] != data.pop("password_confirm"):
            raise serializers.ValidationError({"password_confirm": _("Passwords do not match.")})
        return data

    def create(self, validated_data):
        return User.objects.create_user(
            user_type=UserType.CLIENT,
            **validated_data,
        )


class RegisterSupplierSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["email", "first_name", "last_name", "password", "password_confirm", "phone"]

    def validate(self, data):
        if data["password"] != data.pop("password_confirm"):
            raise serializers.ValidationError({"password_confirm": _("Passwords do not match.")})
        return data

    def create(self, validated_data):
        return User.objects.create_user(
            user_type=UserType.SUPPLIER,
            **validated_data,
        )


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(write_only=True)

    def validate(self, data):
        if data["new_password"] != data["new_password_confirm"]:
            raise serializers.ValidationError({"new_password_confirm": _("Passwords do not match.")})
        return data


# ─────────────────────────────────────────────────────────────────────────────
# Occupation
# ─────────────────────────────────────────────────────────────────────────────

class OccupationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Occupation
        fields = ["id", "name", "definition", "task", "isco_code", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


# ─────────────────────────────────────────────────────────────────────────────
# User
# ─────────────────────────────────────────────────────────────────────────────

class UserLightSerializer(serializers.ModelSerializer):
    """Minimal representation for FK/nested use."""
    full_name = serializers.CharField(source="get_full_name", read_only=True)

    class Meta:
        model = User
        fields = ["id", "email", "full_name", "user_type", "avatar"]
        read_only_fields = fields


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source="get_full_name", read_only=True)

    class Meta:
        model = User
        fields = [
            "id", "email", "first_name", "last_name", "full_name",
            "user_type", "avatar", "phone", "is_active", "is_staff",
            "is_superuser", "date_joined", "last_login",
        ]
        read_only_fields = ["id", "is_staff", "is_superuser", "date_joined", "last_login"]


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "avatar", "phone"]


# ─────────────────────────────────────────────────────────────────────────────
# Profiles
# ─────────────────────────────────────────────────────────────────────────────

class StaffProfileSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(source="pk", read_only=True)
    user = UserLightSerializer(read_only=True)
    branches_info = serializers.SerializerMethodField()

    class Meta:
        model = StaffProfile
        fields = [
            "id", "user", "is_manager", "branches", "branches_info", "accounts",
            "department", "occupation",
            "employee_id", "date_of_birth", "hire_date", "national_id",
            "emergency_contact_name", "emergency_contact_phone",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "accounts", "created_at", "updated_at"]

    def get_branches_info(self, obj):
        return [{"id": str(b.id), "name": b.name} for b in obj.branches.all()]


class ClientProfileSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(source="pk", read_only=True)
    user = UserLightSerializer(read_only=True)

    class Meta:
        model = ClientProfile
        fields = [
            "id", "user", "department", "payment_class",
            "loyalty_points", "credit_limit", "payment_terms", "tier",
            "date_of_birth", "national_id", "notes",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "client_account", "created_at", "updated_at"]


class SupplierProfileSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(source="pk", read_only=True)
    user = UserLightSerializer(read_only=True)

    class Meta:
        model = SupplierProfile
        fields = [
            "id", "user", "department", "company_name", "registration_number",
            "payment_class", "tax_id", "payment_terms_days", "is_approved",
            "rating", "notes",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "vendor_account", "rating", "created_at", "updated_at"]


class AgentProfileSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(source="pk", read_only=True)
    user = UserLightSerializer(read_only=True)

    class Meta:
        model = AgentProfile
        fields = [
            "id", "user", "agent_type", "capabilities", "assigned_modules",
            "status", "api_key",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "api_key", "created_at", "updated_at"]


# ─────────────────────────────────────────────────────────────────────────────
# Contact
# ─────────────────────────────────────────────────────────────────────────────

class ContactPointSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactPoint
        fields = [
            "id", "content_type", "object_id",
            "contact_type", "value", "label",
            "is_primary", "is_verified", "is_whatsapp",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class AddressSerializer(serializers.ModelSerializer):
    city_name = serializers.CharField(source="city.name", read_only=True)
    state_name = serializers.CharField(source="state.name", read_only=True)
    country_name = serializers.CharField(source="country.name", read_only=True)

    class Meta:
        model = Address
        fields = [
            "id", "content_type", "object_id",
            "address_type", "line1", "line2",
            "city", "city_name", "state", "state_name",
            "country", "country_name", "postal_code",
            "is_primary", "latitude", "longitude",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "city_name", "state_name", "country_name", "created_at", "updated_at"]


# ─────────────────────────────────────────────────────────────────────────────
# Documents
# ─────────────────────────────────────────────────────────────────────────────

class DocumentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentType
        fields = ["id", "name", "description", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = [
            "id", "document_type", "document_url", "description",
            "custom_fields", "content_type", "object_id",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


# ─────────────────────────────────────────────────────────────────────────────
# Current User (me endpoint)
# ─────────────────────────────────────────────────────────────────────────────

class MeSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source="get_full_name", read_only=True)
    is_manager = serializers.SerializerMethodField()
    profile = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id", "email", "first_name", "last_name", "full_name",
            "user_type", "avatar", "phone",
            "is_active", "is_staff", "is_superuser",
            "date_joined", "last_login",
            "is_manager", "profile",
        ]
        read_only_fields = fields

    def get_is_manager(self, obj):
        try:
            return obj.staff_profile.is_manager
        except Exception:
            return False

    def get_profile(self, obj):
        if obj.user_type == "staff":
            try:
                return StaffProfileSerializer(obj.staff_profile).data
            except Exception:
                return None
        elif obj.user_type == "client":
            try:
                return ClientProfileSerializer(obj.client_profile).data
            except Exception:
                return None
        elif obj.user_type == "supplier":
            try:
                return SupplierProfileSerializer(obj.supplier_profile).data
            except Exception:
                return None
        elif obj.user_type == "agent":
            try:
                return AgentProfileSerializer(obj.agent_profile).data
            except Exception:
                return None
        return None
