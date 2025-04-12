from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError  

# Custom User Manager
class CustomUserManager(BaseUserManager):
    def create_user(self, username, university_email, password=None, **extra_fields):
        if not university_email:
            raise ValueError('The University Email must be set')
        
        email = self.normalize_email(university_email)
        user = self.model(
            username=username,
            university_email=email,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, university_email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_admin', True)

        return self.create_user(
            username=username,
            university_email=university_email,
            password=password,
            **extra_fields
        )

    def get_by_natural_key(self, username):
        return self.get(
            models.Q(username__iexact=username) | 
            models.Q(university_email__iexact=username)
        )

class CustomUser(AbstractUser):
    university_email = models.EmailField(
        'university email', 
        unique=True,
        error_messages={
            'unique': "A user with that email already exists.",
        }
    )
    is_student = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    
    objects = CustomUserManager()
    
    def clean(self):
        if not self.university_email.endswith('@astu.edu.et'):
            raise ValidationError("Only @astu.edu.et emails allowed")
    
    def __str__(self):
        return self.username

    class Meta:
        ordering = ['-date_joined']
# Communication Models
class Message(models.Model):
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, 
                             on_delete=models.CASCADE, 
                             related_name='sent_messages')
    receiver = models.ForeignKey(settings.AUTH_USER_MODEL, 
                               on_delete=models.CASCADE, 
                               related_name='received_messages')
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['sender', 'receiver']),
            models.Index(fields=['timestamp']),
        ]

    def __str__(self):
        return f"{self.sender} → {self.receiver}: {self.content[:30]}..."

# Academic Models
class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=10, unique=True)
    
    def __str__(self):
        return f"{self.name} ({self.code})"

class Notice(models.Model):
    PRIORITY_CHOICES = [
        ('H', 'High'),
        ('M', 'Medium'),
        ('L', 'Low')
    ]
    
    title = models.CharField(max_length=200)
    content = models.TextField()
    department = models.ForeignKey(
        'Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notices'
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_notices'
    )
    priority = models.CharField(max_length=1, choices=PRIORITY_CHOICES, default='M')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expiration_date = models.DateTimeField(null=True, blank=True)
    is_pinned = models.BooleanField(default=False)

    class Meta:
        ordering = ['-is_pinned', '-priority', '-created_at']
        indexes = [
            models.Index(fields=['department']),
            models.Index(fields=['created_at']),
        ]
        
    def __str__(self):
        dept = self.department.code if self.department else "All"
        return f"[{dept}] {self.title}"

# Task Management
class Task(models.Model):
    STATUS_CHOICES = [
        ('TODO', 'To Do'),
        ('IN_PROGRESS', 'In Progress'),
        ('DONE', 'Completed')
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL,
                                  on_delete=models.CASCADE,
                                  related_name='assigned_tasks')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='TODO')
    deadline = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['deadline']
        
    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"

# Feedback System
class Feedback(models.Model):
    TYPE_CHOICES = [
        ('BUG', 'Bug Report'),
        ('FEATURE', 'Feature Request'),
        ('GENERAL', 'General Feedback')
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                           on_delete=models.SET_NULL,
                           null=True,
                           blank=True)
    feedback_type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    content = models.TextField()
    is_anonymous = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    response = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.get_feedback_type_display()} by {self.user or 'Anonymous'}"

# Issue Tracking
class IssueReport(models.Model):
    STATUS_CHOICES = [
        ('OPEN', 'Open'),
        ('IN_PROGRESS', 'In Progress'),
        ('RESOLVED', 'Resolved'),
        ('REJECTED', 'Rejected')
    ]
    
    CATEGORY_CHOICES = [
        ('ACADEMIC', 'Academic'),
        ('TECHNICAL', 'Technical'),
        ('FACILITY', 'Facility'),
        ('OTHER', 'Other')
    ]
    
    reporter = models.ForeignKey(settings.AUTH_USER_MODEL,
                               on_delete=models.CASCADE,
                               related_name='reported_issues')
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=10, choices=CATEGORY_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='OPEN')
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL,
                                  on_delete=models.SET_NULL,
                                  null=True,
                                  blank=True,
                                  related_name='assigned_issues')

    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.title} [{self.get_status_display()}]"