"""apps/department/serializers.py"""

from apps.common.api import build_model_serializer

from .models import Branch, Department, Room, Shelfing, Shift


def _branch_to_representation(serializer, instance, representation):
    representation["department_name"] = getattr(getattr(instance, "department", None), "name", None)
    return representation


def _shelfing_to_representation(serializer, instance, representation):
    representation["branch_name"] = getattr(getattr(instance, "branch", None), "name", None)
    return representation


DepartmentSerializer = build_model_serializer(Department)
BranchSerializer = build_model_serializer(Branch, to_representation_handler=_branch_to_representation)
ShiftSerializer = build_model_serializer(Shift)
RoomSerializer = build_model_serializer(Room)
ShelfingSerializer = build_model_serializer(Shelfing, to_representation_handler=_shelfing_to_representation)
