from rest_framework import serializers
from .models import Department, AdminProfile, Issue, AuditLog, SystemMetrics
from django.contrib.auth import get_user_model

User = get_user_model()

class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ['id', 'name', 'code', 'description', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'password']
        extra_kwargs = {
            'password': {'write_only': True},
            'email': {'required': True}
        }

    def create(self, validated_data):
        try:
            # Create user with email as both email and username
            user = User.objects.create_user(
                username=validated_data['email'],
                email=validated_data['email'],
                password=validated_data['password'],
                first_name=validated_data.get('first_name', ''),
                last_name=validated_data.get('last_name', ''),
                is_admin=True  # Set is_admin to True for admin users
            )
            return user
        except Exception as e:
            raise serializers.ValidationError(str(e))

class AdminProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    departments = DepartmentSerializer(many=True, read_only=True)
    department_ids = serializers.PrimaryKeyRelatedField(
        queryset=Department.objects.filter(is_active=True),
        many=True,
        write_only=True,
        required=True,
        source='departments'
    )

    class Meta:
        model = AdminProfile
        fields = [
            'id', 'user', 'departments', 'department_ids',
            'permissions', 'is_active', 'created_at', 'updated_at',
            'last_login'
        ]
        read_only_fields = ['created_at', 'updated_at', 'last_login']

    def validate(self, data):
        if not data.get('departments'):
            raise serializers.ValidationError({
                'department_ids': 'At least one department must be selected.'
            })
        return data

    def create(self, validated_data):
        try:
            user_data = validated_data.pop('user')
            departments = validated_data.pop('departments', [])
            
            # Create the user first
            user = UserSerializer().create(user_data)
            
            # Create the admin profile
            admin_profile = AdminProfile.objects.create(
                user=user,
                is_active=validated_data.get('is_active', True),
                permissions=validated_data.get('permissions', {})
            )
            
            # Add departments if provided
            if departments:
                admin_profile.departments.set(departments)
            
            return admin_profile
        except Exception as e:
            # If user creation fails, clean up any created objects
            if 'user' in locals():
                user.delete()
            raise serializers.ValidationError(str(e))

    def update(self, instance, validated_data):
        try:
            user_data = validated_data.pop('user', None)
            departments = validated_data.pop('departments', None)
            
            # Update user if provided
            if user_data:
                user = instance.user
                for attr, value in user_data.items():
                    if attr == 'password':
                        user.set_password(value)
                    else:
                        setattr(user, attr, value)
                user.save()
            
            # Update admin profile fields
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            
            # Update departments if provided
            if departments is not None:
                instance.departments.set(departments)
            
            instance.save()
            return instance
        except Exception as e:
            raise serializers.ValidationError(str(e))

class IssueSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source='department.name', read_only=True)
    reported_by_name = serializers.CharField(source='reported_by.get_full_name', read_only=True)
    assigned_to_name = serializers.CharField(source='assigned_to.user.get_full_name', read_only=True)

    class Meta:
        model = Issue
        fields = [
            'id', 'title', 'description', 'department', 'department_name',
            'reported_by', 'reported_by_name', 'assigned_to', 'assigned_to_name',
            'urgency', 'status', 'created_at', 'updated_at', 'resolved_at',
            'resolution_notes'
        ]
        read_only_fields = ['created_at', 'updated_at', 'resolved_at']

    def validate(self, data):
        if data.get('status') == 'resolved' and not data.get('resolution_notes'):
            raise serializers.ValidationError(
                "Resolution notes are required when marking an issue as resolved."
            )
        return data

class AuditLogSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)

    class Meta:
        model = AuditLog
        fields = [
            'id', 'user', 'user_name', 'action', 'model_name',
            'object_id', 'details', 'ip_address', 'timestamp'
        ]
        read_only_fields = ['timestamp']

class SystemMetricsSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source='department.name', read_only=True)

    class Meta:
        model = SystemMetrics
        fields = [
            'id', 'department', 'department_name', 'date',
            'total_issues', 'resolved_issues', 'avg_resolution_time',
            'admin_response_time', 'satisfaction_rating'
        ] 