from apps.accounts.api.serializers import AccountSerializer, BankAccountSerializer, BankSerializer, BudgetAllocationSerializer, BudgetRequestSerializer, BudgetTypeSerializer, ChartsOfAccountSerializer, ExpenseReportSerializer, TaxSerializer, TransactionDocSerializer, TransactionRequestSerializer, TransactionRequestTypeSerializer, TransactionSerializer
from apps.accounts.models import Account, Bank, BankAccount, BudgetAllocation, BudgetRequest, BudgetType, Charts_of_account, ExpenseReport, Tax, Transaction, TransactionDoc, TransactionRequest, TransactionRequestType
from apps.common.api import build_model_viewset

ChartsOfAccountViewSet = build_model_viewset(Charts_of_account, ChartsOfAccountSerializer, search_fields=("name", "acc_number"), filterset_fields=("account_type",))
AccountViewSet = build_model_viewset(Account, AccountSerializer, search_fields=("name",), filterset_fields=("accounttype",))
TransactionDocViewSet = build_model_viewset(TransactionDoc, TransactionDocSerializer, search_fields=("title",))
TransactionViewSet = build_model_viewset(Transaction, TransactionSerializer, filterset_fields=("notes", "account", "entry_type"))
BankViewSet = build_model_viewset(Bank, BankSerializer, search_fields=("name",))
BankAccountViewSet = build_model_viewset(BankAccount, BankAccountSerializer, search_fields=("account_number", "account_name"), filterset_fields=("bank",))
TaxViewSet = build_model_viewset(Tax, TaxSerializer, search_fields=("name",))
BudgetTypeViewSet = build_model_viewset(BudgetType, BudgetTypeSerializer, search_fields=("name",), filterset_fields=("department",))
BudgetRequestViewSet = build_model_viewset(BudgetRequest, BudgetRequestSerializer, filterset_fields=("budget_type", "requested_by", "status"))
BudgetAllocationViewSet = build_model_viewset(BudgetAllocation, BudgetAllocationSerializer, filterset_fields=("budget_request", "allocated_by"))
ExpenseReportViewSet = build_model_viewset(ExpenseReport, ExpenseReportSerializer, filterset_fields=("budget_allocation", "staff"), ordering_fields=("created_at",))
TransactionRequestTypeViewSet = build_model_viewset(TransactionRequestType, TransactionRequestTypeSerializer, search_fields=("name",))
TransactionRequestViewSet = build_model_viewset(TransactionRequest, TransactionRequestSerializer, filterset_fields=("transaction_type", "status"))
