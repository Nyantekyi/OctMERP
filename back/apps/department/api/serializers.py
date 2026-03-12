from apps.common.api import build_model_serializer
from apps.department.models import Branch, Department, Room, Shelfing, Shift

DepartmentSerializer = build_model_serializer(Department)
BranchSerializer = build_model_serializer(Branch)
ShiftSerializer = build_model_serializer(Shift)
RoomSerializer = build_model_serializer(Room)
ShelfingSerializer = build_model_serializer(Shelfing)
