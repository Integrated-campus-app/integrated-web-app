from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django.db.models import Count, Sum
from .models import (
    Notice, 
    Task, 
    Message, 
    Feedback, 
    IssueReport,
    LocationCategory,
    CampusLocation,
    UserFavoriteLocation,Question, Answer, Tag, QuestionVote, AnswerVote

)
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import (
    UserRegistrationSerializer,
    NoticeSerializer,
    TaskSerializer,
    MessageSerializer,
    FeedbackSerializer,
    IssueReportSerializer,
    CustomTokenObtainPairSerializer,
    DepartmentSerializer,
    LocationCategorySerializer,
    CampusLocationSerializer,
    UserFavoriteLocationSerializer,
    QuestionSerializer, AnswerSerializer,
    TagSerializer, QuestionVoteSerializer,
    AnswerVoteSerializer
)

User = get_user_model()

# ==================== Login ====================
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

# ==================== AUTHENTICATION VIEWS ====================
class RegisterView(generics.CreateAPIView):
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Generate tokens for immediate login
        refresh = CustomTokenObtainPairSerializer.get_token(user)
        
        return Response({
            "success": True,
            "user": {
                "username": user.username,
                "email": user.university_email,
                "is_admin": user.is_admin
            },
            "tokens": {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
            }
        }, status=status.HTTP_201_CREATED)

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
# ==================== NOTIFICATION VIEWS ====================
class NotificationTestView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"user_{request.user.id}",
            {
                'type': 'send_notification',
                'message': f'Personal notification for {request.user.username}'
            }
        )
        async_to_sync(channel_layer.group_send)(
            "global_notifications",
            {
                'type': 'send_notification',
                'message': 'New campus-wide announcement!'
            }
        )
        return Response({"status": "Test notifications sent"})

# ==================== NOTICE VIEWS ====================
class NoticeListView(generics.ListCreateAPIView):
    serializer_class = NoticeSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['department', 'priority', 'is_pinned']
    search_fields = ['title', 'content']
    
    def get_permission_classes(self):
        if self.request.method == 'POST':
            return [permissions.IsAdminUser]
        return [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        queryset = Notice.objects.all().order_by('-is_pinned', '-created_at')
        
        # Optional: Filter by department if query param exists
        department = self.request.query_params.get('department')
        if department:
            queryset = queryset.filter(department__code=department)
            
        return queryset

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

class NoticeDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Notice.objects.all()
    serializer_class = NoticeSerializer
    permission_classes = [permissions.IsAdminUser]


# ==================== TASK VIEWS ====================
class TaskListView(generics.ListCreateAPIView):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_admin:
            return Task.objects.all()
        return Task.objects.filter(assigned_to=self.request.user)

    def perform_create(self, serializer):
        serializer.save()

class TaskDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_admin:
            return Task.objects.all()
        return Task.objects.filter(assigned_to=self.request.user)

# ==================== MESSAGE VIEWS ====================
class MessageCreateView(generics.CreateAPIView):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(sender=self.request.user)

class MessageListView(generics.ListAPIView):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Message.objects.filter(
            receiver=self.request.user
        ).order_by('-timestamp')

# ==================== FEEDBACK VIEWS ====================
class FeedbackCreateView(generics.CreateAPIView):
    serializer_class = FeedbackSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        if serializer.validated_data.get('is_anonymous'):
            serializer.save(user=None)
        else:
            serializer.save(user=self.request.user)

# ==================== ISSUE REPORT VIEWS ====================
class IssueReportCreateView(generics.CreateAPIView):
    serializer_class = IssueReportSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(reporter=self.request.user)

class IssueReportListView(generics.ListAPIView):
    serializer_class = IssueReportSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_queryset(self):
        return IssueReport.objects.all().order_by('-created_at')

class IssueReportUpdateView(generics.UpdateAPIView):
    serializer_class = IssueReportSerializer
    permission_classes = [permissions.IsAdminUser]
    queryset = IssueReport.objects.all()

    #===================LOCATION VIEWS====================
    # views.py
class LocationCategoryListView(generics.ListAPIView):
    queryset = LocationCategory.objects.all()
    serializer_class = LocationCategorySerializer
    permission_classes = [permissions.AllowAny]

class CampusLocationListView(generics.ListCreateAPIView):
    serializer_class = CampusLocationSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['category', 'department', 'floor_level']
    search_fields = ['name', 'description']
    
    def get_queryset(self):
        return CampusLocation.objects.select_related('category', 'department').all()

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

class CampusLocationDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = CampusLocation.objects.all()
    serializer_class = CampusLocationSerializer
    permission_classes = [permissions.IsAdminUser]

class UserFavoriteLocationView(generics.ListCreateAPIView):
    serializer_class = UserFavoriteLocationSerializer
    
    def get_queryset(self):
        return UserFavoriteLocation.objects.filter(
            user=self.request.user
        ).select_related('location', 'location__category')
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class RemoveFavoriteView(generics.DestroyAPIView):
    serializer_class = UserFavoriteLocationSerializer
    
    def get_queryset(self):
        return UserFavoriteLocation.objects.filter(user=self.request.user)
    


    #===================GROUP DISCUSSION QUESTION VIEWS====================
    
class QuestionListView(generics.ListCreateAPIView):
    serializer_class = QuestionSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ['title', 'content']
    filterset_fields = ['tags', 'user', 'is_closed']

    def get_queryset(self):
        queryset = Question.objects.annotate(
            answers_count=Count('answers')
        ).select_related('user').prefetch_related('tags')
        
        # Order by most recent or most viewed
        ordering = self.request.query_params.get('ordering', '-created_at')
        if ordering in ['-created_at', '-views', '-answers_count']:
            queryset = queryset.order_by(ordering)
            
        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
class QuestionDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Question.objects.all()
    serializer_class = QuestionSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.views += 1
        instance.save()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

class AnswerCreateView(generics.CreateAPIView):
    serializer_class = AnswerSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class AnswerDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Answer.objects.all()
    serializer_class = AnswerSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

class TagListView(generics.ListAPIView):
    queryset = Tag.objects.annotate(questions_count=Count('questions'))
    serializer_class = TagSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None

class QuestionVoteView(generics.CreateAPIView):
    serializer_class = QuestionVoteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        question_id = self.kwargs['question_id']
        serializer.save(
            user=self.request.user,
            question_id=question_id
        )

class AnswerVoteView(generics.CreateAPIView):
    serializer_class = AnswerVoteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        answer_id = self.kwargs['answer_id']
        serializer.save(
            user=self.request.user,
            answer_id=answer_id
        )