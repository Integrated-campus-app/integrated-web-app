from django.shortcuts import render
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Count, Avg, F, Q
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from .models import Department, AdminProfile, Issue, AuditLog, SystemMetrics
from .serializers import (
    DepartmentSerializer, AdminProfileSerializer, IssueSerializer,
    AuditLogSerializer, SystemMetricsSerializer
)
from .permissions import IsSuperAdmin, IsDepartmentAdmin
from .utils import log_audit_action

class DepartmentViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = []

    def perform_create(self, serializer):
        department = serializer.save()
        try:
            log_audit_action(
                user=self.request.user,
                action='create',
                model_name='Department',
                object_id=department.id,
                details={'name': department.name, 'code': department.code}
            )
        except:
            pass  # Skip audit logging if no user

    def perform_update(self, serializer):
        department = serializer.save()
        try:
            log_audit_action(
                user=self.request.user,
                action='update',
                model_name='Department',
                object_id=department.id,
                details={'name': department.name, 'code': department.code}
            )
        except:
            pass  # Skip audit logging if no user

    @action(detail=True, methods=['get'])
    def metrics(self, request, pk=None):
        department = self.get_object()
        metrics = SystemMetrics.objects.filter(department=department).order_by('-date')[:30]
        serializer = SystemMetricsSerializer(metrics, many=True)
        return Response(serializer.data)

class AdminProfileViewSet(viewsets.ModelViewSet):
    queryset = AdminProfile.objects.all()
    serializer_class = AdminProfileSerializer
    permission_classes = []

    def perform_create(self, serializer):
        admin_profile = serializer.save()
        try:
            log_audit_action(
                user=self.request.user,
                action='create',
                model_name='AdminProfile',
                object_id=admin_profile.id,
                details={
                    'user_id': admin_profile.user.id,
                    'departments': [dept.id for dept in admin_profile.departments.all()]
                }
            )
        except:
            pass  # Skip audit logging if no user

    def perform_update(self, serializer):
        admin_profile = serializer.save()
        try:
            log_audit_action(
                user=self.request.user,
                action='update',
                model_name='AdminProfile',
                object_id=admin_profile.id,
                details={
                    'user_id': admin_profile.user.id,
                    'is_active': admin_profile.is_active,
                    'departments': [dept.id for dept in admin_profile.departments.all()]
                }
            )
        except:
            pass  # Skip audit logging if no user

    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        admin_profile = self.get_object()
        admin_profile.is_active = False
        admin_profile.save()
        log_audit_action(
            user=request.user,
            action='deactivate',
            model_name='AdminProfile',
            object_id=admin_profile.id,
            details={'user_id': admin_profile.user.id}
        )
        return Response({'status': 'admin deactivated'})

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        admin_profile = self.get_object()
        admin_profile.is_active = True
        admin_profile.save()
        log_audit_action(
            user=request.user,
            action='activate',
            model_name='AdminProfile',
            object_id=admin_profile.id,
            details={'user_id': admin_profile.user.id}
        )
        return Response({'status': 'admin activated'})

class IssueViewSet(viewsets.ModelViewSet):
    queryset = Issue.objects.all()
    serializer_class = IssueSerializer
    permission_classes = []

    def get_queryset(self):
        return Issue.objects.all()

    def perform_create(self, serializer):
        issue = serializer.save()  # Remove reported_by since we don't have user
        try:
            log_audit_action(
                user=self.request.user,
                action='create',
                model_name='Issue',
                object_id=issue.id,
                details={
                    'title': issue.title,
                    'department_id': issue.department.id,
                    'urgency': issue.urgency
                }
            )
        except:
            pass  # Skip audit logging if no user

    @action(detail=True, methods=['post'])
    def assign(self, request, pk=None):
        issue = self.get_object()
        admin_id = request.data.get('admin_id')
        try:
            admin = AdminProfile.objects.get(id=admin_id)
            if not admin.is_active:
                return Response(
                    {'error': 'Cannot assign to inactive admin'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            issue.assigned_to = admin
            issue.status = 'assigned'
            issue.save()
            log_audit_action(
                user=request.user,
                action='assign',
                model_name='Issue',
                object_id=issue.id,
                details={
                    'issue_id': issue.id,
                    'admin_id': admin.id
                }
            )
            return Response({'status': 'issue assigned'})
        except AdminProfile.DoesNotExist:
            return Response(
                {'error': 'Admin not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        issue = self.get_object()
        resolution_notes = request.data.get('resolution_notes')
        if not resolution_notes:
            return Response(
                {'error': 'Resolution notes are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        issue.status = 'resolved'
        issue.resolution_notes = resolution_notes
        issue.resolved_at = timezone.now()
        issue.save()
        log_audit_action(
            user=request.user,
            action='update',
            model_name='Issue',
            object_id=issue.id,
            details={
                'status': 'resolved',
                'resolution_notes': resolution_notes
            }
        )
        return Response({'status': 'issue resolved'})

class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    permission_classes = []

    @method_decorator(cache_page(60))  # Cache for 1 minute
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

class SystemMetricsViewSet(viewsets.ModelViewSet):
    queryset = SystemMetrics.objects.all()
    serializer_class = SystemMetricsSerializer
    permission_classes = []

    def get_queryset(self):
        return SystemMetrics.objects.all()

    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        departments = Department.objects.all()
        metrics = {
            'total_departments': departments.count(),
            'active_admins': AdminProfile.objects.filter(is_active=True).count(),
            'pending_issues': Issue.objects.filter(status__in=['pending', 'assigned']).count(),
            'high_priority_issues': Issue.objects.filter(urgency='high', status__in=['pending', 'assigned']).count(),
            'avg_resolution_time': SystemMetrics.objects.all().aggregate(avg_time=Avg('avg_resolution_time'))['avg_time']
        }
        return Response(metrics)
