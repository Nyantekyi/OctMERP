"""apps/party/views.py"""

from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView

from apps.common.api import build_action_route, build_model_viewset
from apps.common.permissions import IsManager, IsTenantUser

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
)
from apps.party.serializers import (
    AddressSerializer,
    AgentProfileSerializer,
    ChangePasswordSerializer,
    ClientProfileSerializer,
    ContactPointSerializer,
    CustomTokenObtainPairSerializer,
    DocumentSerializer,
    DocumentTypeSerializer,
    MeSerializer,
    OccupationSerializer,
    RegisterClientSerializer,
    RegisterStaffSerializer,
    RegisterSupplierSerializer,
    StaffProfileSerializer,
    SupplierProfileSerializer,
    UserSerializer,
    UserUpdateSerializer,
)

User = get_user_model()


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class RegisterStaffView(generics.CreateAPIView):
    serializer_class = RegisterStaffSerializer
    permission_classes = [permissions.IsAdminUser]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response({"success": True, "data": UserSerializer(user).data}, status=status.HTTP_201_CREATED)


class RegisterClientView(generics.CreateAPIView):
    serializer_class = RegisterClientSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response({"success": True, "data": UserSerializer(user).data}, status=status.HTTP_201_CREATED)


class RegisterSupplierView(generics.CreateAPIView):
    serializer_class = RegisterSupplierSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response({"success": True, "data": UserSerializer(user).data}, status=status.HTTP_201_CREATED)


class MeView(generics.RetrieveUpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return UserUpdateSerializer
        return MeSerializer

    def get_object(self):
        return self.request.user

    def retrieve(self, request, *args, **kwargs):
        serializer = MeSerializer(request.user)
        return Response({"success": True, "data": serializer.data})

    def partial_update(self, request, *args, **kwargs):
        serializer = UserUpdateSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"success": True, "data": MeSerializer(request.user).data})


class ChangePasswordView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ChangePasswordSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user
        if not user.check_password(serializer.validated_data["old_password"]):
            return Response(
                {"success": False, "errors": {"old_password": [_("Wrong password.")]}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user.set_password(serializer.validated_data["new_password"])
        user.save(update_fields=["password"])
        return Response({"success": True, "data": {"detail": _("Password changed successfully.")}})


def _filter_users(self, queryset):
    user_type = self.request.query_params.get("user_type")
    if user_type:
        queryset = queryset.filter(user_type=user_type)
    return queryset


def _user_permissions(self):
    if self.action in ["destroy", "create"]:
        return [IsManager()]
    return [permission() for permission in self.permission_classes]


def _user_profile(self, request, *args, **kwargs):
    user = self.get_object()
    return Response({"success": True, "data": MeSerializer(user).data})


def _activate_user(self, request, *args, **kwargs):
    user = self.get_object()
    user.is_active = True
    user.save(update_fields=["is_active"])
    return Response({"success": True, "data": {"detail": "User activated."}})


def _deactivate_user(self, request, *args, **kwargs):
    user = self.get_object()
    user.is_active = False
    user.save(update_fields=["is_active"])
    return Response({"success": True, "data": {"detail": "User deactivated."}})


OccupationViewSet = build_model_viewset(
    Occupation,
    OccupationSerializer,
    permission_classes=[IsTenantUser],
    search_fields=["name", "isco_code"],
    ordering_fields=["name", "created_at"],
)

UserViewSet = build_model_viewset(
    User,
    UserSerializer,
    permission_classes=[IsTenantUser],
    search_fields=["email", "first_name", "last_name"],
    filterset_fields=["user_type", "is_active"],
    ordering_fields=["email", "date_joined", "last_name"],
    queryset_handler=_filter_users,
    extra_routes={
        "profile": build_action_route("profile", _user_profile, methods=("get",), detail=True),
        "activate": build_action_route("activate", _activate_user, methods=("post",), detail=True, url_path="activate"),
        "deactivate": build_action_route("deactivate", _deactivate_user, methods=("post",), detail=True, url_path="deactivate"),
    },
    method_overrides={"get_permissions": _user_permissions},
)

StaffProfileViewSet = build_model_viewset(
    StaffProfile,
    StaffProfileSerializer,
    permission_classes=[IsTenantUser],
    search_fields=["user__first_name", "user__last_name", "user__email", "employee_id"],
    filterset_fields=["is_manager", "department", "is_active"],
    ordering_fields=["user__last_name", "created_at"],
    select_related_fields=["user", "department", "occupation"],
    prefetch_related_fields=["branches"],
)

ClientProfileViewSet = build_model_viewset(
    ClientProfile,
    ClientProfileSerializer,
    permission_classes=[IsTenantUser],
    search_fields=["user__first_name", "user__last_name", "user__email"],
    filterset_fields=["tier", "department", "is_active"],
    ordering_fields=["user__last_name", "created_at"],
    select_related_fields=["user", "department", "payment_class"],
)

SupplierProfileViewSet = build_model_viewset(
    SupplierProfile,
    SupplierProfileSerializer,
    permission_classes=[IsTenantUser],
    search_fields=["user__first_name", "user__last_name", "company_name"],
    filterset_fields=["is_approved", "department", "is_active"],
    ordering_fields=["user__last_name", "rating", "created_at"],
    select_related_fields=["user", "department", "payment_class"],
)

AgentProfileViewSet = build_model_viewset(
    AgentProfile,
    AgentProfileSerializer,
    permission_classes=[IsTenantUser],
    filterset_fields=["agent_type", "status", "is_active"],
    select_related_fields=["user"],
)

ContactPointViewSet = build_model_viewset(
    ContactPoint,
    ContactPointSerializer,
    permission_classes=[IsTenantUser],
    filterset_fields=["contact_type", "is_primary", "is_verified"],
)

AddressViewSet = build_model_viewset(
    Address,
    AddressSerializer,
    permission_classes=[IsTenantUser],
    filterset_fields=["address_type", "is_primary", "country", "city"],
    select_related_fields=["city", "state", "country"],
)

DocumentTypeViewSet = build_model_viewset(
    DocumentType,
    DocumentTypeSerializer,
    permission_classes=[IsTenantUser],
    search_fields=["name"],
)

DocumentViewSet = build_model_viewset(
    Document,
    DocumentSerializer,
    permission_classes=[IsTenantUser],
    filterset_fields=["document_type", "content_type"],
    select_related_fields=["document_type"],
)
