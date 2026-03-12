from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.department.api.views import BranchViewSet, DepartmentViewSet, RoomViewSet, ShelfingViewSet, ShiftViewSet

router = DefaultRouter()
router.register("departments", DepartmentViewSet, basename="department")
router.register("branches", BranchViewSet, basename="branch")
router.register("shifts", ShiftViewSet, basename="shift")
router.register("rooms", RoomViewSet, basename="room")
router.register("shelves", ShelfingViewSet, basename="shelf")

urlpatterns = [path("", include(router.urls))]
