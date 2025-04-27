from django.urls import path
from .views import (
    # ... other imports ...
    QuestionVoteCreate,
    AnswerVoteCreate
)
from discussion import views

urlpatterns = [
    path('questions/<int:question_id>/vote/', QuestionVoteCreate.as_view(), name='question-vote'),
    path('answers/<int:answer_id>/vote/', AnswerVoteCreate.as_view(), name='answer-vote'),
]