from django.db import models
from django.utils import timezone  # Better time handling
from django.core.exceptions import ValidationError  # For validation errors
import uuid  # For generating unique identifiers


class Notification(models.Model):
    message = models.TextField()
    anonymous_id = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

class Question(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)  # More flexible than auto_now_add
    updated_at = models.DateTimeField(auto_now=True)  # Track edits
    anonymous_id = models.CharField(max_length=100, blank=True, null=True)  # Explicit null
    
    def __str__(self):
        return self.title[:50]  # Better admin representation

class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    text = models.TextField()
    upvotes = models.PositiveIntegerField(default=0)  # This field exists
    downvotes = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)
    anonymous_id = models.CharField(max_length=100, blank=True, null=True)
    is_accepted = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Answer to: {self.question.title[:30]}"
    def accept(self):
        """Mark this answer as accepted and notify the answer author"""
        self.is_accepted = True
        self.save()
        Notification.objects.create(
            message=f"Your answer to '{self.question.title}' was accepted!",
            anonymous_id=self.anonymous_id
        )
class Comment(models.Model):
    answer = models.ForeignKey(Answer, on_delete=models.CASCADE, null=True, blank=True)
    parent_comment = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)
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
    parent_comment = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='replies'
    )