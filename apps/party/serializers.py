"""apps/party/serializers.py"""

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from apps.common.api import build_model_serializer

from .models import (
    Address,
    AgentProfile,
    ClientProfile,
    ContactPoint,
    Document,
    DocumentType,
    Occupation,
    StaffProfile,
    SupplierProfile,
    UserType,
)

User = get_user_model()


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["user_id"] = str(user.id)
        token["email"] = user.email
        token["user_type"] = user.user_type
        token["full_name"] = user.get_full_name()
        token["is_superuser"] = user.is_superuser
        token["is_staff"] = user.is_staff
        try:
            token["is_manager"] = user.staff_profile.is_manager
        except Exception:
            token["is_manager"] = False
        token["groups"] = list(user.groups.values_list("name", flat=True))
        token["permissions"] = list(user.get_all_permissions())
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
        return User.objects.create_user(user_type=UserType.STAFF, **validated_data)


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
        return User.objects.create_user(user_type=UserType.CLIENT, **validated_data)


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
        return User.objects.create_user(user_type=UserType.SUPPLIER, **validated_data)


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(write_only=True)

    def validate(self, data):
        if data["new_password"] != data["new_password_confirm"]:
            raise serializers.ValidationError({"new_password_confirm": _("Passwords do not match.")})
        return data


def _user_light_to_representation(serializer, instance, representation):
    representation["full_name"] = instance.get_full_name()
    return representation


def _user_to_representation(serializer, instance, representation):
    representation["full_name"] = instance.get_full_name()
    return representation


def _staff_profile_to_representation(serializer, instance, representation):
    representation["branches_info"] = [{"id": str(branch.id), "name": branch.name} for branch in instance.branches.all()]
    return representation


def _address_to_representation(serializer, instance, representation):
    representation["city_name"] = getattr(getattr(instance, "city", None), "name", None)
    representation["state_name"] = getattr(getattr(instance, "state", None), "name", None)
    representation["country_name"] = getattr(getattr(instance, "country", None), "name", None)
    return representation


OccupationSerializer = build_model_serializer(
    Occupation,
    fields=["id", "name", "definition", "task", "isco_code", "created_at", "updated_at"],
)

UserLightSerializer = build_model_serializer(
    User,
    fields=["id", "email", "user_type", "avatar"],
    read_only_fields=("email", "user_type", "avatar"),
    to_representation_handler=_user_light_to_representation,
)

UserSerializer = build_model_serializer(
    User,
    fields=[
        "id", "email", "first_name", "last_name",
        "user_type", "avatar", "phone", "is_active", "is_staff",
        "is_superuser", "date_joined", "last_login",
    ],
    read_only_fields=("is_staff", "is_superuser", "date_joined", "last_login"),
    to_representation_handler=_user_to_representation,
)


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "avatar", "phone"]


StaffProfileSerializer = build_model_serializer(
    StaffProfile,
    fields=[
        "id", "user", "is_manager", "branches", "accounts",
        "department", "occupation",
        "employee_id", "date_of_birth", "hire_date", "national_id",
        "emergency_contact_name", "emergency_contact_phone",
        "created_at", "updated_at",
    ],
    read_only_fields=("accounts",),
    nested_serializers={"user": {"serializer": UserLightSerializer, "read_only": True}},
    to_representation_handler=_staff_profile_to_representation,
)

ClientProfileSerializer = build_model_serializer(
    ClientProfile,
    fields=[
        "id", "user", "department", "payment_class",
        "loyalty_points", "credit_limit", "payment_terms", "tier",
        "date_of_birth", "national_id", "notes",
        "created_at", "updated_at",
    ],
    read_only_fields=("client_account",),
    nested_serializers={"user": {"serializer": UserLightSerializer, "read_only": True}},
)

SupplierProfileSerializer = build_model_serializer(
    SupplierProfile,
    fields=[
        "id", "user", "department", "company_name", "registration_number",
        "payment_class", "tax_id", "payment_terms_days", "is_approved",
        "rating", "notes",
        "created_at", "updated_at",
    ],
    read_only_fields=("vendor_account", "rating"),
    nested_serializers={"user": {"serializer": UserLightSerializer, "read_only": True}},
)

AgentProfileSerializer = build_model_serializer(
    AgentProfile,
    fields=[
        "id", "user", "agent_type", "capabilities", "assigned_modules",
        "status", "api_key",
        "created_at", "updated_at",
    ],
    read_only_fields=("api_key",),
    nested_serializers={"user": {"serializer": UserLightSerializer, "read_only": True}},
)

ContactPointSerializer = build_model_serializer(
    ContactPoint,
    fields=[
        "id", "content_type", "object_id",
        "contact_type", "value", "label",
        "is_primary", "is_verified", "is_whatsapp",
        "created_at", "updated_at",
    ],
)

AddressSerializer = build_model_serializer(
    Address,
    fields=[
        "id", "content_type", "object_id",
        "address_type", "line1", "line2",
        "city", "state", "country", "postal_code",
        "is_primary", "latitude", "longitude",
        "created_at", "updated_at",
    ],
    to_representation_handler=_address_to_representation,
)

DocumentTypeSerializer = build_model_serializer(
    DocumentType,
    fields=["id", "name", "description", "created_at", "updated_at"],
)

DocumentSerializer = build_model_serializer(
    Document,
    fields=[
        "id", "document_type", "document_url", "description",
        "custom_fields", "content_type", "object_id",
        "created_at", "updated_at",
    ],
)


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
        if obj.user_type == "client":
            try:
                return ClientProfileSerializer(obj.client_profile).data
            except Exception:
                return None
        if obj.user_type == "supplier":
            try:
                return SupplierProfileSerializer(obj.supplier_profile).data
            except Exception:
                return None
        if obj.user_type == "agent":
            try:
                return AgentProfileSerializer(obj.agent_profile).data
            except Exception:
                return None
        return None
