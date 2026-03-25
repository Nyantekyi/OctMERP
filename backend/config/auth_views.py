from django.contrib.auth import authenticate, login
from rest_framework import serializers
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from knox.views import LoginView as KnoxLoginView


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(trim_whitespace=False, style={'input_type': 'password'})

    def validate(self, attrs):
        request = self.context.get('request')
        user = authenticate(request=request, username=attrs['username'], password=attrs['password'])
        if user is None:
            raise serializers.ValidationError('Unable to log in with the provided credentials.')
        if not user.is_active:
            raise serializers.ValidationError('This user account is inactive.')
        attrs['user'] = user
        return attrs


class UserSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    username = serializers.CharField(read_only=True)
    email = serializers.EmailField(read_only=True)
    first_name = serializers.CharField(read_only=True)
    last_name = serializers.CharField(read_only=True)
    is_staff = serializers.BooleanField(read_only=True)


class KnoxLoginAPIView(KnoxLoginView):
    permission_classes = [AllowAny]

    def post(self, request, format=None):
        serializer = LoginSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        login(request, user)
        request.user = user
        response = super().post(request, format=format)
        response.data['user'] = UserSerializer(user).data
        return response


class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tenant = getattr(request, 'tenant', None)
        return Response(
            {
                'user': UserSerializer(request.user).data,
                'tenant': {
                    'id': str(tenant.id) if tenant else None,
                    'name': getattr(tenant, 'name', None),
                    'schema_name': getattr(tenant, 'schema_name', None),
                },
            }
        )