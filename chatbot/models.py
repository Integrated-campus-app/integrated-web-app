from django.db import models
from django.utils import timezone

class Conversation(models.Model):
    title = models.CharField(max_length=255, default="New Conversation")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self) -> str:
        return f"{self.title} ({self.id})"

    def soft_delete(self) -> None:
        """Soft delete the conversation."""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()

    def restore(self) -> None:
        """Restore a deleted conversation."""
        self.is_deleted = False
        self.deleted_at = None
        self.save()

class Message(models.Model):
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    content = models.TextField()
    is_user = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    source_documents = models.JSONField(null=True, blank=True)  # Store document references used for the response
    attachments = models.JSONField(null=True, blank=True)  # Store file attachments

    class Meta:
        ordering = ['created_at']

    def __str__(self) -> str:
        return f"{'User' if self.is_user else 'Bot'}: {self.content[:50]}..."