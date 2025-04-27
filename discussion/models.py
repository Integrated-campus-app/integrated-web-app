from django.db import models
from django.conf import settings
from django.db.models import Sum
# from .auth import CustomUser

class Question(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    views = models.PositiveIntegerField(default=0)
    is_closed = models.BooleanField(default=False)
    class Meta:
        app_label = 'discussion'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title[:50]} by {self.user.username}"

class Answer(models.Model):
    question = models.ForeignKey(
        Question, 
        on_delete=models.CASCADE,
        related_name='answers'  # Add related_name here
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_accepted = models.BooleanField(default=False)
    weighted_score = models.IntegerField(default=0)

    class Meta:
        ordering = ['-is_accepted', '-created_at']

    def update_score(self):
        self.weighted_score = self.answervote_set.aggregate(Sum('vote'))['vote__sum'] or 0
        self.save()

class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    questions = models.ManyToManyField(Question)

    def __str__(self):
        return self.name

class QuestionVote(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    vote = models.SmallIntegerField(choices=[(1, 'Upvote'), (-1, 'Downvote')])
    
    class Meta:
        unique_together = [['user', 'question']]

class AnswerVote(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    answer = models.ForeignKey(Answer, on_delete=models.CASCADE)
    vote = models.SmallIntegerField(choices=[(1, 'Upvote'), (-1, 'Downvote')])
    
    class Meta:
        unique_together = [['user', 'answer']]
