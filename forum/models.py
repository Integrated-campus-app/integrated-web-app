# forum/models.py
from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericForeignKey  # Add this
from django.contrib.contenttypes.models import ContentType  # Add this

User = get_user_model()
class Question(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)

class Answer(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)

class Vote(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    answer = models.ForeignKey(Answer, on_delete=models.CASCADE, related_name='votes')
    value = models.SmallIntegerField()  # +1 (upvote) or -1 (downvote)
    voted_at = models.DateTimeField(auto_now_add=True)

class Reply(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    answer = models.ForeignKey(Answer, on_delete=models.CASCADE, related_name='replies')
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    parent_reply = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)  # For nesting

class EditLog(models.Model):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)  # Tracks whether it's a Question/Answer
    object_id = models.PositiveIntegerField()  # Stores the ID of the Question/Answer
    content_object = GenericForeignKey('content_type', 'object_id')  # Magic field to access the actual object
    old_body = models.TextField()  # Previous content before edit
    edited_by = models.ForeignKey(User, on_delete=models.CASCADE)
    edited_at = models.DateTimeField(auto_now_add=True)