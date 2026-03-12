from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from djmoney.models.fields import MoneyField

from apps.common.models import activearchlockedMixin, createdtimestamp_uid


default_currency = "GHS"
allowed_currencies = ["GHS", "USD", "EUR", "GBP", "JPY"]

# ---------------------------------------------------------------------------
# Chart of Accounts
# ---------------------------------------------------------------------------

# Ranges for auto-numbering per account type
_COA_RANGES = {
    "Assets":           (10100000, 1000),
    "Liabilities":      (20100000, 2000),
    "Capital_Equity":   (30100000, 1000),
    "Revenues_Income":  (40100000, 1000),
    "Expenses":         (50100000, 2000),
}

# Which account type is normally Debit-normal vs Credit-normal
_BALANCE_TYPE_MAP = {
    "Assets":           "Debit",
    "Expenses":         "Debit",
    "Liabilities":      "Credit",
    "Capital_Equity":   "Credit",
    "Revenues_Income":  "Credit",
}


class Charts_of_account(createdtimestamp_uid, activearchlockedMixin):
    ACCOUNT_TYPES = (
        ("Assets",          "Assets"),
        ("Liabilities",     "Liabilities"),
        ("Capital_Equity",  "Capital / Equity"),
        ("Revenues_Income", "Revenues / Income"),
        ("Expenses",        "Expenses"),
    )
    BALANCE_TYPES = (
        ("Debit",  "Debit"),
        ("Credit", "Credit"),
    )

    name = models.CharField(max_length=100, unique=True)
    account_type = models.CharField(max_length=30, choices=ACCOUNT_TYPES)
    account_balance_type = models.CharField(
        max_length=10, choices=BALANCE_TYPES, editable=False, blank=True
    )
    acc_number = models.PositiveIntegerField(unique=True, editable=False)
    description = models.TextField(blank=True)

    def save(self, *args, **kwargs):
        # Auto-set balance type
        self.account_balance_type = _BALANCE_TYPE_MAP.get(self.account_type, "Debit")

        # Auto-assign acc_number if not yet set
        if not self.acc_number:
            base, step = _COA_RANGES.get(self.account_type, (10100000, 1000))
            existing_max = (
                Charts_of_account.objects.filter(account_type=self.account_type)
                .aggregate(mx=models.Max("acc_number"))["mx"]
            )
            self.acc_number = (existing_max + step) if existing_max else base

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.acc_number} – {self.name}"


# ---------------------------------------------------------------------------
# Account  (sub-account, optionally linked to a business object via GenericFK)
# ---------------------------------------------------------------------------

class Account(createdtimestamp_uid, activearchlockedMixin):
    accounttype = models.ForeignKey(
        Charts_of_account, on_delete=models.PROTECT, related_name="accounts"
    )
    name = models.CharField(max_length=150)
    acc_number = models.PositiveIntegerField(unique=True, editable=False)
    # Generic link to the source object that owns this account
    content_type = models.ForeignKey(
        ContentType, null=True, blank=True, on_delete=models.SET_NULL
    )
    object_id = models.UUIDField(null=True, blank=True)
    account_object = GenericForeignKey("content_type", "object_id")

    class Meta:
        unique_together = (("accounttype", "content_type", "object_id"),)

    @property
    def running_balance(self):
        """Sum of debits minus credits (or inverse for credit-normal accounts)."""
        from django.db.models import Sum, Q
        txns = self.transactions.all()
        debits = txns.filter(transaction_type="Debit").aggregate(
            total=Sum("amount")
        )["total"] or 0
        credits = txns.filter(transaction_type="Credit").aggregate(
            total=Sum("amount")
        )["total"] or 0
        if self.accounttype.account_balance_type == "Debit":
            return debits - credits
        return credits - debits

    def save(self, *args, **kwargs):
        if not self.acc_number:
            coa_num = self.accounttype.acc_number if self.accounttype_id else 10100000
            existing_count = Account.objects.filter(accounttype=self.accounttype_id).count()
            self.acc_number = coa_num + existing_count + 1
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.acc_number} – {self.name}"


# ---------------------------------------------------------------------------
# Transaction document & journal entries
# ---------------------------------------------------------------------------

class TransactionDoc(createdtimestamp_uid, activearchlockedMixin):
    """Groups one or more Transaction lines under a single business event."""
    datetimestamp = models.DateTimeField(auto_now=True)
    title = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    content_type = models.ForeignKey(
        ContentType, null=True, blank=True, on_delete=models.SET_NULL
    )
    object_id = models.UUIDField(null=True, blank=True)
    transaction_object = GenericForeignKey("content_type", "object_id")

    def __str__(self):
        return self.title


class Transaction(createdtimestamp_uid):
    """Individual debit or credit journal entry against an Account."""
    notes = models.ForeignKey(TransactionDoc, on_delete=models.CASCADE, related_name="transactions")
    account = models.ForeignKey(Account, on_delete=models.PROTECT, related_name="transactions")
    COA = models.ForeignKey(
        Charts_of_account,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="transactions",
    )
    transaction_type = models.CharField(
        max_length=10, choices=(("Debit", "Debit"), ("Credit", "Credit"))
    )
    amount = MoneyField(max_digits=14, decimal_places=2, default=0, default_currency=default_currency)
    conversion_rate = models.DecimalField(max_digits=10, decimal_places=6, default=1)
    memo = models.CharField(max_length=255, blank=True)

    def save(self, *args, **kwargs):
        # Auto-set COA from the linked account
        if not self.COA_id and self.account_id:
            self.COA_id = self.account.accounttype_id
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.transaction_type} {self.amount}"


# ---------------------------------------------------------------------------
# Payment (abstract base)
# ---------------------------------------------------------------------------

class paymentbase(models.Model):
    """Abstract mixin for any model that records a payment event."""
    class PaymentMethod(models.TextChoices):
        CASH = "cash", "Cash"
        CHEQUE = "cheque", "Cheque"
        BANK_TRANSFER = "bank_transfer", "Bank Transfer"
        MOBILE_MONEY = "mobile_money", "Mobile Money"

    paymentmethod = models.CharField(
        max_length=20, choices=PaymentMethod.choices, default=PaymentMethod.CASH
    )
    reference = models.CharField(max_length=120, blank=True)
    paymentnotes = models.TextField(blank=True)
    transaction = models.ForeignKey(
        TransactionDoc, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    paymentdate = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True


# ---------------------------------------------------------------------------
# Bank & BankAccount
# ---------------------------------------------------------------------------

class Bank(createdtimestamp_uid, activearchlockedMixin):
    name = models.CharField(max_length=100, unique=True)
    ismainbranch = models.BooleanField(default=True)
    location = models.ForeignKey(
        "contact.Address", null=True, blank=True, on_delete=models.SET_NULL, related_name="banks"
    )
    branchof = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.SET_NULL, related_name="sub_branches"
    )
    contact = models.ManyToManyField("contact.Contact", blank=True)
    # Auto-created accounts via signal
    notes_account = models.ForeignKey(
        Account, null=True, blank=True, on_delete=models.SET_NULL, related_name="bank_notes"
    )
    notes_interest_account = models.ForeignKey(
        Account, null=True, blank=True, on_delete=models.SET_NULL, related_name="bank_interest"
    )

    def __str__(self):
        return self.name


class BankAccount(createdtimestamp_uid, activearchlockedMixin):
    """Company bank account (asset)."""
    class AccountType(models.TextChoices):
        SAVINGS = "savings", "Savings"
        CHECKING = "checking", "Checking"
        CURRENT = "current", "Current"

    bank = models.ForeignKey(Bank, on_delete=models.CASCADE, related_name="bank_accounts")
    name = models.CharField(max_length=150)
    account_number = models.CharField(
        max_length=50,
        validators=[RegexValidator(r"^\d+$", "Account number must contain only digits.")],
    )
    routing_number = models.CharField(max_length=50, blank=True)
    swift_number = models.CharField(max_length=20, blank=True)
    account_type = models.CharField(
        max_length=15, choices=AccountType.choices, default=AccountType.CURRENT
    )
    # Auto-created Current Asset account
    cash_account = models.ForeignKey(
        Account, null=True, blank=True, on_delete=models.SET_NULL, related_name="bank_account_asset"
    )

    class Meta:
        unique_together = (("bank", "account_number"),)

    def __str__(self):
        return f"{self.bank.name} – {self.account_number}"


# ---------------------------------------------------------------------------
# Tax
# ---------------------------------------------------------------------------

class Tax(createdtimestamp_uid, activearchlockedMixin):
    class TaxType(models.TextChoices):
        PERCENT = "percent", "Percent"
        AMOUNT = "amount", "Fixed Amount"

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    effectivedate = models.DateField(null=True, blank=True)
    is_tax_recoverable = models.BooleanField(default=False)
    tax_type = models.CharField(max_length=10, choices=TaxType.choices, default=TaxType.PERCENT)
    tax = models.DecimalField(max_digits=7, decimal_places=2, default=0)
    mintaxable_amount = MoneyField(
        max_digits=14, decimal_places=2, default=0, default_currency=default_currency,
        help_text="0 = always applies",
    )
    maxtaxable_amount = MoneyField(
        max_digits=14, decimal_places=2, default=0, default_currency=default_currency,
        help_text="0 = no ceiling",
    )
    # Auto-created accounts
    tax_payable_account = models.ForeignKey(
        Account, null=True, blank=True, on_delete=models.SET_NULL, related_name="tax_payable"
    )
    tax_expense_account = models.ForeignKey(
        Account, null=True, blank=True, on_delete=models.SET_NULL, related_name="tax_expense"
    )

    def clean(self):
        if self.tax_type == self.TaxType.PERCENT and not (0 <= self.tax <= 100):
            raise ValidationError({"tax": "Percent rate must be between 0 and 100."})
        if self.tax_type == self.TaxType.AMOUNT and self.tax < 0:
            raise ValidationError({"tax": "Fixed tax amount cannot be negative."})
        min_amt = self.mintaxable_amount.amount if self.mintaxable_amount else 0
        max_amt = self.maxtaxable_amount.amount if self.maxtaxable_amount else 0
        if min_amt and max_amt and min_amt >= max_amt:
            raise ValidationError("Minimum taxable amount must be less than maximum.")

    def __str__(self):
        return self.name


# ---------------------------------------------------------------------------
# Budget
# ---------------------------------------------------------------------------

class BudgetType(createdtimestamp_uid, activearchlockedMixin):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    department = models.ForeignKey(
        "department.Department", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="budget_types",
    )
    assigned_approving_manager = models.ManyToManyField(
        "party.Staff", blank=True, related_name="approving_budget_types"
    )

    class Meta:
        unique_together = (("name", "department"),)

    def __str__(self):
        return self.name


class BudgetRequest(createdtimestamp_uid, activearchlockedMixin):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        NEEDS_REVISION = "needs_revision", "Needs Revision"
        CANCELLED = "cancelled", "Cancelled"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    budget_type = models.ForeignKey(BudgetType, on_delete=models.CASCADE, related_name="requests")
    # Source of the request — any model
    content_type = models.ForeignKey(ContentType, null=True, blank=True, on_delete=models.SET_NULL)
    object_id = models.UUIDField(null=True, blank=True)
    source_object = GenericForeignKey("content_type", "object_id")
    amount = MoneyField(max_digits=14, decimal_places=2, default=0, default_currency=default_currency)
    reason = models.TextField(blank=True)
    requested_by = models.ForeignKey(
        "party.Staff", null=True, blank=True, on_delete=models.SET_NULL, related_name="budget_requests"
    )
    date_requested = models.DateField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    approving_staff = models.ForeignKey(
        "party.Staff", null=True, blank=True, on_delete=models.SET_NULL, related_name="approved_budgets"
    )
    date_approved = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.budget_type} – {self.amount}"


class BudgetAllocation(createdtimestamp_uid, activearchlockedMixin):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ALLOCATED = "allocated", "Allocated"
        CANCELLED = "cancelled", "Cancelled"

    budget_request = models.ForeignKey(BudgetRequest, on_delete=models.CASCADE, related_name="allocations")
    transaction = models.ForeignKey(
        TransactionDoc, null=True, blank=True, on_delete=models.SET_NULL, related_name="budget_allocations"
    )
    amount = MoneyField(max_digits=14, decimal_places=2, default=0, default_currency=default_currency)
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.PENDING)
    description = models.TextField(blank=True)
    allocated_to = models.ForeignKey(
        "party.Staff", null=True, blank=True, on_delete=models.SET_NULL, related_name="received_allocations"
    )
    allocated_by = models.ForeignKey(
        "party.Staff", null=True, blank=True, on_delete=models.SET_NULL, related_name="given_allocations"
    )

    def __str__(self):
        return f"{self.amount} → {self.allocated_to}"


# ---------------------------------------------------------------------------
# Expense
# ---------------------------------------------------------------------------

class ExpenseReport(createdtimestamp_uid, activearchlockedMixin):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        COMPLETED = "completed", "Completed"
        LOCKED = "locked", "Locked"

    budget_allocation = models.ForeignKey(
        BudgetAllocation,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="expense_reports",
        limit_choices_to={"status": "allocated"},
    )
    branch = models.ForeignKey(
        "department.Branch", null=True, blank=True, on_delete=models.SET_NULL, related_name="expense_reports"
    )
    amount = MoneyField(max_digits=14, decimal_places=2, default=0, default_currency=default_currency)
    returned_amount = MoneyField(max_digits=14, decimal_places=2, default=0, default_currency=default_currency)
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.DRAFT)
    transaction = models.ForeignKey(
        TransactionDoc, null=True, blank=True, on_delete=models.SET_NULL, related_name="expense_reports"
    )
    description = models.TextField(blank=True)
    staff = models.ForeignKey(
        "party.Staff", null=True, blank=True, on_delete=models.SET_NULL, related_name="expense_reports"
    )
    incurred_on = models.DateTimeField()

    def __str__(self):
        return f"{self.amount} on {self.incurred_on}"


# ---------------------------------------------------------------------------
# Transaction Requests
# ---------------------------------------------------------------------------

class TransactionRequestType(createdtimestamp_uid, activearchlockedMixin):
    class TxnType(models.TextChoices):
        EXPENSE = "Expense", "Expense"
        REVENUE = "Revenue", "Revenue"
        TRANSFER = "Transfer", "Transfer"
        ADJUSTMENT = "Adjustment", "Adjustment"
        PAYROLL = "Payroll", "Payroll"
        CREDIT_NOTE = "Credit Note", "Credit Note"
        DEBIT_NOTE = "Debit Note", "Debit Note"
        LOAN = "Loan", "Loan"
        INVESTMENT = "Investment", "Investment"

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    transaction_type = models.CharField(max_length=20, choices=TxnType.choices, blank=True)

    def __str__(self):
        return self.name


class TransactionRequest(createdtimestamp_uid, activearchlockedMixin):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    transaction_type = models.ForeignKey(
        TransactionRequestType, on_delete=models.CASCADE, related_name="requests"
    )
    increase_direction = models.CharField(
        max_length=10, choices=(("debit", "Debit"), ("credit", "Credit"))
    )
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.PENDING)
    description = models.TextField(blank=True)
    amount = MoneyField(max_digits=14, decimal_places=2, default=0, default_currency=default_currency)
    approving_staff = models.ForeignKey(
        "party.Staff", null=True, blank=True, on_delete=models.SET_NULL, related_name="transaction_approvals"
    )
    debit_account = models.ForeignKey(
        Account, null=True, blank=True, on_delete=models.SET_NULL, related_name="debit_requests"
    )
    credit_account = models.ForeignKey(
        Account, null=True, blank=True, on_delete=models.SET_NULL, related_name="credit_requests"
    )
    transactiondoc = models.ForeignKey(
        TransactionDoc, null=True, blank=True, on_delete=models.SET_NULL, related_name="requests"
    )
    # Source of the request — any model
    content_type = models.ForeignKey(ContentType, null=True, blank=True, on_delete=models.SET_NULL)
    object_id = models.UUIDField(null=True, blank=True)
    source_object = GenericForeignKey("content_type", "object_id")

    def __str__(self):
        return f"{self.transaction_type} – {self.amount}"


# ---------------------------------------------------------------------------
# Signals — auto-create Accounts Payable / Receivable accounts on model create
# ---------------------------------------------------------------------------

def _get_or_create_account(coa_name: str, account_name: str, content_type, object_id):
    """Helper to get_or_create an Account from a COA by name."""
    try:
        coa = Charts_of_account.objects.get(name=coa_name)
    except Charts_of_account.DoesNotExist:
        return None
    account, _ = Account.objects.get_or_create(
        accounttype=coa,
        content_type=content_type,
        object_id=object_id,
        defaults={"name": account_name},
    )
    return account


@receiver(post_save, sender="party.Vendor")
def create_vendor_account(sender, instance, created, **kwargs):
    if not created or instance.vendoraccount_id:
        return
    ct = ContentType.objects.get_for_model(instance)
    account = _get_or_create_account("Accounts Payable", f"AP – {instance.vendorname}", ct, instance.pk)
    if account:
        sender.objects.filter(pk=instance.pk).update(vendoraccount=account)


@receiver(post_save, sender="party.Client")
def create_client_account(sender, instance, created, **kwargs):
    if not created or instance.client_account_id:
        return
    ct = ContentType.objects.get_for_model(instance)
    account = _get_or_create_account(
        "Accounts Receivable", f"AR – {instance.user.get_full_name()}", ct, instance.pk
    )
    if account:
        sender.objects.filter(pk=instance.pk).update(client_account=account)


@receiver(post_save, sender=Tax)
def create_tax_accounts(sender, instance, created, **kwargs):
    if not created:
        return
    ct = ContentType.objects.get_for_model(instance)
    if not instance.tax_payable_account_id:
        payable = _get_or_create_account("Taxes Payable", f"Tax Payable – {instance.name}", ct, instance.pk)
        if payable:
            Tax.objects.filter(pk=instance.pk).update(tax_payable_account=payable)
    if not instance.tax_expense_account_id:
        expense = _get_or_create_account("Tax Expense", f"Tax Expense – {instance.name}", ct, instance.pk)
        if expense:
            Tax.objects.filter(pk=instance.pk).update(tax_expense_account=expense)


@receiver(post_save, sender=Bank)
def create_bank_accounts(sender, instance, created, **kwargs):
    if not created:
        return
    ct = ContentType.objects.get_for_model(instance)
    if not instance.notes_account_id:
        notes = _get_or_create_account("Notes Payable", f"Notes Payable – {instance.name}", ct, instance.pk)
        if notes:
            Bank.objects.filter(pk=instance.pk).update(notes_account=notes)
    if not instance.notes_interest_account_id:
        interest = _get_or_create_account("Interest Payable", f"Interest Payable – {instance.name}", ct, instance.pk)
        if interest:
            Bank.objects.filter(pk=instance.pk).update(notes_interest_account=interest)


@receiver(post_save, sender=BankAccount)
def create_bank_account_asset(sender, instance, created, **kwargs):
    if not created or instance.cash_account_id:
        return
    ct = ContentType.objects.get_for_model(instance)
    account = _get_or_create_account(
        "Cash and Cash Equivalents",
        f"Cash – {instance.bank.name} {instance.account_number[-4:]}",
        ct,
        instance.pk,
    )
    if account:
        BankAccount.objects.filter(pk=instance.pk).update(cash_account=account)

