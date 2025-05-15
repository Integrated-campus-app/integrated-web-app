from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'departments', views.DepartmentViewSet)
router.register(r'admins', views.AdminProfileViewSet)
router.register(r'issues', views.IssueViewSet)
router.register(r'audit-logs', views.AuditLogViewSet)
router.register(r'metrics', views.SystemMetricsViewSet)

urlpatterns = [
    path('', include(router.urls)),
] 