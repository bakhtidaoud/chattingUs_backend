"""
Admin configuration for live streaming models.
"""

from django.contrib import admin
from .models import LiveStream, LiveViewer, LiveComment, LiveReaction


@admin.register(LiveStream)
class LiveStreamAdmin(admin.ModelAdmin):
    """Admin interface for LiveStream model."""
    list_display = [
        'id', 'title', 'streamer', 'status', 'viewer_count',
        'peak_viewer_count', 'started_at', 'ended_at'
    ]
    list_filter = ['status', 'is_recorded', 'created_at']
    search_fields = ['title', 'description', 'streamer__username']
    readonly_fields = [
        'viewer_count', 'peak_viewer_count', 'started_at',
        'ended_at', 'created_at', 'updated_at'
    ]
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Stream Information', {
            'fields': ('streamer', 'title', 'description', 'thumbnail')
        }),
        ('Status', {
            'fields': ('status', 'viewer_count', 'peak_viewer_count')
        }),
        ('Recording', {
            'fields': ('is_recorded', 'recording_url')
        }),
        ('Timestamps', {
            'fields': ('started_at', 'ended_at', 'created_at', 'updated_at')
        }),
    )
    
    actions = ['end_streams']
    
    def end_streams(self, request, queryset):
        """End selected live streams."""
        count = 0
        for stream in queryset.filter(status='live'):
            stream.end_stream()
            count += 1
        self.message_user(request, f'{count} stream(s) ended successfully.')
    end_streams.short_description = 'End selected live streams'


@admin.register(LiveViewer)
class LiveViewerAdmin(admin.ModelAdmin):
    """Admin interface for LiveViewer model."""
    list_display = ['id', 'user', 'stream', 'is_active', 'joined_at', 'left_at']
    list_filter = ['is_active', 'joined_at']
    search_fields = ['user__username', 'stream__title']
    readonly_fields = ['joined_at', 'left_at']
    date_hierarchy = 'joined_at'


@admin.register(LiveComment)
class LiveCommentAdmin(admin.ModelAdmin):
    """Admin interface for LiveComment model."""
    list_display = ['id', 'user', 'stream', 'text_preview', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'stream__title', 'text']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'
    
    def text_preview(self, obj):
        """Show preview of comment text."""
        return obj.text[:50] + '...' if len(obj.text) > 50 else obj.text
    text_preview.short_description = 'Comment'


@admin.register(LiveReaction)
class LiveReactionAdmin(admin.ModelAdmin):
    """Admin interface for LiveReaction model."""
    list_display = ['id', 'user', 'stream', 'reaction_type', 'created_at']
    list_filter = ['reaction_type', 'created_at']
    search_fields = ['user__username', 'stream__title']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'
