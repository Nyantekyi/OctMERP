from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from djmoney.models.fields import MoneyField

from apps.common.models import activearchlockedMixin, createdtimestamp_uid


default_currency = "GHS"
allowed_currencies = ["GHS", "USD", "EUR", "GBP", "JPY"]


class Charts_of_account(createdtimestamp_uid, activearchlockedMixin):
    ACCOUNT_TYPES = (
        ("asset", "Asset"),
        ("liability", "Liability"),
        ("equity", "Equity"),
        ("income", "Income"),
        ("expense", "Expense"),
    )

    name = models.CharField(max_length=100, unique=True)
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPES)
    acc_number = models.PositiveIntegerField(unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.acc_number} - {self.name}"


class Account(createdtimestamp_uid, activearchlockedMixin):
    accounttype = models.ForeignKey(Charts_of_account, on_delete=models.PROTECT, related_name="accounts")
    name = models.CharField(max_length=150)
    content_type = models.ForeignKey(ContentType, null=True, blank=True, on_delete=models.SET_NULL)
    object_id = models.UUIDField(null=True, blank=True)
    source_object = GenericForeignKey("content_type", "object_id")

    class Meta:
        unique_together = (("accounttype", "name", "content_type", "object_id"),)

    def __str__(self):
        return self.name


class TransactionDoc(createdtimestamp_uid, activearchlockedMixin):
    title = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    content_type = models.ForeignKey(ContentType, null=True, blank=True, on_delete=models.SET_NULL)
    object_id = models.UUIDField(null=True, blank=True)
    source_object = GenericForeignKey("content_type", "object_id")

    def __str__(self):
        return self.title


class Transaction(createdtimestamp_uid):
    notes = models.ForeignKey(TransactionDoc, on_delete=models.CASCADE, related_name="transactions")
    account = models.ForeignKey(Account, on_delete=models.PROTECT, related_name="transactions")
    entry_type = models.CharField(max_length=10, choices=(("debit", "Debit"), ("credit", "Credit")))
    amount = MoneyField(max_digits=14, decimal_places=2, default=0, default_currency=default_currency)
    memo = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"{self.entry_type} {self.amount}"


class Bank(createdtimestamp_uid, activearchlockedMixin):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class BankAccount(createdtimestamp_uid, activearchlockedMixin):
    bank = models.ForeignKey(Bank, on_delete=models.CASCADE, related_name="accounts")
    account_number = models.CharField(max_length=50)
    account_name = models.CharField(max_length=150)

    class Meta:
        unique_together = (("bank", "account_number"),)

    def __str__(self):
        return self.account_number


class Tax(createdtimestamp_uid, activearchlockedMixin):
    name = models.CharField(max_length=100, unique=True)
    rate = models.DecimalField(max_digits=7, decimal_places=2, default=0)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class BudgetType(createdtimestamp_uid, activearchlockedMixin):
    name = models.CharField(max_length=100)
    department = models.ForeignKey("department.Department", null=True, blank=True, on_delete=models.SET_NULL, related_name="budget_types")

    class Meta:
        unique_together = (("name", "department"),)

    def __str__(self):
        return self.name


class BudgetRequest(createdtimestamp_uid, activearchlockedMixin):
    budget_type = models.ForeignKey(BudgetType, on_delete=models.CASCADE, related_name="requests")
    requested_by = models.ForeignKey("party.Staff", null=True, blank=True, on_delete=models.SET_NULL, related_name="budget_requests")
    amount = MoneyField(max_digits=14, decimal_places=2, default=0, default_currency=default_currency)
    status = models.CharField(max_length=20, default="draft")
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.budget_type} - {self.amount}"


class BudgetAllocation(createdtimestamp_uid, activearchlockedMixin):
    budget_request = models.ForeignKey(BudgetRequest, on_delete=models.CASCADE, related_name="allocations")
    allocated_by = models.ForeignKey("party.Staff", null=True, blank=True, on_delete=models.SET_NULL, related_name="budget_allocations")
    amount = MoneyField(max_digits=14, decimal_places=2, default=0, default_currency=default_currency)

    def __str__(self):
        return f"{self.amount}"


class ExpenseType(createdtimestamp_uid, activearchlockedMixin):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name


class ExpenseReport(createdtimestamp_uid, activearchlockedMixin):
    expense_type = models.ForeignKey(ExpenseType, null=True, blank=True, on_delete=models.SET_NULL, related_name="reports")
    branch = models.ForeignKey("department.Branch", null=True, blank=True, on_delete=models.SET_NULL, related_name="expense_reports")
    amount = MoneyField(max_digits=14, decimal_places=2, default=0, default_currency=default_currency)
    incurred_on = models.DateTimeField()
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.expense_type} - {self.amount}"


class TransactionRequestType(createdtimestamp_uid, activearchlockedMixin):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class TransactionRequest(createdtimestamp_uid, activearchlockedMixin):
    transaction_type = models.ForeignKey(TransactionRequestType, on_delete=models.CASCADE, related_name="requests")
    amount = MoneyField(max_digits=14, decimal_places=2, default=0, default_currency=default_currency)
    status = models.CharField(max_length=20, default="draft")
    content_type = models.ForeignKey(ContentType, null=True, blank=True, on_delete=models.SET_NULL)
    object_id = models.UUIDField(null=True, blank=True)
    source_object = GenericForeignKey("content_type", "object_id")

    def __str__(self):
        return f"{self.transaction_type} - {self.amount}"
