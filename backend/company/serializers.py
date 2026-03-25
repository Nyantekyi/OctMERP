from rest_framework import serializers

from .models import (
    BusinessType,
    Company,
    Domain,
    Industry,
    PaymentClass,
)


class IndustrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Industry
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')


class PaymentClassSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentClass
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')


class BusinessTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = BusinessType
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')


class DomainSerializer(serializers.ModelSerializer):
    class Meta:
        model = Domain
        fields = ('id', 'domain', 'is_primary', 'tenant', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')


class CompanySerializer(serializers.ModelSerializer):
    domains = DomainSerializer(many=True, read_only=True)
    contacts = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = Company
        fields = (
            'id',
            'name',
            'company_logo',
            'trade_name',
            'incorporation_date',
            'description',
            'motto',
            'schema_name',
            'slug',
            'industry',
            'trade_country',
            'is_active',
            'payment_class',
            'business_type',
            'default_currency',
            'additional_info',
            'contacts',
            'created_at',
            'updated_at',
            'domains',
        )
        read_only_fields = ('id', 'slug', 'created_at', 'updated_at')