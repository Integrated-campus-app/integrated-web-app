from django.db import models
from authentication.models import CustomUser  # Explicit import (better than string reference)

class Conversation(models.Model):
    user = models.ForeignKey(
        CustomUser, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,  # Allow admin/forms to save without user (e.g., guest chats)
        related_name="conversations"  # Enable user.conversations.all()
    )
    title = models.CharField(max_length=100, blank=True)  # Explicit title field (required for SSE)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        ordering = ['-updated_at']
        verbose_name = "Conversation"  # Human-readable name in admin
        verbose_name_plural = "Conversations"

    def __str__(self):
        return f"Chat #{self.id} ({self.title})"  # Helpful for debugging/admin

class Message(models.Model):
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="messages"  # conversation.messages.all()
    )
    content = models.TextField()
    is_user = models.BooleanField(default=False)  # Explicit default
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        verbose_name = "Message"
        verbose_name_plural = "Messages"

    def __str__(self):
        return f"{'User' if self.is_user else 'AI'}: {self.content[:50]}..."