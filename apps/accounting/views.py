"""
apps/accounting/views.py

DRF ViewSets for accounting models.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.common.permissions import IsTenantUser, IsManager
from .models import (
    ChartsOfAccount,
    Account,
    TransactionDoc,
    Transaction,
    Tax,
    Bank,
    BankAccount,
    BudgetType,
    BudgetRequest,
    BudgetAllocation,
    ExpenseReport,
    TransactionRequestType,
    TransactionRequest,
    Invoice,
    InvoiceLine,
    Bill,
    BillLine,
    JournalEntry,
    JournalEntryLine,
)
from .serializers import (
    ChartsOfAccountSerializer,
    AccountSerializer,
    TransactionDocSerializer,
    TransactionSerializer,
    TaxSerializer,
    BankSerializer,
    BankAccountSerializer,
    BudgetTypeSerializer,
    BudgetRequestSerializer,
    BudgetAllocationSerializer,
    ExpenseReportSerializer,
    TransactionRequestTypeSerializer,
    TransactionRequestSerializer,
)


class ChartsOfAccountViewSet(viewsets.ModelViewSet):
    queryset = ChartsOfAccount.objects.all()
    serializer_class = ChartsOfAccountSerializer
    permission_classes = [IsTenantUser]
    filterset_fields = ["account_type", "account_balance_type", "is_active"]
    search_fields = ["name", "description"]
    ordering_fields = ["acc_number", "name", "account_type"]


class AccountViewSet(viewsets.ModelViewSet):
    queryset = Account.objects.select_related("account_type")
    serializer_class = AccountSerializer
    permission_classes = [IsTenantUser]
    filterset_fields = ["account_type", "is_active"]
    search_fields = ["name", "acc_number"]
    ordering_fields = ["acc_number", "name"]

    @action(detail=True, methods=["get"])
    def balance(self, request, pk=None):
        acc = self.get_object()
        return Response({"success": True, "data": {"balance": str(acc.running_balance)}})


class TransactionDocViewSet(viewsets.ModelViewSet):
    queryset = TransactionDoc.objects.all()
    serializer_class = TransactionDocSerializer
    permission_classes = [IsTenantUser]
    filterset_fields = ["posted"]
    search_fields = ["description", "reference"]
    ordering_fields = ["date", "created_at"]

    @action(detail=True, methods=["post"])
    def post_doc(self, request, pk=None):
        doc = self.get_object()
        doc.posted = True
        doc.save(update_fields=["posted"])
        return Response({"success": True, "data": TransactionDocSerializer(doc).data})


class TransactionViewSet(viewsets.ModelViewSet):
    queryset = Transaction.objects.select_related("notes", "account", "coa")
    serializer_class = TransactionSerializer
    permission_classes = [IsTenantUser]
    filterset_fields = ["transaction_type", "account"]
    ordering_fields = ["notes__date", "created_at"]


class TaxViewSet(viewsets.ModelViewSet):
    queryset = Tax.objects.all()
    serializer_class = TaxSerializer
    permission_classes = [IsTenantUser]
    filterset_fields = ["tax_type", "is_active", "is_tax_recoverable"]
    search_fields = ["name"]
    ordering_fields = ["name", "effective_date"]


class BankViewSet(viewsets.ModelViewSet):
    queryset = Bank.objects.all()
    serializer_class = BankSerializer
    permission_classes = [IsTenantUser]
    search_fields = ["name"]
    filterset_fields = ["is_active"]


class BankAccountViewSet(viewsets.ModelViewSet):
    queryset = BankAccount.objects.select_related("bank")
    serializer_class = BankAccountSerializer
    permission_classes = [IsTenantUser]
    filterset_fields = ["bank", "account_type", "is_active"]
    search_fields = ["name", "account_number"]


class BudgetTypeViewSet(viewsets.ModelViewSet):
    queryset = BudgetType.objects.select_related("department")
    serializer_class = BudgetTypeSerializer
    permission_classes = [IsTenantUser]
    filterset_fields = ["department", "is_active"]
    search_fields = ["name"]


class BudgetRequestViewSet(viewsets.ModelViewSet):
    queryset = BudgetRequest.objects.select_related("budget_type", "requested_by")
    serializer_class = BudgetRequestSerializer
    permission_classes = [IsTenantUser]
    filterset_fields = ["status", "budget_type"]
    ordering_fields = ["date_requested", "created_at"]

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        obj = self.get_object()
        obj.status = "approved"
        obj.approving_staff = request.user.staff_profile if hasattr(request.user, "staff_profile") else None
        obj.save()
        return Response({"success": True, "data": BudgetRequestSerializer(obj).data})

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        obj = self.get_object()
        obj.status = "rejected"
        obj.save()
        return Response({"success": True, "data": BudgetRequestSerializer(obj).data})


class BudgetAllocationViewSet(viewsets.ModelViewSet):
    queryset = BudgetAllocation.objects.select_related("budget_request")
    serializer_class = BudgetAllocationSerializer
    permission_classes = [IsTenantUser]
    filterset_fields = ["status"]


class ExpenseReportViewSet(viewsets.ModelViewSet):
    queryset = ExpenseReport.objects.select_related("budget_allocation", "staff")
    serializer_class = ExpenseReportSerializer
    permission_classes = [IsTenantUser]
    filterset_fields = ["status", "staff"]
    ordering_fields = ["incurred_on", "created_at"]


class TransactionRequestTypeViewSet(viewsets.ModelViewSet):
    queryset = TransactionRequestType.objects.all()
    serializer_class = TransactionRequestTypeSerializer
    permission_classes = [IsTenantUser]
    search_fields = ["name"]


class TransactionRequestViewSet(viewsets.ModelViewSet):
    queryset = TransactionRequest.objects.select_related("transaction_type", "approving_staff")
    serializer_class = TransactionRequestSerializer
    permission_classes = [IsTenantUser]
    filterset_fields = ["status", "transaction_type"]

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        obj = self.get_object()
        obj.status = "approved"
        obj.save()
        return Response({"success": True, "data": TransactionRequestSerializer(obj).data})

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        obj = self.get_object()
        obj.status = "rejected"
        obj.save()
        return Response({"success": True, "data": TransactionRequestSerializer(obj).data})
