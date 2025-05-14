from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'university_email', 'is_admin', 'profile_image']
        read_only_fields = ['id', 'is_admin'] 