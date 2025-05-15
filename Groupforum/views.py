from argparse import Action
from rest_framework.response import Response 
from rest_framework import viewsets
from rest_framework.permissions import AllowAny  # Add this import
from rest_framework.pagination import PageNumberPagination  # Import PageNumberPagination
from rest_framework import status  # Import status for HTTP response codes
from rest_framework.views import APIView  # Changed from generics to views
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from .models import Question, Answer, Comment
from .serializers import QuestionSerializer, AnswerSerializer, CommentSerializer
from rest_framework import serializers  # Import serializers to fix the error
from rest_framework import generics
from .models import Notification
from .serializers import NotificationSerializer
from rest_framework.decorators import action
from rest_framework import filters
from django.db.models import Q, Count, F
from django.core.paginator import Paginator
from django.utils import timezone
from django.http import StreamingHttpResponse
import json
import time
from django.core.cache import cache
from threading import Thread
import queue

# Global notification queue
notification_queue = queue.Queue()

def notification_generator():
    """Generator function that yields notifications as they come in"""
    while True:
        try:
            # Get notification from queue with timeout
            notification = notification_queue.get(timeout=30)
            if notification:
                # Format the SSE message properly
                yield f"data: {json.dumps(notification)}\n\n"
        except queue.Empty:
            # Send heartbeat to keep connection alive
            yield f"data: {json.dumps({'type': 'heartbeat'})}\n\n"

@method_decorator(csrf_exempt, name='dispatch')
class NotificationStreamView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        # Check if client accepts text/event-stream
        accept_header = request.META.get('HTTP_ACCEPT', '')
        if 'text/event-stream' not in accept_header and '*/*' not in accept_header:
            return Response(
                {'error': 'Client must accept text/event-stream'},
                status=status.HTTP_406_NOT_ACCEPTABLE
            )

        def event_generator():
            while True:
                try:
                    # Get notification from queue with timeout
                    notification = notification_queue.get(timeout=30)
                    if notification:
                        # Format the SSE message properly
                        yield f"data: {json.dumps(notification)}\n\n"
                except queue.Empty:
                    # Send heartbeat to keep connection alive
                    yield f"data: {json.dumps({'type': 'heartbeat'})}\n\n"

        response = StreamingHttpResponse(
            event_generator(),
            content_type='text/event-stream'
        )
        
        # Add required headers for SSE
        response['Cache-Control'] = 'no-cache'
        response['X-Accel-Buffering'] = 'no'
        response['Connection'] = 'keep-alive'
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, Accept'
        
        return response

    def options(self, request, *args, **kwargs):
        response = Response()
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, Accept'
        return response

def send_notification(message, notification_type='info', related_question=None, related_answer=None):
    """Helper function to send notifications"""
    notification = {
        'message': message,
        'type': notification_type,
        'timestamp': time.time(),
        'question_id': related_question.id if related_question else None,
        'answer_id': related_answer.id if related_answer else None
    }
    notification_queue.put(notification)

@method_decorator(csrf_exempt, name='dispatch')
class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        return Notification.objects.filter(
            anonymous_id=self.request.session.session_key
        ).order_by('-created_at')

@method_decorator(csrf_exempt, name='dispatch')
class QuestionViewSet(viewsets.ModelViewSet):
    queryset = Question.objects.all()
    serializer_class = QuestionSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        queryset = Question.objects.all()
        
        # Search functionality
        search_query = self.request.query_params.get('search', '')
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(description__icontains=search_query)
            )
        
        # Sort by most recent by default
        queryset = queryset.order_by('-created_at')
        
        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        
        # Pagination
        page = int(request.query_params.get('page', 1))
        paginator = Paginator(queryset, 10)  # 10 items per page
        
        try:
            questions = paginator.page(page)
        except:
            return Response([], status=status.HTTP_200_OK)
        
        serializer = self.get_serializer(questions, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def flag(self, request, pk=None):
        question = self.get_object()
        reason = request.data.get('reason')
        description = request.data.get('description', '')
        
        if not reason:
            return Response(
                {'error': 'Reason is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        question.reports.create(
            reason=reason,
            description=description,
            reporter=request.user if request.user.is_authenticated else None
        )
        
        return Response({'status': 'question flagged'})

    def perform_create(self, serializer):
        question = serializer.save()
        send_notification(
            f"New question posted: {question.title}",
            'new_question',
            related_question=question
        )

    def perform_update(self, serializer):
        question = serializer.save()
        send_notification(
            f"Question updated: {question.title}",
            'question_updated',
            related_question=question
        )

    def perform_destroy(self, instance):
        send_notification(
            f"Question deleted: {instance.title}",
            'question_deleted'
        )
        instance.delete()

@method_decorator(csrf_exempt, name='dispatch')
class AnswerViewSet(viewsets.ModelViewSet):
    queryset = Answer.objects.all()
    serializer_class = AnswerSerializer
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        answer = serializer.save()
        question = answer.question
        
        # Update question's last activity
        question.last_activity = timezone.now()
        question.save()
        
        # Send notification
        send_notification(
            f"New answer to: {question.title}",
            'new_answer',
            related_question=question,
            related_answer=answer
        )

    @action(detail=True, methods=['post'])
    def vote(self, request, pk=None):
        answer = self.get_object()
        vote_type = request.data.get('type')
        
        if vote_type == 'up':
            answer.upvotes += 1
        elif vote_type == 'down':
            answer.downvotes += 1
        else:
            return Response(
                {'error': 'Invalid vote type'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        answer.save()
        send_notification(
            f"Answer received a {vote_type}vote",
            'vote',
            related_answer=answer
        )
        return Response(self.get_serializer(answer).data)

    @action(detail=True, methods=['post'])
    def flag(self, request, pk=None):
        answer = self.get_object()
        reason = request.data.get('reason')
        description = request.data.get('description', '')
        
        if not reason:
            return Response(
                {'error': 'Reason is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        answer.reports.create(
            reason=reason,
            description=description,
            reporter=request.user if request.user.is_authenticated else None
        )
        
        return Response({'status': 'answer flagged'})

@method_decorator(csrf_exempt, name='dispatch')
class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        comment = serializer.save()
        
        # Get the associated answer (either directly or through parent comment)
        answer = comment.answer
        if not answer and comment.parent_comment:
            answer = comment.parent_comment.answer
            
        if answer:
            question = answer.question
            
            # Update question's last activity
            question.last_activity = timezone.now()
            question.save()
            
            # Send notification
            notification_message = "New comment on answer to: " if comment.answer else "New reply to comment on: "
            send_notification(
                f"{notification_message}{question.title}",
                'new_comment',
                related_question=question,
                related_answer=answer
            )

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