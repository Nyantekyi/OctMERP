"""apps/accounting/serializers.py"""

from apps.common.api import build_model_serializer

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


def _account_to_representation(serializer, instance, representation):
    representation["account_type_name"] = getattr(instance.account_type, "name", None)
    representation["running_balance"] = str(instance.running_balance)
    return representation


def _transaction_to_representation(serializer, instance, representation):
    account = getattr(instance, "account", None)
    account_type = getattr(account, "account_type", None)
    representation["account_name"] = getattr(account_type, "name", None)
    representation["account_number"] = getattr(account, "acc_number", None)
    return representation


def _bank_account_to_representation(serializer, instance, representation):
    representation["bank_name"] = getattr(getattr(instance, "bank", None), "name", None)
    return representation


ChartsOfAccountSerializer = build_model_serializer(
    ChartsOfAccount,
    fields=[
        "id", "acc_number", "name", "description",
        "account_type", "account_balance_type",
        "is_system_account", "allow_direct_posting",
        "is_active", "is_archived", "created_at", "updated_at",
    ],
    read_only_fields=("acc_number", "account_balance_type"),
)

AccountSerializer = build_model_serializer(
    Account,
    fields=[
        "id", "acc_number", "currency",
        "account_type", "content_type", "object_id",
        "notes", "is_active", "created_at", "updated_at",
    ],
    read_only_fields=("acc_number",),
    to_representation_handler=_account_to_representation,
)

TransactionDocSerializer = build_model_serializer(
    TransactionDoc,
    fields=[
        "id", "date", "description", "reference", "posted",
        "content_type", "object_id",
        "created_at", "updated_at",
    ],
)

TransactionSerializer = build_model_serializer(
    Transaction,
    fields=[
        "id", "notes", "account", "coa", "transaction_type",
        "amount", "amount_currency",
        "conversion_rate", "amount_default", "amount_default_currency",
        "description", "created_at", "updated_at",
    ],
    read_only_fields=("coa", "amount_default", "amount_default_currency"),
    to_representation_handler=_transaction_to_representation,
)

TaxSerializer = build_model_serializer(
    Tax,
    fields=[
        "id", "name", "description", "effective_date",
        "is_tax_recoverable", "tax_type", "tax",
        "min_tax_amount", "max_tax_amount",
        "min_taxable_amount", "max_taxable_amount",
        "is_active", "created_at", "updated_at",
    ],
)

BankSerializer = build_model_serializer(
    Bank,
    fields=[
        "id", "name", "is_main_branch", "branch_of",
        "swift_code", "country",
        "is_active", "created_at", "updated_at",
    ],
)

BankAccountSerializer = build_model_serializer(
    BankAccount,
    fields=[
        "id", "bank", "name",
        "account_number", "routing_number", "swift_number",
        "account_type", "currency",
        "is_active", "created_at", "updated_at",
    ],
    to_representation_handler=_bank_account_to_representation,
)

BudgetTypeSerializer = build_model_serializer(
    BudgetType,
    fields=[
        "id", "name", "description", "department",
        "assigned_approving_managers",
        "is_active", "created_at", "updated_at",
    ],
)

BudgetRequestSerializer = build_model_serializer(
    BudgetRequest,
    fields=[
        "id", "budget_type", "amount", "amount_currency",
        "reason", "requested_by", "date_requested",
        "status", "approving_staff", "date_approved",
        "content_type", "object_id",
        "created_at", "updated_at",
    ],
    read_only_fields=("date_requested", "date_approved"),
)

BudgetAllocationSerializer = build_model_serializer(
    BudgetAllocation,
    fields=[
        "id", "budget_request", "transaction",
        "amount", "amount_currency",
        "status", "description",
        "allocated_to", "allocated_by",
        "created_at", "updated_at",
    ],
)

ExpenseReportSerializer = build_model_serializer(
    ExpenseReport,
    fields=[
        "id", "budget_allocation",
        "amount", "amount_currency",
        "returned_amount", "returned_amount_currency",
        "status", "description", "staff", "incurred_on",
        "transaction",
        "created_at", "updated_at",
    ],
)

TransactionRequestTypeSerializer = build_model_serializer(
    TransactionRequestType,
    fields=[
        "id", "name", "description", "transaction_type",
        "created_at", "updated_at",
    ],
)

TransactionRequestSerializer = build_model_serializer(
    TransactionRequest,
    fields=[
        "id", "transaction_type", "increase_direction",
        "status", "description",
        "amount", "amount_currency",
        "approving_staff", "debit_account", "credit_account",
        "transactiondoc",
        "content_type", "object_id",
        "created_at", "updated_at",
    ],
)
