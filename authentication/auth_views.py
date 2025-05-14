from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from .auth_serializers import UserRegistrationSerializer, CustomTokenObtainPairSerializer
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.authentication import JWTAuthentication
from .serializers import UserSerializer

User = get_user_model()

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except Exception as e:
            return Response({
                "university_email": ["Invalid email or password"]
            }, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.user
        refresh = serializer.validated_data.get('refresh')
        access = serializer.validated_data.get('access')

        return Response({
            "access": access,
            "refresh": refresh,
            "user": {
                "username": user.username,
                "university_email": user.university_email,
                "is_admin": user.is_admin
            }
        })

class RegisterView(generics.CreateAPIView):
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = CustomTokenObtainPairSerializer.get_token(user)
        return Response({
            "success": True,
             "user": {
              "username": user.username,
             "email": user.university_email,
                "is_admin": user.is_admin
                },
            "tokens": {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
    }
}, status=status.HTTP_201_CREATED)

@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([AllowAny])
def current_user(request):
    try:
        if not request.user.is_authenticated:
            return Response({
                'user': None,
                'isAuthenticated': False
            }, status=status.HTTP_200_OK)
            
        serializer = UserSerializer(request.user)
        return Response({
            'user': serializer.data,
            'isAuthenticated': True
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            'user': None,
            'isAuthenticated': False,
            'error': str(e)
        }, status=status.HTTP_200_OK)

@api_view(['GET'])
def api_root(request):
    return Response({
        'login': request.build_absolute_uri('api/auth/login/'),
        'register': request.build_absolute_uri('api/auth/register/')
    })