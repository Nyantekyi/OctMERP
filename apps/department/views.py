"""apps/department/views.py"""

from apps.common.api import build_model_viewset
from apps.common.permissions import IsTenantUser

from .models import Branch, Department, Room, Shelfing, Shift
from .serializers import BranchSerializer, DepartmentSerializer, RoomSerializer, ShelfingSerializer, ShiftSerializer


DepartmentViewSet = build_model_viewset(
    Department,
    DepartmentSerializer,
    permission_classes=[IsTenantUser],
    filterset_fields=["departmenttype", "is_saledepartment", "is_active"],
    search_fields=["name", "code"],
    ordering_fields=["name", "created_at"],
)

BranchViewSet = build_model_viewset(
    Branch,
    BranchSerializer,
    permission_classes=[IsTenantUser],
    filterset_fields=["department", "is_warehouse", "is_active"],
    search_fields=["name", "code"],
    ordering_fields=["name", "created_at"],
    select_related_fields=["department"],
)

ShiftViewSet = build_model_viewset(
    Shift,
    ShiftSerializer,
    permission_classes=[IsTenantUser],
    filterset_fields=["department", "shift_types", "is_active"],
    select_related_fields=["department"],
)

RoomViewSet = build_model_viewset(
    Room,
    RoomSerializer,
    permission_classes=[IsTenantUser],
    filterset_fields=["status", "restricted_access", "is_active"],
    search_fields=["name"],
)

ShelfingViewSet = build_model_viewset(
    Shelfing,
    ShelfingSerializer,
    permission_classes=[IsTenantUser],
    filterset_fields=["branch", "room", "is_active"],
    search_fields=["shelf"],
    select_related_fields=["branch", "room"],
)
