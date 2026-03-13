from rest_framework import viewsets

from apps.customers.permissions import HasTenantModulePermission
from apps.manufacturing.models import WorkOrder
from apps.manufacturing.serializers import WorkOrderSerializer


class WorkOrderViewSet(viewsets.ModelViewSet):
    queryset = WorkOrder.objects.all()
    serializer_class = WorkOrderSerializer
    permission_classes = [HasTenantModulePermission]
    required_module = "manufacturing"
