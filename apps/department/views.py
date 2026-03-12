"""
apps/department/views.py
"""

from rest_framework import viewsets
from apps.common.permissions import IsTenantUser, IsManager
from .models import Department, Branch, Shift, Room, Shelfing
from .serializers import DepartmentSerializer, BranchSerializer, ShiftSerializer, RoomSerializer, ShelfingSerializer


class DepartmentViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [IsTenantUser]
    filterset_fields = ["departmenttype", "is_saledepartment", "is_active"]
    search_fields = ["name", "code"]
    ordering_fields = ["name", "created_at"]


class BranchViewSet(viewsets.ModelViewSet):
    queryset = Branch.objects.select_related("department")
    serializer_class = BranchSerializer
    permission_classes = [IsTenantUser]
    filterset_fields = ["department", "is_warehouse", "is_active"]
    search_fields = ["name", "code"]
    ordering_fields = ["name", "created_at"]


class ShiftViewSet(viewsets.ModelViewSet):
    queryset = Shift.objects.select_related("department")
    serializer_class = ShiftSerializer
    permission_classes = [IsTenantUser]
    filterset_fields = ["department", "shift_types", "is_active"]


class RoomViewSet(viewsets.ModelViewSet):
    queryset = Room.objects.all()
    serializer_class = RoomSerializer
    permission_classes = [IsTenantUser]
    filterset_fields = ["status", "restricted_access", "is_active"]
    search_fields = ["name"]


class ShelfingViewSet(viewsets.ModelViewSet):
    queryset = Shelfing.objects.select_related("branch", "room")
    serializer_class = ShelfingSerializer
    permission_classes = [IsTenantUser]
    filterset_fields = ["branch", "room", "is_active"]
    search_fields = ["shelf"]
