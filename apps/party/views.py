"""
apps/party/views.py

ViewSets for User, Profiles, Auth, and related Party models.
"""

from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from rest_framework import generics, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView

from apps.common.permissions import IsTenantUser, IsManager, IsSuperUser
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
)
from .serializers import (
    CustomTokenObtainPairSerializer,
    RegisterStaffSerializer,
    RegisterClientSerializer,
    RegisterSupplierSerializer,
    ChangePasswordSerializer,
    OccupationSerializer,
    UserSerializer,
    UserUpdateSerializer,
    StaffProfileSerializer,
    ClientProfileSerializer,
    SupplierProfileSerializer,
    AgentProfileSerializer,
    ContactPointSerializer,
    AddressSerializer,
    DocumentTypeSerializer,
    DocumentSerializer,
    MeSerializer,
)

User = get_user_model()


# ─────────────────────────────────────────────────────────────────────────────
# Auth Views
# ─────────────────────────────────────────────────────────────────────────────

class CustomTokenObtainPairView(TokenObtainPairView):
    """Login — returns JWT with extra claims."""
    serializer_class = CustomTokenObtainPairSerializer


class RegisterStaffView(generics.CreateAPIView):
    serializer_class = RegisterStaffSerializer
    permission_classes = [permissions.IsAdminUser]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {"success": True, "data": UserSerializer(user).data},
            status=status.HTTP_201_CREATED,
        )


class RegisterClientView(generics.CreateAPIView):
    serializer_class = RegisterClientSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {"success": True, "data": UserSerializer(user).data},
            status=status.HTTP_201_CREATED,
        )


class RegisterSupplierView(generics.CreateAPIView):
    serializer_class = RegisterSupplierSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {"success": True, "data": UserSerializer(user).data},
            status=status.HTTP_201_CREATED,
        )


class MeView(generics.RetrieveUpdateAPIView):
    """GET /auth/me/ — returns full current user + profile."""
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
        kwargs["partial"] = True
        serializer = UserUpdateSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"success": True, "data": MeSerializer(request.user).data})


class ChangePasswordView(generics.GenericAPIView):
    """POST /auth/change-password/"""
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


# ─────────────────────────────────────────────────────────────────────────────
# Occupation
# ─────────────────────────────────────────────────────────────────────────────

class OccupationViewSet(viewsets.ModelViewSet):
    queryset = Occupation.objects.all()
    serializer_class = OccupationSerializer
    permission_classes = [IsTenantUser]
    search_fields = ["name", "isco_code"]
    ordering_fields = ["name", "created_at"]
    filterset_fields = []


# ─────────────────────────────────────────────────────────────────────────────
# Users
# ─────────────────────────────────────────────────────────────────────────────

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsTenantUser]
    search_fields = ["email", "first_name", "last_name"]
    filterset_fields = ["user_type", "is_active"]
    ordering_fields = ["email", "date_joined", "last_name"]

    def get_permissions(self):
        if self.action in ["destroy", "create"]:
            return [IsManager()]
        return super().get_permissions()

    def get_queryset(self):
        qs = super().get_queryset()
        user_type = self.request.query_params.get("user_type")
        if user_type:
            qs = qs.filter(user_type=user_type)
        return qs

    @action(detail=True, methods=["get"])
    def profile(self, request, pk=None):
        user = self.get_object()
        serializer = MeSerializer(user)
        return Response({"success": True, "data": serializer.data})

    @action(detail=True, methods=["post"], url_path="activate")
    def activate(self, request, pk=None):
        user = self.get_object()
        user.is_active = True
        user.save(update_fields=["is_active"])
        return Response({"success": True, "data": {"detail": "User activated."}})

    @action(detail=True, methods=["post"], url_path="deactivate")
    def deactivate(self, request, pk=None):
        user = self.get_object()
        user.is_active = False
        user.save(update_fields=["is_active"])
        return Response({"success": True, "data": {"detail": "User deactivated."}})


# ─────────────────────────────────────────────────────────────────────────────
# Staff Profiles
# ─────────────────────────────────────────────────────────────────────────────

class StaffProfileViewSet(viewsets.ModelViewSet):
    queryset = StaffProfile.objects.select_related("user", "department", "occupation").prefetch_related("branches")
    serializer_class = StaffProfileSerializer
    permission_classes = [IsTenantUser]
    search_fields = ["user__first_name", "user__last_name", "user__email", "employee_id"]
    filterset_fields = ["is_manager", "department", "is_active"]
    ordering_fields = ["user__last_name", "created_at"]


class ClientProfileViewSet(viewsets.ModelViewSet):
    queryset = ClientProfile.objects.select_related("user", "department", "payment_class")
    serializer_class = ClientProfileSerializer
    permission_classes = [IsTenantUser]
    search_fields = ["user__first_name", "user__last_name", "user__email"]
    filterset_fields = ["tier", "department", "is_active"]
    ordering_fields = ["user__last_name", "created_at"]


class SupplierProfileViewSet(viewsets.ModelViewSet):
    queryset = SupplierProfile.objects.select_related("user", "department", "payment_class")
    serializer_class = SupplierProfileSerializer
    permission_classes = [IsTenantUser]
    search_fields = ["user__first_name", "user__last_name", "company_name"]
    filterset_fields = ["is_approved", "department", "is_active"]
    ordering_fields = ["user__last_name", "rating", "created_at"]


class AgentProfileViewSet(viewsets.ModelViewSet):
    queryset = AgentProfile.objects.select_related("user")
    serializer_class = AgentProfileSerializer
    permission_classes = [IsTenantUser]
    filterset_fields = ["agent_type", "status", "is_active"]


# ─────────────────────────────────────────────────────────────────────────────
# Contact
# ─────────────────────────────────────────────────────────────────────────────

class ContactPointViewSet(viewsets.ModelViewSet):
    queryset = ContactPoint.objects.all()
    serializer_class = ContactPointSerializer
    permission_classes = [IsTenantUser]
    filterset_fields = ["contact_type", "is_primary", "is_verified"]


class AddressViewSet(viewsets.ModelViewSet):
    queryset = Address.objects.select_related("city", "state", "country")
    serializer_class = AddressSerializer
    permission_classes = [IsTenantUser]
    filterset_fields = ["address_type", "is_primary", "country", "city"]


# ─────────────────────────────────────────────────────────────────────────────
# Documents
# ─────────────────────────────────────────────────────────────────────────────

class DocumentTypeViewSet(viewsets.ModelViewSet):
    queryset = DocumentType.objects.all()
    serializer_class = DocumentTypeSerializer
    permission_classes = [IsTenantUser]
    search_fields = ["name"]


class DocumentViewSet(viewsets.ModelViewSet):
    queryset = Document.objects.select_related("document_type")
    serializer_class = DocumentSerializer
    permission_classes = [IsTenantUser]
    filterset_fields = ["document_type", "content_type"]
