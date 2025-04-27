from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django.db.models import Count, Q
from .models import Question, Answer, Tag, QuestionVote, AnswerVote
from .discussion_serializers import (
    QuestionSerializer,
    AnswerSerializer,
    TagSerializer,
    QuestionVoteSerializer,
    AnswerVoteSerializer
)

class QuestionListCreate(generics.ListCreateAPIView):
    queryset = Question.objects.annotate(
        answers_count=Count('answers')  # This will now work with the related_name
    ).order_by('-created_at')
    serializer_class = QuestionSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_queryset(self):
        queryset = super().get_queryset()
        search_query = self.request.query_params.get('search', None)
        if search_query:
            queryset = queryset.filter(
                models.Q(title__icontains=search_query) |
                models.Q(content__icontains=search_query) |
                models.Q(answers__content__icontains=search_query)
            ).distinct()
        return queryset

class QuestionDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Question.objects.all()
    serializer_class = QuestionSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_update(self, serializer):
        serializer.save(user=self.request.user)

class AnswerListCreate(generics.ListCreateAPIView):
    serializer_class = AnswerSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


    def get_queryset(self):
        question_id = self.kwargs['question_id']
        return Answer.objects.filter(question_id=question_id).annotate(
            weighted_score=models.Count(
                models.Case(
                    models.When(votes__vote=1, then=1),
                    models.When(votes__vote=-1, then=-1),
                    output_field=models.IntegerField()
                )
            )
        ).order_by('-weighted_score', '-created_at')

    def perform_create(self, serializer):
        question_id = self.kwargs['question_id']
        serializer.save(
            question_id=question_id,
            user=self.request.user
        )

# Replace the VoteCreate view with these two separate views:
class QuestionVoteCreate(generics.CreateAPIView):
    serializer_class = QuestionVoteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        question_id = kwargs['question_id']
        vote_value = request.data.get('vote', 0)
        
        if vote_value not in [-1, 1]:
            return Response(
                {'error': 'Invalid vote value. Must be -1 or 1'},
                status=status.HTTP_400_BAD_REQUEST
            )

        question = Question.objects.get(id=question_id)
        vote, created = QuestionVote.objects.update_or_create(
            question=question,
            user=request.user,
            defaults={'vote': vote_value}
        )
        
        return Response(QuestionVoteSerializer(vote).data)

class AnswerVoteCreate(generics.CreateAPIView):
    serializer_class = AnswerVoteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        answer_id = kwargs['answer_id']
        vote_value = request.data.get('vote', 0)
        
        if vote_value not in [-1, 1]:
            return Response(
                {'error': 'Invalid vote value. Must be -1 or 1'},
                status=status.HTTP_400_BAD_REQUEST
            )

        answer = Answer.objects.get(id=answer_id)
        vote, created = AnswerVote.objects.update_or_create(
            answer=answer,
            user=request.user,
            defaults={'vote': vote_value}
        )
        
        answer.update_score()  # Update the answer's weighted score
        return Response(AnswerVoteSerializer(vote).data)
