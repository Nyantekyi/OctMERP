from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DepartmentViewSet, BranchViewSet, ShiftViewSet, RoomViewSet, ShelfingViewSet

app_name = "department"

router = DefaultRouter()
router.register("departments", DepartmentViewSet, basename="department")
router.register("branches", BranchViewSet, basename="branch")
router.register("shifts", ShiftViewSet, basename="shift")
router.register("rooms", RoomViewSet, basename="room")
router.register("shelves", ShelfingViewSet, basename="shelf")

urlpatterns = [path("", include(router.urls))]
