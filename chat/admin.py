"""
Admin configuration for messages app.
"""

from django.contrib import admin
from .models import Chat, Message


@admin.register(Chat)
class ChatAdmin(admin.ModelAdmin):
    list_display = ['id', 'created_at', 'updated_at']
    list_filter = ['created_at', 'updated_at']
    filter_horizontal = ['participants']


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['sender', 'chat', 'content', 'message_type', 'is_read', 'created_at']
    list_filter = ['is_read', 'created_at', 'message_type']
    search_fields = ['sender__username', 'content']
