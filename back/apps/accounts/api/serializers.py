from apps.accounts.models import Account, Bank, BankAccount, BudgetAllocation, BudgetRequest, BudgetType, Charts_of_account, ExpenseReport, ExpenseType, Tax, Transaction, TransactionDoc, TransactionRequest, TransactionRequestType
from apps.common.api import build_model_serializer

ChartsOfAccountSerializer = build_model_serializer(Charts_of_account)
AccountSerializer = build_model_serializer(Account)
TransactionDocSerializer = build_model_serializer(TransactionDoc)
TransactionSerializer = build_model_serializer(Transaction)
BankSerializer = build_model_serializer(Bank)
BankAccountSerializer = build_model_serializer(BankAccount)
TaxSerializer = build_model_serializer(Tax)
BudgetTypeSerializer = build_model_serializer(BudgetType)
BudgetRequestSerializer = build_model_serializer(BudgetRequest)
BudgetAllocationSerializer = build_model_serializer(BudgetAllocation)
ExpenseTypeSerializer = build_model_serializer(ExpenseType)
ExpenseReportSerializer = build_model_serializer(ExpenseReport)
TransactionRequestTypeSerializer = build_model_serializer(TransactionRequestType)
TransactionRequestSerializer = build_model_serializer(TransactionRequest)
