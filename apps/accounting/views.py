"""apps/accounting/views.py"""

from rest_framework.response import Response

from apps.common.api import build_action_route, build_model_viewset
from apps.common.permissions import IsTenantUser

from .models import (
    Account,
    Bank,
    BankAccount,
    BudgetAllocation,
    BudgetRequest,
    BudgetType,
    ChartsOfAccount,
    ExpenseReport,
    Tax,
    Transaction,
    TransactionDoc,
    TransactionRequest,
    TransactionRequestType,
)
from apps.accounting.serializers import (
    AccountSerializer,
    BankAccountSerializer,
    BankSerializer,
    BudgetAllocationSerializer,
    BudgetRequestSerializer,
    BudgetTypeSerializer,
    ChartsOfAccountSerializer,
    ExpenseReportSerializer,
    TaxSerializer,
    TransactionDocSerializer,
    TransactionRequestSerializer,
    TransactionRequestTypeSerializer,
    TransactionSerializer,
)


def _account_balance(self, request, *args, **kwargs):
    account = self.get_object()
    return Response({"success": True, "data": {"balance": str(account.running_balance)}})


def _post_transaction_doc(self, request, *args, **kwargs):
    document = self.get_object()
    document.posted = True
    document.save(update_fields=["posted"])
    return Response({"success": True, "data": TransactionDocSerializer(document, context=self.get_serializer_context()).data})


def _approve_budget_request(self, request, *args, **kwargs):
    budget_request = self.get_object()
    budget_request.status = "approved"
    budget_request.approving_staff = getattr(request.user, "staff_profile", None)
    budget_request.save()
    return Response({"success": True, "data": BudgetRequestSerializer(budget_request, context=self.get_serializer_context()).data})


def _reject_budget_request(self, request, *args, **kwargs):
    budget_request = self.get_object()
    budget_request.status = "rejected"
    budget_request.save()
    return Response({"success": True, "data": BudgetRequestSerializer(budget_request, context=self.get_serializer_context()).data})


def _approve_transaction_request(self, request, *args, **kwargs):
    transaction_request = self.get_object()
    transaction_request.status = "approved"
    transaction_request.save()
    return Response({"success": True, "data": TransactionRequestSerializer(transaction_request, context=self.get_serializer_context()).data})


def _reject_transaction_request(self, request, *args, **kwargs):
    transaction_request = self.get_object()
    transaction_request.status = "rejected"
    transaction_request.save()
    return Response({"success": True, "data": TransactionRequestSerializer(transaction_request, context=self.get_serializer_context()).data})


ChartsOfAccountViewSet = build_model_viewset(
    ChartsOfAccount,
    ChartsOfAccountSerializer,
    permission_classes=[IsTenantUser],
    filterset_fields=["account_type", "account_balance_type", "is_active"],
    search_fields=["name", "description"],
    ordering_fields=["acc_number", "name", "account_type"],
)

AccountViewSet = build_model_viewset(
    Account,
    AccountSerializer,
    permission_classes=[IsTenantUser],
    filterset_fields=["account_type", "currency", "is_active"],
    search_fields=["acc_number", "account_type__name"],
    ordering_fields=["acc_number", "account_type__name", "currency"],
    select_related_fields=["account_type"],
    extra_routes={
        "balance": build_action_route("balance", _account_balance, methods=("get",), detail=True),
    },
)

TransactionDocViewSet = build_model_viewset(
    TransactionDoc,
    TransactionDocSerializer,
    permission_classes=[IsTenantUser],
    filterset_fields=["posted"],
    search_fields=["description", "reference"],
    ordering_fields=["date", "created_at"],
    extra_routes={
        "post_doc": build_action_route("post_doc", _post_transaction_doc, methods=("post",), detail=True),
    },
)

TransactionViewSet = build_model_viewset(
    Transaction,
    TransactionSerializer,
    permission_classes=[IsTenantUser],
    filterset_fields=["transaction_type", "account"],
    ordering_fields=["notes__date", "created_at"],
    select_related_fields=["notes", "account", "coa"],
)

TaxViewSet = build_model_viewset(
    Tax,
    TaxSerializer,
    permission_classes=[IsTenantUser],
    filterset_fields=["tax_type", "is_active", "is_tax_recoverable"],
    search_fields=["name"],
    ordering_fields=["name", "effective_date"],
)

BankViewSet = build_model_viewset(
    Bank,
    BankSerializer,
    permission_classes=[IsTenantUser],
    search_fields=["name"],
    filterset_fields=["is_active"],
)

BankAccountViewSet = build_model_viewset(
    BankAccount,
    BankAccountSerializer,
    permission_classes=[IsTenantUser],
    filterset_fields=["bank", "account_type", "is_active"],
    search_fields=["name", "account_number"],
    select_related_fields=["bank"],
)

BudgetTypeViewSet = build_model_viewset(
    BudgetType,
    BudgetTypeSerializer,
    permission_classes=[IsTenantUser],
    filterset_fields=["department", "is_active"],
    search_fields=["name"],
    select_related_fields=["department"],
)

BudgetRequestViewSet = build_model_viewset(
    BudgetRequest,
    BudgetRequestSerializer,
    permission_classes=[IsTenantUser],
    filterset_fields=["status", "budget_type"],
    ordering_fields=["date_requested", "created_at"],
    select_related_fields=["budget_type", "requested_by"],
    extra_routes={
        "approve": build_action_route("approve", _approve_budget_request, methods=("post",), detail=True),
        "reject": build_action_route("reject", _reject_budget_request, methods=("post",), detail=True),
    },
)

BudgetAllocationViewSet = build_model_viewset(
    BudgetAllocation,
    BudgetAllocationSerializer,
    permission_classes=[IsTenantUser],
    filterset_fields=["status"],
    select_related_fields=["budget_request"],
)

ExpenseReportViewSet = build_model_viewset(
    ExpenseReport,
    ExpenseReportSerializer,
    permission_classes=[IsTenantUser],
    filterset_fields=["status", "staff"],
    ordering_fields=["incurred_on", "created_at"],
    select_related_fields=["budget_allocation", "staff"],
)

TransactionRequestTypeViewSet = build_model_viewset(
    TransactionRequestType,
    TransactionRequestTypeSerializer,
    permission_classes=[IsTenantUser],
    search_fields=["name"],
)

TransactionRequestViewSet = build_model_viewset(
    TransactionRequest,
    TransactionRequestSerializer,
    permission_classes=[IsTenantUser],
    filterset_fields=["status", "transaction_type"],
    select_related_fields=["transaction_type", "approving_staff"],
    extra_routes={
        "approve": build_action_route("approve", _approve_transaction_request, methods=("post",), detail=True),
        "reject": build_action_route("reject", _reject_transaction_request, methods=("post",), detail=True),
    },
)
