from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from apps.common.api import build_model_serializer
from apps.party.models import Client, Occupation, Staff, Vendor

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ("email", "first_name", "last_name", "password", "phone", "company", "user_type")

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User.objects.create_user(password=password, **validated_data)
        return user


class ERPTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["user_id"] = str(user.id)
        token["email"] = user.email
        token["user_type"] = user.user_type
        token["full_name"] = user.get_full_name()
        token["is_manager"] = bool(getattr(getattr(user, "staff", None), "is_manager", False))
        return token


UserSerializer = build_model_serializer(User, read_only_fields=("last_login", "date_joined"))
OccupationSerializer = build_model_serializer(Occupation)
StaffSerializer = build_model_serializer(Staff)
ClientSerializer = build_model_serializer(Client)
VendorSerializer = build_model_serializer(Vendor)
