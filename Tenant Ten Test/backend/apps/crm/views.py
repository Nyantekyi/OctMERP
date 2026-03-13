from rest_framework import viewsets

from apps.crm.models import Lead
from apps.crm.serializers import LeadSerializer
from apps.customers.permissions import HasTenantModulePermission


class LeadViewSet(viewsets.ModelViewSet):
    queryset = Lead.objects.all()
    serializer_class = LeadSerializer
    permission_classes = [HasTenantModulePermission]
    required_module = "crm"
