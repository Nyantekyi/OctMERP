from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers

from .models import (
    Address,
    AddressType,
    City,
    Contact,
    Country,
    Email,
    EmailType,
    Phone,
    PhoneType,
    State,
    Website,
    WebsiteType,
)


class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')


class StateSerializer(serializers.ModelSerializer):
    class Meta:
        model = State
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')


class CitySerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')


class AddressTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AddressType
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')


class PhoneTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PhoneType
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')


class EmailTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailType
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')


class WebsiteTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = WebsiteType
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')


class PhoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Phone
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')


class EmailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Email
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')


class WebsiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Website
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')


class ContactSerializer(serializers.ModelSerializer):
    content_type_label = serializers.CharField(source='content_type.model', read_only=True)
    contact_display = serializers.SerializerMethodField()

    class Meta:
        model = Contact
        fields = (
            'id',
            'content_type',
            'content_type_label',
            'contact_id',
            'contact_display',
            'label',
            'is_verified',
            'is_primary',
            'related_contacts',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at')

    def get_contact_display(self, obj):
        return str(obj.contact_object) if obj.contact_object else None