"""
apps/department/serializers.py
"""

from rest_framework import serializers
from .models import Department, Branch, Shift, Room, Shelfing


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = [
            "id", "name", "code", "departmenttype", "description",
            "staff", "base_markup", "is_marked_up_from",
            "is_saledepartment", "is_onlinesaledepartment",
            "defaultonlinedepartment", "is_creditsale_allowed",
            "is_active", "is_archived", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class BranchSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source="department.name", read_only=True)

    class Meta:
        model = Branch
        fields = [
            "id", "department", "department_name", "name", "code",
            "staff", "address", "is_warehouse", "warehouse_unit",
            "branchaccount", "sale_tax", "avatar",
            "is_active", "is_archived", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class ShiftSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shift
        fields = [
            "id", "shift_types", "start_time", "end_time",
            "department", "staff", "break_duration_minutes",
            "is_active", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class RoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = [
            "id", "name", "description", "cost_rate", "assigned_cost",
            "assigned_cost_currency",
            "staff", "location", "floor_number", "capacity",
            "restricted_access", "status",
            "assigned_branch", "assigned_staff",
            "is_active", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class ShelfingSerializer(serializers.ModelSerializer):
    branch_name = serializers.CharField(source="branch.name", read_only=True)

    class Meta:
        model = Shelfing
        fields = [
            "id", "branch", "branch_name", "room", "shelf",
            "is_active", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
