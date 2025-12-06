"""
Serializers for the reels app.
"""

from rest_framework import serializers
from .models import Reel, ReelComment, ReelLike


class ReelSerializer(serializers.ModelSerializer):
    """
    Serializer for Reel model.
    """
    user_username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = Reel
        fields = ['id', 'user', 'user_username', 'video', 'caption', 'thumbnail', 'audio', 'duration',
                  'likes_count', 'comments_count', 'shares_count', 'views_count', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'likes_count', 'comments_count', 'shares_count', 'views_count', 
                           'created_at', 'updated_at', 'thumbnail', 'audio', 'duration']


class ReelCommentSerializer(serializers.ModelSerializer):
    """
    Serializer for ReelComment model.
    """
    user_username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = ReelComment
        fields = ['id', 'reel', 'user', 'user_username', 'text', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']


class ReelLikeSerializer(serializers.ModelSerializer):
    """
    Serializer for ReelLike model.
    """
    class Meta:
        model = ReelLike
        fields = ['id', 'reel', 'user', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']
