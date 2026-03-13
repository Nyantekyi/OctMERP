from rest_framework import serializers

from apps.accounting.models import AccountingEntry


class AccountingEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = AccountingEntry
        fields = ["id", "description", "amount", "currency", "entry_date", "created_at"]
