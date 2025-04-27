from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from .auth_serializers import UserRegistrationSerializer, CustomTokenObtainPairSerializer
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

User = get_user_model()

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

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

@login_required
def current_user(request):
    user = request.user
    return JsonResponse({
        'username': user.username,
        'email': user.email,
        # Add other user fields you need
    })