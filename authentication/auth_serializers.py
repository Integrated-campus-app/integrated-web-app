from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.password_validation import validate_password
from rest_framework.validators import UniqueValidator

User = get_user_model()

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        validators=[validate_password]
    )
    password2 = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
        required=True
    )

    class Meta:
        model = User
        fields = ['username', 'university_email', 'password', 'password2']
        extra_kwargs = {
            'university_email': {'required': True},
            'username': {
                'validators': [
                    UniqueValidator(
                        queryset=User.objects.all(),
                        message="This username is already taken"
                    )
                ]
            }
        }

    def validate_university_email(self, value):
        if not value.endswith('@astu.edu.et'):
            raise serializers.ValidationError("Only @astu.edu.et emails allowed")
        return value

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match"})
        return attrs

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            university_email=validated_data['university_email'],
            password=validated_data['password']
        )
        return user

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        username = attrs.get('username')
        if '@' in username:  # If input looks like email
            try:
                user = User.objects.get(university_email=username)
                attrs['username'] = user.username
            except User.DoesNotExist:
                pass
        
        data = super().validate(attrs)
        
        data.update({
            'user': {
                'id': self.user.id,
                'username': self.user.username,
                'email': self.user.university_email,
                'is_admin': self.user.is_admin
            }
        })
        return data