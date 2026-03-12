from django.contrib.auth import get_user_model
from rest_framework import generics
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from apps.common.api import build_model_viewset
from apps.party.api.serializers import ClientSerializer, ERPTokenObtainPairSerializer, OccupationSerializer, RegisterSerializer, StaffSerializer, UserSerializer, VendorSerializer
from apps.party.models import Client, Occupation, Staff, Vendor

User = get_user_model()

UserViewSet = build_model_viewset(User, UserSerializer, search_fields=("email", "first_name", "last_name"), filterset_fields=("user_type", "is_active", "company"), ordering_fields=("email", "date_joined"))
OccupationViewSet = build_model_viewset(Occupation, OccupationSerializer, search_fields=("name",))
StaffViewSet = build_model_viewset(Staff, StaffSerializer, search_fields=("employee_id",), filterset_fields=("is_manager", "occupation"))
ClientViewSet = build_model_viewset(Client, ClientSerializer, filterset_fields=("department",))
VendorViewSet = build_model_viewset(Vendor, VendorSerializer, search_fields=("vendorname",), filterset_fields=("department",))


class LoginView(TokenObtainPairView):
    serializer_class = ERPTokenObtainPairSerializer


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]


class MeView(APIView):
    def get(self, request):
        return Response(UserSerializer(request.user).data)
