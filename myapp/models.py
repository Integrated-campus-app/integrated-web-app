from django.db import models
from django.conf import settings  # Import settings for AUTH_USER_MODEL
from django.contrib.auth.models import AbstractUser  # Import AbstractUser

# Define the CustomUser model first
class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)  # Ensure email is unique
    # Add any additional fields you need

    def __str__(self):
        return self.username

# Define other models after CustomUser
class Message(models.Model):
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_messages')
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message from {self.sender} to {self.receiver}"

class Task(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    completed = models.BooleanField(default=False)

    def __str__(self):
        return self.title

class Notice(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title