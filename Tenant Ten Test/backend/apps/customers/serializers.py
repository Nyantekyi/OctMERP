from rest_framework import serializers

from apps.customers.models import Company


class CompanySerializer(serializers.ModelSerializer):
    enabled_modules = serializers.SerializerMethodField()

    class Meta:
        model = Company
        fields = ["id", "name", "schema_name", "company_type", "enabled_modules"]

    def get_enabled_modules(self, obj: Company) -> list[str]:
        return obj.enabled_modules


class TenantFeatureSerializer(serializers.Serializer):
    schema_name = serializers.CharField()
    company_name = serializers.CharField()
    company_type = serializers.CharField()
    enabled_modules = serializers.ListField(child=serializers.CharField())
