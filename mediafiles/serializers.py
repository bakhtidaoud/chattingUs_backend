"""
Serializers for the mediafiles app.
"""

from rest_framework import serializers
from .models import Media
from .utils.validators import validate_media_file


class MediaUploadSerializer(serializers.ModelSerializer):
    """
    Serializer for uploading media files.
    """
    file = serializers.FileField(write_only=True, source='original_file')
    
    class Meta:
        model = Media
        fields = ['file']
    
    def validate_file(self, file):
        """
        Validate uploaded file.
        """
        # This will raise ValidationError if file is invalid
        file_type = validate_media_file(file)
        
        # Store file type for later use
        self.context['file_type'] = file_type
        self.context['mime_type'] = file.content_type
        self.context['file_size'] = file.size
        
        return file
    
    def create(self, validated_data):
        """
        Create Media instance with validated data.
        """
        # Get user from context
        user = self.context['request'].user
        
        # Get file type from validation
        file_type = self.context.get('file_type')
        mime_type = self.context.get('mime_type')
        file_size = self.context.get('file_size')
        
        # Create media instance
        media = Media.objects.create(
            user=user,
            file_type=file_type,
            original_file=validated_data['original_file'],
            mime_type=mime_type,
            file_size=file_size,
            status='uploading'
        )
        
        return media


class MediaSerializer(serializers.ModelSerializer):
    """
    Serializer for Media model with all URLs.
    """
    display_url = serializers.SerializerMethodField()
    thumbnail_url = serializers.SerializerMethodField()
    urls = serializers.SerializerMethodField()
    user_username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = Media
        fields = [
            'id', 'user', 'user_username', 'file_type', 'status',
            'file_size', 'mime_type', 'display_url', 'thumbnail_url',
            'urls', 'width', 'height', 'duration', 'bitrate',
            'metadata', 'is_public', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'user', 'file_type', 'status', 'file_size',
            'mime_type', 'width', 'height', 'duration', 'bitrate',
            'metadata', 'created_at', 'updated_at'
        ]
    
    def get_display_url(self, obj):
        """Get the best URL to display."""
        url = obj.get_display_url()
        if url and self.context.get('request'):
            return self.context['request'].build_absolute_uri(url)
        return url
    
    def get_thumbnail_url(self, obj):
        """Get thumbnail URL."""
        url = obj.get_thumbnail_url()
        if url and self.context.get('request'):
            return self.context['request'].build_absolute_uri(url)
        return url
    
    def get_urls(self, obj):
        """Get all available URLs for the media."""
        request = self.context.get('request')
        urls = {}
        
        if obj.file_type == 'image':
            if obj.thumbnail:
                urls['thumbnail'] = request.build_absolute_uri(obj.thumbnail.url) if request else obj.thumbnail.url
            if obj.small:
                urls['small'] = request.build_absolute_uri(obj.small.url) if request else obj.small.url
            if obj.medium:
                urls['medium'] = request.build_absolute_uri(obj.medium.url) if request else obj.medium.url
            if obj.large:
                urls['large'] = request.build_absolute_uri(obj.large.url) if request else obj.large.url
            if obj.webp:
                urls['webp'] = request.build_absolute_uri(obj.webp.url) if request else obj.webp.url
            if obj.original_file:
                urls['original'] = request.build_absolute_uri(obj.original_file.url) if request else obj.original_file.url
        
        elif obj.file_type == 'video':
            if obj.video_thumbnail:
                urls['thumbnail'] = request.build_absolute_uri(obj.video_thumbnail.url) if request else obj.video_thumbnail.url
            if obj.processed_video:
                urls['processed'] = request.build_absolute_uri(obj.processed_video.url) if request else obj.processed_video.url
            if obj.original_file:
                urls['original'] = request.build_absolute_uri(obj.original_file.url) if request else obj.original_file.url
        
        elif obj.file_type == 'audio':
            if obj.processed_audio:
                urls['processed'] = request.build_absolute_uri(obj.processed_audio.url) if request else obj.processed_audio.url
            if obj.original_file:
                urls['original'] = request.build_absolute_uri(obj.original_file.url) if request else obj.original_file.url
        
        return urls


class MediaListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for listing media.
    """
    display_url = serializers.SerializerMethodField()
    thumbnail_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Media
        fields = [
            'id', 'file_type', 'status', 'display_url',
            'thumbnail_url', 'created_at'
        ]
    
    def get_display_url(self, obj):
        """Get the best URL to display."""
        url = obj.get_display_url()
        if url and self.context.get('request'):
            return self.context['request'].build_absolute_uri(url)
        return url
    
    def get_thumbnail_url(self, obj):
        """Get thumbnail URL."""
        url = obj.get_thumbnail_url()
        if url and self.context.get('request'):
            return self.context['request'].build_absolute_uri(url)
        return url
