from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.customers.models import Company
from apps.customers.serializers import CompanySerializer, TenantFeatureSerializer


class CompanyListAPIView(ListAPIView):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer


class TenantFeatureAPIView(APIView):
    def get(self, request):
        tenant = request.tenant
        payload = {
            "schema_name": tenant.schema_name,
            "company_name": tenant.name,
            "company_type": tenant.company_type,
            "enabled_modules": tenant.enabled_modules,
        }
        serializer = TenantFeatureSerializer(payload)
        return Response(serializer.data)
