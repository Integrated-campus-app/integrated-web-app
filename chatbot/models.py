from django.db import models

class Conversation(models.Model):
    user = models.ForeignKey('authentication.CustomUser', on_delete=models.CASCADE, null=True)
    updated_at = models.DateTimeField(auto_now=True)  # Track last activity
    is_deleted = models.BooleanField(default=False)  # Add if you want soft delete for conversations
    
    class Meta:
        ordering = ['-updated_at']  # Show most recent first

class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    content = models.TextField()
    is_user = models.BooleanField()
    is_deleted = models.BooleanField(default=False)  # Added soft delete field
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']