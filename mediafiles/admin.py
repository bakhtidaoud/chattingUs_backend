"""
Admin configuration for mediafiles app.
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import Media


@admin.register(Media)
class MediaAdmin(admin.ModelAdmin):
    list_display = ['id', 'thumbnail_preview', 'user', 'file_type', 'status', 'file_size_display', 'created_at']
    list_filter = ['file_type', 'status', 'created_at', 'is_public']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['thumbnail_preview', 'file_size', 'mime_type', 'width', 'height', 'duration', 'bitrate', 'metadata', 'created_at', 'updated_at']
    list_select_related = ['user']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'file_type', 'status', 'is_public')
        }),
        ('File Information', {
            'fields': ('original_file', 'file_size', 'mime_type')
        }),
        ('Image Files', {
            'fields': ('thumbnail', 'small', 'medium', 'large', 'webp', 'width', 'height'),
            'classes': ('collapse',)
        }),
        ('Video Files', {
            'fields': ('video_thumbnail', 'processed_video', 'duration'),
            'classes': ('collapse',)
        }),
        ('Audio Files', {
            'fields': ('processed_audio', 'bitrate'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def thumbnail_preview(self, obj):
        """Display thumbnail preview in admin."""
        url = obj.get_thumbnail_url()
        if url:
            return format_html('<img src="{}" width="50" height="50" style="object-fit: cover;" />', url)
        return '-'
    thumbnail_preview.short_description = 'Preview'
    
    def file_size_display(self, obj):
        """Display file size in human-readable format."""
        size = obj.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
    file_size_display.short_description = 'Size'
    
    actions = ['reprocess_media', 'mark_as_public', 'mark_as_private']
    
    def reprocess_media(self, request, queryset):
        """Reprocess selected media files."""
        from .tasks import process_media_task
        
        count = 0
        for media in queryset.filter(status='failed'):
            media.status = 'uploading'
            media.metadata.pop('error', None)
            media.save()
            process_media_task.delay(media.id)
            count += 1
        
        self.message_user(request, f"Triggered reprocessing for {count} media files")
    reprocess_media.short_description = "Reprocess selected failed media"
    
    def mark_as_public(self, request, queryset):
        """Mark selected media as public."""
        count = queryset.update(is_public=True)
        self.message_user(request, f"Marked {count} media files as public")
    mark_as_public.short_description = "Mark as public"
    
    def mark_as_private(self, request, queryset):
        """Mark selected media as private."""
        count = queryset.update(is_public=False)
        self.message_user(request, f"Marked {count} media files as private")
    mark_as_private.short_description = "Mark as private"
