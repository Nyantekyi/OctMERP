from rest_framework import viewsets

from apps.accounting.models import AccountingEntry
from apps.accounting.serializers import AccountingEntrySerializer
from apps.customers.permissions import HasTenantModulePermission


class AccountingEntryViewSet(viewsets.ModelViewSet):
    queryset = AccountingEntry.objects.all()
    serializer_class = AccountingEntrySerializer
    permission_classes = [HasTenantModulePermission]
    required_module = "accounting"
