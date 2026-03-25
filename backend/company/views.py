from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, permissions, viewsets

from .models import (
    BusinessType,
    Company,
    Industry,
    PaymentClass,
)
from .serializers import (
    BusinessTypeSerializer,
    CompanySerializer,
    IndustrySerializer,
    PaymentClassSerializer,
)


class BaseCompanyViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]


class IndustryViewSet(BaseCompanyViewSet):
    queryset = Industry.objects.all().order_by('name')
    serializer_class = IndustrySerializer
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']


class PaymentClassViewSet(BaseCompanyViewSet):
    queryset = PaymentClass.objects.all().order_by('name')
    serializer_class = PaymentClassSerializer
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']


class BusinessTypeViewSet(BaseCompanyViewSet):
    queryset = BusinessType.objects.all().order_by('name')
    serializer_class = BusinessTypeSerializer
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']


class CompanyViewSet(BaseCompanyViewSet):
    queryset = Company.objects.select_related('industry', 'payment_class', 'business_type').prefetch_related('domains', 'contacts')
    serializer_class = CompanySerializer
    lookup_field = 'slug'
    filterset_fields = ['is_active', 'trade_country', 'default_currency', 'industry', 'payment_class', 'business_type']
    search_fields = ['name', 'trade_name', 'schema_name', 'slug']
    ordering_fields = ['name', 'created_at', 'updated_at']