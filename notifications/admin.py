"""
Admin configuration for notifications app.
"""

from django.contrib import admin
from .models import Notification, NotificationPreference


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['id', 'recipient', 'sender', 'notification_type', 'get_text', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read', 'created_at', 'content_type']
    search_fields = ['recipient__username', 'sender__username']
    readonly_fields = ['created_at', 'content_type', 'object_id', 'get_text', 'get_link']
    list_select_related = ['recipient', 'sender', 'content_type']
    date_hierarchy = 'created_at'
    
    def get_text(self, obj):
        """Display notification text."""
        return obj.get_notification_text()
    get_text.short_description = 'Text'
    
    def get_link(self, obj):
        """Display notification link."""
        return obj.get_notification_link()
    get_link.short_description = 'Link'


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = ['user', 'like_push', 'comment_push', 'follow_push', 'message_push', 'mention_push']
    search_fields = ['user__username', 'user__email']
    list_filter = ['like_push', 'comment_push', 'follow_push', 'message_push', 'mention_push']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Like Notifications', {
            'fields': ('like_push', 'like_email', 'like_in_app'),
        }),
        ('Comment Notifications', {
            'fields': ('comment_push', 'comment_email', 'comment_in_app'),
        }),
        ('Follow Notifications', {
            'fields': ('follow_push', 'follow_email', 'follow_in_app'),
        }),
        ('Message Notifications', {
            'fields': ('message_push', 'message_email', 'message_in_app'),
        }),
        ('Mention Notifications', {
            'fields': ('mention_push', 'mention_email', 'mention_in_app'),
        }),
        ('FCM Tokens', {
            'fields': ('fcm_tokens',),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
        }),
    )

