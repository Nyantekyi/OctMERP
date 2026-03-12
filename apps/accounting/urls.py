from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    ChartsOfAccountViewSet,
    AccountViewSet,
    TransactionDocViewSet,
    TransactionViewSet,
    TaxViewSet,
    BankViewSet,
    BankAccountViewSet,
    BudgetTypeViewSet,
    BudgetRequestViewSet,
    BudgetAllocationViewSet,
    ExpenseReportViewSet,
    TransactionRequestTypeViewSet,
    TransactionRequestViewSet,
)

app_name = "accounting"

router = DefaultRouter()
router.register("coa", ChartsOfAccountViewSet, basename="coa")
router.register("accounts", AccountViewSet, basename="account")
router.register("transaction-docs", TransactionDocViewSet, basename="transaction-doc")
router.register("transactions", TransactionViewSet, basename="transaction")
router.register("taxes", TaxViewSet, basename="tax")
router.register("banks", BankViewSet, basename="bank")
router.register("bank-accounts", BankAccountViewSet, basename="bank-account")
router.register("budget-types", BudgetTypeViewSet, basename="budget-type")
router.register("budget-requests", BudgetRequestViewSet, basename="budget-request")
router.register("budget-allocations", BudgetAllocationViewSet, basename="budget-allocation")
router.register("expense-reports", ExpenseReportViewSet, basename="expense-report")
router.register("transaction-request-types", TransactionRequestTypeViewSet, basename="transaction-request-type")
router.register("transaction-requests", TransactionRequestViewSet, basename="transaction-request")

urlpatterns = [path("", include(router.urls))]

