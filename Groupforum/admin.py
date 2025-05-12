from django.contrib import admin
from .models import Question, Answer, Comment, Notification

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_at', 'anonymous_id')
    search_fields = ('title', 'description')

@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ('truncated_text', 'question', 'upvotes', 'downvotes', 'is_accepted', 'created_at')
    list_filter = ('is_accepted', 'created_at')
    search_fields = ('text', 'question__title')
    
    def truncated_text(self, obj):
        return obj.text[:50] + '...' if len(obj.text) > 50 else obj.text
    truncated_text.short_description = 'Text Preview'

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('truncated_text', 'answer', 'created_at')
    
    def truncated_text(self, obj):
        return obj.text[:50] + '...' if len(obj.text) > 50 else obj.text
    truncated_text.short_description = 'Text Preview'

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('truncated_message', 'anonymous_id', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at')
    
    def truncated_message(self, obj):
        return obj.message[:50] + '...' if len(obj.message) > 50 else obj.message
    truncated_message.short_description = 'Message'