"""
apps/accounting/serializers.py

DRF serializers for accounting models.
"""

from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

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
)


class ChartsOfAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChartsOfAccount
        fields = [
            "id", "acc_number", "name", "description",
            "account_type", "account_balance_type",
            "is_system_account", "allow_direct_posting",
            "is_active", "is_archived", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "acc_number", "account_balance_type", "created_at", "updated_at"]


class AccountSerializer(serializers.ModelSerializer):
    account_type_name = serializers.CharField(source="account_type.name", read_only=True)
    running_balance = serializers.DecimalField(
        max_digits=20, decimal_places=2, read_only=True
    )

    class Meta:
        model = Account
        fields = [
            "id", "acc_number", "currency",
            "account_type", "account_type_name",
            "content_type", "object_id",
            "notes", "running_balance",
            "is_active", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "acc_number", "created_at", "updated_at"]


class TransactionDocSerializer(serializers.ModelSerializer):
    class Meta:
        model = TransactionDoc
        fields = [
            "id", "date", "description", "reference", "posted",
            "content_type", "object_id",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class TransactionSerializer(serializers.ModelSerializer):
    account_name = serializers.CharField(source="account.account_type.name", read_only=True)
    account_number = serializers.IntegerField(source="account.acc_number", read_only=True)

    class Meta:
        model = Transaction
        fields = [
            "id", "notes", "account", "account_name", "account_number",
            "coa", "transaction_type",
            "amount", "amount_currency",
            "conversion_rate", "amount_default", "amount_default_currency",
            "description", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "coa", "amount_default", "amount_default_currency", "created_at", "updated_at"]


class TaxSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tax
        fields = [
            "id", "name", "description", "effective_date",
            "is_tax_recoverable", "tax_type", "tax",
            "min_tax_amount", "max_tax_amount",
            "min_taxable_amount", "max_taxable_amount",
            "is_active", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "tax_payable_account", "tax_expense_account", "created_at", "updated_at"]


class BankSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bank
        fields = [
            "id", "name", "is_main_branch", "branch_of",
            "swift_code", "country",
            "is_active", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "notes_payable_account", "notes_interest_account", "created_at", "updated_at"]


class BankAccountSerializer(serializers.ModelSerializer):
    bank_name = serializers.CharField(source="bank.name", read_only=True)

    class Meta:
        model = BankAccount
        fields = [
            "id", "bank", "bank_name", "name",
            "account_number", "routing_number", "swift_number",
            "account_type", "currency",
            "is_active", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "cash_account", "created_at", "updated_at"]


class BudgetTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = BudgetType
        fields = [
            "id", "name", "description", "department",
            "assigned_approving_managers",
            "is_active", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class BudgetRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = BudgetRequest
        fields = [
            "id", "budget_type", "amount", "amount_currency",
            "reason", "requested_by", "date_requested",
            "status", "approving_staff", "date_approved",
            "content_type", "object_id",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "date_requested", "date_approved", "created_at", "updated_at"]


class BudgetAllocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = BudgetAllocation
        fields = [
            "id", "budget_request", "transaction",
            "amount", "amount_currency",
            "status", "description",
            "allocated_to", "allocated_by",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class ExpenseReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpenseReport
        fields = [
            "id", "budget_allocation",
            "amount", "amount_currency",
            "returned_amount", "returned_amount_currency",
            "status", "description", "staff", "incurred_on",
            "transaction",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class TransactionRequestTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = TransactionRequestType
        fields = [
            "id", "name", "description", "transaction_type",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class TransactionRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = TransactionRequest
        fields = [
            "id", "transaction_type", "increase_direction",
            "status", "description",
            "amount", "amount_currency",
            "approving_staff", "debit_account", "credit_account",
            "transactiondoc",
            "content_type", "object_id",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
