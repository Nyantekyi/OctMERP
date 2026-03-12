from apps.common.api import build_model_viewset
from apps.department.api.serializers import BranchSerializer, DepartmentSerializer, RoomSerializer, ShelfingSerializer, ShiftSerializer
from apps.department.models import Branch, Department, Room, Shelfing, Shift

DepartmentViewSet = build_model_viewset(Department, DepartmentSerializer, search_fields=("name",), filterset_fields=("departmenttype", "is_saledepartment", "is_active"))
BranchViewSet = build_model_viewset(Branch, BranchSerializer, search_fields=("name",), filterset_fields=("department", "is_warehouse", "is_active"))
ShiftViewSet = build_model_viewset(Shift, ShiftSerializer, search_fields=("shift_types",), filterset_fields=("department", "is_active"))
RoomViewSet = build_model_viewset(Room, RoomSerializer, search_fields=("name",), filterset_fields=("status", "restricted_access", "is_active"))
ShelfingViewSet = build_model_viewset(Shelfing, ShelfingSerializer, search_fields=("shelf",), filterset_fields=("branch", "room", "is_active"))
