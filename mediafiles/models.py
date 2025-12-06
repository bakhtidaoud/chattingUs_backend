"""
Models for the mediafiles app.
"""

from django.db import models
from django.conf import settings
from django.core.validators import FileExtensionValidator
import os


def user_media_path(instance, filename):
    """
    Generate upload path for user media.
    Format: media/user_{id}/{file_type}/{filename}
    """
    ext = filename.split('.')[-1]
    filename = f"{instance.id or 'temp'}_{filename}"
    return f'user_{instance.user.id}/{instance.file_type}/{filename}'


class Media(models.Model):
    """
    Model for storing media files (images, videos, audio).
    """
    FILE_TYPE_CHOICES = (
        ('image', 'Image'),
        ('video', 'Video'),
        ('audio', 'Audio'),
    )
    
    STATUS_CHOICES = (
        ('uploading', 'Uploading'),
        ('processing', 'Processing'),
        ('ready', 'Ready'),
        ('failed', 'Failed'),
    )
    
    # Basic fields
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='media_files'
    )
    file_type = models.CharField(max_length=10, choices=FILE_TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='uploading')
    
    # Original file
    original_file = models.FileField(
        upload_to=user_media_path,
        max_length=500
    )
    file_size = models.BigIntegerField(help_text='File size in bytes')
    mime_type = models.CharField(max_length=100)
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True)
    
    # Image-specific fields
    thumbnail = models.ImageField(upload_to='thumbnails/', null=True, blank=True)
    small = models.ImageField(upload_to='small/', null=True, blank=True)
    medium = models.ImageField(upload_to='medium/', null=True, blank=True)
    large = models.ImageField(upload_to='large/', null=True, blank=True)
    webp = models.ImageField(upload_to='webp/', null=True, blank=True)
    
    width = models.IntegerField(null=True, blank=True)
    height = models.IntegerField(null=True, blank=True)
    
    # Video-specific fields
    video_thumbnail = models.ImageField(upload_to='video_thumbnails/', null=True, blank=True)
    processed_video = models.FileField(upload_to='processed_videos/', null=True, blank=True)
    duration = models.FloatField(null=True, blank=True, help_text='Duration in seconds')
    
    # Audio-specific fields
    processed_audio = models.FileField(upload_to='processed_audio/', null=True, blank=True)
    bitrate = models.IntegerField(null=True, blank=True, help_text='Bitrate in kbps')
    
    # Access control
    is_public = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Media File'
        verbose_name_plural = 'Media Files'
        indexes = [
            models.Index(fields=['user', 'file_type', '-created_at']),
            models.Index(fields=['status', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.file_type} - {self.user.username} - {self.id}"
    
    def get_display_url(self):
        """
        Get the best URL to display based on file type and processing status.
        """
        if self.file_type == 'image':
            if self.medium:
                return self.medium.url
            elif self.original_file:
                return self.original_file.url
        elif self.file_type == 'video':
            if self.processed_video:
                return self.processed_video.url
            elif self.original_file:
                return self.original_file.url
        elif self.file_type == 'audio':
            if self.processed_audio:
                return self.processed_audio.url
            elif self.original_file:
                return self.original_file.url
        
        return self.original_file.url if self.original_file else None
    
    def get_thumbnail_url(self):
        """
        Get thumbnail URL.
        """
        if self.file_type == 'image' and self.thumbnail:
            return self.thumbnail.url
        elif self.file_type == 'video' and self.video_thumbnail:
            return self.video_thumbnail.url
        return None
    
    def delete(self, *args, **kwargs):
        """
        Override delete to remove files from storage.
        """
        # Delete all associated files
        files_to_delete = [
            self.original_file,
            self.thumbnail,
            self.small,
            self.medium,
            self.large,
            self.webp,
            self.video_thumbnail,
            self.processed_video,
            self.processed_audio,
        ]
        
        for file_field in files_to_delete:
            if file_field:
                try:
                    if os.path.isfile(file_field.path):
                        os.remove(file_field.path)
                except Exception:
                    pass
        
        super().delete(*args, **kwargs)
