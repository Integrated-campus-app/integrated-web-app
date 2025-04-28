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
    university_email = serializers.EmailField(required=False)
    username = serializers.CharField(required=False)

    def validate(self, attrs):
        email = attrs.get('university_email')
        username = attrs.get('username')

        if not email and not username:
            raise serializers.ValidationError({
                "university_email": "Email or username is required"
            })

        try:
            if email:
                user = User.objects.get(university_email=email)
            else:
                user = User.objects.get(username=username)
                
            attrs['username'] = user.username  # Required for JWT
        except User.DoesNotExist:
            raise serializers.ValidationError({
                "university_email": "Invalid credentials"
            })

        return super().validate(attrs)