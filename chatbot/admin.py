from django.contrib import admin
from .models import Conversation, Message

@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_at', 'is_deleted')
    list_filter = ('is_deleted',)
    actions = ['hard_delete']
    
    def hard_delete(self, request, queryset):
        queryset.delete()
    hard_delete.short_description = "Permanently delete selected items"

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('truncated_content', 'conversation', 'is_user')
    
    def truncated_content(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    truncated_content.short_description = 'Content'