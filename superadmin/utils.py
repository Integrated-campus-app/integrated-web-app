from django.utils import timezone
from .models import AuditLog, SystemMetrics
from django.db.models import Avg
from datetime import timedelta

def log_audit_action(user, action, model_name, object_id, details=None):
    """
    Log an audit action performed by a user.
    
    Args:
        user: The user performing the action
        action: The type of action (create, update, delete, etc.)
        model_name: The name of the model being acted upon
        object_id: The ID of the object being acted upon
        details: Additional details about the action (optional)
    """
    AuditLog.objects.create(
        user=user,
        action=action,
        model_name=model_name,
        object_id=object_id,
        details=details or {},
        timestamp=timezone.now()
    )

def update_system_metrics(department):
    """
    Update system metrics for a department.
    
    Args:
        department: The department to update metrics for
    """
    today = timezone.now().date()
    
    # Calculate metrics for the last 24 hours
    last_24h = timezone.now() - timedelta(days=1)
    
    # Get issues created in the last 24 hours
    new_issues = department.issue_set.filter(created_at__gte=last_24h).count()
    
    # Get resolved issues in the last 24 hours
    resolved_issues = department.issue_set.filter(
        status='resolved',
        resolved_at__gte=last_24h
    )
    
    # Calculate average resolution time
    avg_resolution_time = resolved_issues.aggregate(
        avg_time=Avg('resolved_at' - F('created_at'))
    )['avg_time']
    
    # Create or update metrics
    SystemMetrics.objects.update_or_create(
        department=department,
        date=today,
        defaults={
            'new_issues': new_issues,
            'resolved_issues': resolved_issues.count(),
            'avg_resolution_time': avg_resolution_time.total_seconds() if avg_resolution_time else 0
        }
    )

def get_department_performance(department, days=30):
    """
    Get performance metrics for a department over a specified period.
    
    Args:
        department: The department to get metrics for
        days: Number of days to look back (default: 30)
    
    Returns:
        dict: Performance metrics including:
            - total_issues
            - resolved_issues
            - avg_resolution_time
            - high_priority_issues
            - resolution_rate
    """
    start_date = timezone.now() - timedelta(days=days)
    
    # Get all issues in the period
    issues = department.issue_set.filter(created_at__gte=start_date)
    total_issues = issues.count()
    
    # Get resolved issues
    resolved_issues = issues.filter(status='resolved')
    resolved_count = resolved_issues.count()
    
    # Calculate average resolution time
    avg_resolution_time = resolved_issues.aggregate(
        avg_time=Avg('resolved_at' - F('created_at'))
    )['avg_time']
    
    # Get high priority issues
    high_priority = issues.filter(urgency='high').count()
    
    # Calculate resolution rate
    resolution_rate = (resolved_count / total_issues * 100) if total_issues > 0 else 0
    
    return {
        'total_issues': total_issues,
        'resolved_issues': resolved_count,
        'avg_resolution_time': avg_resolution_time.total_seconds() if avg_resolution_time else 0,
        'high_priority_issues': high_priority,
        'resolution_rate': resolution_rate
    } 