from django.db import models
from django.utils import timezone  # Better time handling
from django.core.exceptions import ValidationError  # For validation errors
import uuid  # For generating unique identifiers


class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('answer_accepted', 'Answer Accepted'),
        ('new_answer', 'New Answer'),
        ('new_comment', 'New Comment'),
        ('question_updated', 'Question Updated'),
        ('answer_updated', 'Answer Updated'),
        ('report_resolved', 'Report Resolved'),
    ]

    message = models.TextField()
    user = models.ForeignKey('authentication.CustomUser', on_delete=models.CASCADE, null=True, blank=True)
    anonymous_id = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    is_read = models.BooleanField(default=False)
    notification_type = models.CharField(
        max_length=20, 
        choices=NOTIFICATION_TYPES,
        default='new_answer'  # Adding default value
    )
    related_question = models.ForeignKey('Question', on_delete=models.CASCADE, null=True, blank=True)
    related_answer = models.ForeignKey('Answer', on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['anonymous_id', '-created_at']),
            models.Index(fields=['is_read']),
        ]

    def mark_as_read(self):
        self.is_read = True
        self.save(update_fields=['is_read'])

class Question(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('closed', 'Closed'),
        ('deleted', 'Deleted'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    anonymous_id = models.CharField(max_length=100, blank=True, null=True)
    user = models.ForeignKey('authentication.CustomUser', on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    is_anonymous = models.BooleanField(default=False)
    view_count = models.PositiveIntegerField(default=0)
    last_activity = models.DateTimeField(auto_now=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['title']),
            models.Index(fields=['created_at']),
            models.Index(fields=['status']),
        ]
        ordering = ['-last_activity']

    def __str__(self):
        return self.title[:50]

    def increment_view_count(self):
        self.view_count += 1
        self.save(update_fields=['view_count'])

class QuestionReport(models.Model):
    REASON_CHOICES = [
        ('spam', 'Spam'),
        ('inappropriate', 'Inappropriate Content'),
        ('duplicate', 'Duplicate Question'),
        ('off_topic', 'Off Topic'),
        ('other', 'Other'),
    ]

    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='reports')
    reporter = models.ForeignKey('authentication.CustomUser', on_delete=models.SET_NULL, null=True, blank=True)
    reason = models.CharField(max_length=20, choices=REASON_CHOICES)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    is_resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey('authentication.CustomUser', on_delete=models.SET_NULL, null=True, blank=True, related_name='resolved_reports')

    class Meta:
        ordering = ['-created_at']

class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    text = models.TextField()
    upvotes = models.PositiveIntegerField(default=0)
    downvotes = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    anonymous_id = models.CharField(max_length=100, blank=True, null=True)
    user = models.ForeignKey('authentication.CustomUser', on_delete=models.SET_NULL, null=True, blank=True)
    is_accepted = models.BooleanField(default=False)
    is_anonymous = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-is_accepted', '-upvotes', 'created_at']
        indexes = [
            models.Index(fields=['question', '-is_accepted']),
            models.Index(fields=['question', '-upvotes']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"Answer to: {self.question.title[:30]}"

    def accept(self):
        """Mark this answer as accepted and notify the answer author"""
        self.is_accepted = True
        self.save()
        
        # Create notification for answer author
        if self.user:
            Notification.objects.create(
                message=f"Your answer to '{self.question.title}' was accepted!",
                user=self.user
            )
        elif self.anonymous_id:
            Notification.objects.create(
                message=f"Your answer to '{self.question.title}' was accepted!",
                anonymous_id=self.anonymous_id
            )

class AnswerReport(models.Model):
    REASON_CHOICES = [
        ('spam', 'Spam'),
        ('inappropriate', 'Inappropriate Content'),
        ('incorrect', 'Incorrect Information'),
        ('other', 'Other'),
    ]

    answer = models.ForeignKey(Answer, on_delete=models.CASCADE, related_name='reports')
    reporter = models.ForeignKey('authentication.CustomUser', on_delete=models.SET_NULL, null=True, blank=True)
    reason = models.CharField(max_length=20, choices=REASON_CHOICES)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    is_resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey('authentication.CustomUser', on_delete=models.SET_NULL, null=True, blank=True, related_name='resolved_answer_reports')

    class Meta:
        ordering = ['-created_at']

class Comment(models.Model):
    answer = models.ForeignKey(Answer, on_delete=models.CASCADE)
    parent_comment = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='replies'
    )
    text = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    anonymous_id = models.CharField(max_length=100, blank=True, null=True)
    
    def clean(self):
        if not self.answer and not self.parent_comment:
            raise ValidationError("A comment must be associated with either an answer or another comment")
    
    def save(self, *args, **kwargs):
        self.clean()
        if not self.anonymous_id:
            # Set a default anonymous_id if none provided
            self.anonymous_id = "anonymous_" + str(uuid.uuid4())[:8]
        super().save(*args, **kwargs)
        
    def __str__(self):
        return f"Comment on: {self.answer.question.title[:20]}"