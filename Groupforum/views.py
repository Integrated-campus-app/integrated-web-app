from argparse import Action
from rest_framework.response import Response 
from rest_framework import viewsets
from rest_framework.permissions import AllowAny  # Add this import
from rest_framework.pagination import PageNumberPagination  # Import PageNumberPagination
from rest_framework import status  # Import status for HTTP response codes
from .models import Question, Answer, Comment
from .serializers import QuestionSerializer, AnswerSerializer, CommentSerializer
from rest_framework import serializers  # Import serializers to fix the error
from rest_framework import generics
from .models import Notification
from .serializers import NotificationSerializer
from rest_framework.decorators import action
from rest_framework import filters

class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        return Notification.objects.filter(
            anonymous_id=self.request.session.session_key
        ).order_by('-created_at')

class QuestionViewSet(viewsets.ModelViewSet):
    pagination_class = PageNumberPagination
    page_size = 10
    queryset = Question.objects.all()
    serializer_class = QuestionSerializer
    permission_classes = [AllowAny]  # Allow unauthenticated access

    filter_backends = [filters.SearchFilter]
    search_fields = ['title', 'description']
    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            # First delete all related answers and comments
            Answer.objects.filter(question=instance).delete()
            self.perform_destroy(instance)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

class AnswerViewSet(viewsets.ModelViewSet):
    queryset = Answer.objects.all()
    serializer_class = AnswerSerializer
    permission_classes = [AllowAny]


    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        answer = self.get_object()
        answer.accept()  # Uses the model method we defined
        return Response({
            'status': 'answer accepted',
            'answer_id': answer.id,
            'question_id': answer.question.id
        })    

    @action(detail=True, methods=['post'])  # Correct lowercase decorator
    def upvote(self, request, pk=None):
        answer = self.get_object()
        answer.upvotes += 1
        answer.save()
        return Response({'status': 'upvoted', 'new_count': answer.upvotes})
    
    @action(detail=True, methods=['post'])  # Also fixed here
    def downvote(self, request, pk=None):
        answer = self.get_object()
        answer.downvotes += 1
        answer.save()
        return Response({'status': 'downvoted', 'new_count': answer.downvotes})
    
class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        try:
            # Ensure anonymous_id is set from session if available
            if not request.data.get('anonymous_id') and request.session.session_key:
                request.data._mutable = True
                request.data['anonymous_id'] = request.session.session_key
                request.data._mutable = False
            return super().create(request, *args, **kwargs)
        except serializers.ValidationError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    @action(detail=True, methods=['post'])
    def upvote(self, request, pk=None):
        comment = self.get_object()
        comment.upvotes += 1
        comment.save()
        return Response({'status': 'upvoted', 'new_count': comment.upvotes})
    
    @action(detail=True, methods=['post'])
    def downvote(self, request, pk=None):
        comment = self.get_object()
        comment.downvotes += 1
        comment.save()
        return Response({'status': 'downvoted', 'new_count': comment.downvotes})