from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.accounts.api.views import AccountViewSet, BankAccountViewSet, BankViewSet, BudgetAllocationViewSet, BudgetRequestViewSet, BudgetTypeViewSet, ChartsOfAccountViewSet, ExpenseReportViewSet, ExpenseTypeViewSet, TaxViewSet, TransactionDocViewSet, TransactionRequestTypeViewSet, TransactionRequestViewSet, TransactionViewSet

router = DefaultRouter()
router.register("charts-of-account", ChartsOfAccountViewSet, basename="chart-of-account")
router.register("accounts", AccountViewSet, basename="account")
router.register("transaction-docs", TransactionDocViewSet, basename="transaction-doc")
router.register("transactions", TransactionViewSet, basename="transaction")
router.register("banks", BankViewSet, basename="bank")
router.register("bank-accounts", BankAccountViewSet, basename="bank-account")
router.register("taxes", TaxViewSet, basename="tax")
router.register("budget-types", BudgetTypeViewSet, basename="budget-type")
router.register("budget-requests", BudgetRequestViewSet, basename="budget-request")
router.register("budget-allocations", BudgetAllocationViewSet, basename="budget-allocation")
router.register("expense-types", ExpenseTypeViewSet, basename="expense-type")
router.register("expense-reports", ExpenseReportViewSet, basename="expense-report")
router.register("transaction-request-types", TransactionRequestTypeViewSet, basename="transaction-request-type")
router.register("transaction-requests", TransactionRequestViewSet, basename="transaction-request")

urlpatterns = [path("", include(router.urls))]
