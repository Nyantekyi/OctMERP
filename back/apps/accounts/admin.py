from django.contrib import admin

from apps.accounts.models import (
    Account,
    Bank,
    BankAccount,
    BudgetAllocation,
    BudgetRequest,
    BudgetType,
    Charts_of_account,
    ExpenseReport,
    ExpenseType,
    Tax,
    Transaction,
    TransactionDoc,
    TransactionRequest,
    TransactionRequestType,
)


admin.site.register(Charts_of_account)
admin.site.register(Account)
admin.site.register(TransactionDoc)
admin.site.register(Transaction)
admin.site.register(Bank)
admin.site.register(BankAccount)
admin.site.register(Tax)
admin.site.register(BudgetType)
admin.site.register(BudgetRequest)
admin.site.register(BudgetAllocation)
admin.site.register(ExpenseType)
admin.site.register(ExpenseReport)
admin.site.register(TransactionRequestType)
admin.site.register(TransactionRequest)
