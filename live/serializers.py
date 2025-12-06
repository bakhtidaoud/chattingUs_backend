"""
Serializers for live streaming models.
"""

from rest_framework import serializers
from .models import LiveStream, LiveViewer, LiveComment, LiveReaction
from users.serializers import UserSerializer


class LiveStreamSerializer(serializers.ModelSerializer):
    """
    Serializer for LiveStream model.
    """
    streamer = UserSerializer(read_only=True)
    duration = serializers.ReadOnlyField()
    is_owner = serializers.SerializerMethodField()
    
    class Meta:
        model = LiveStream
        fields = [
            'id', 'streamer', 'title', 'description', 'thumbnail',
            'status', 'viewer_count', 'peak_viewer_count',
            'is_recorded', 'recording_url',
            'started_at', 'ended_at', 'created_at', 'updated_at',
            'duration', 'is_owner'
        ]
        read_only_fields = [
            'id', 'streamer', 'status', 'viewer_count', 'peak_viewer_count',
            'started_at', 'ended_at', 'created_at', 'updated_at'
        ]
    
    def get_is_owner(self, obj):
        """Check if current user is the stream owner."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.streamer == request.user
        return False


class LiveStreamCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a live stream.
    """
    class Meta:
        model = LiveStream
        fields = ['title', 'description', 'thumbnail', 'is_recorded']
    
    def create(self, validated_data):
        """Create a new live stream."""
        request = self.context.get('request')
        validated_data['streamer'] = request.user
        return super().create(validated_data)


class LiveViewerSerializer(serializers.ModelSerializer):
    """
    Serializer for LiveViewer model.
    """
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = LiveViewer
        fields = [
            'id', 'user', 'joined_at', 'left_at', 'is_active'
        ]
        read_only_fields = ['id', 'joined_at', 'left_at']


class LiveCommentSerializer(serializers.ModelSerializer):
    """
    Serializer for LiveComment model.
    """
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = LiveComment
        fields = ['id', 'user', 'text', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']
    
    def create(self, validated_data):
        """Create a new comment."""
        request = self.context.get('request')
        validated_data['user'] = request.user
        return super().create(validated_data)


class LiveReactionSerializer(serializers.ModelSerializer):
    """
    Serializer for LiveReaction model.
    """
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = LiveReaction
        fields = ['id', 'user', 'reaction_type', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']
    
    def create(self, validated_data):
        """Create a new reaction."""
        request = self.context.get('request')
        validated_data['user'] = request.user
        return super().create(validated_data)
