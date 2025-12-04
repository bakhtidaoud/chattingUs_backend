"""
Serializers for the posts app.
"""

from rest_framework import serializers
from .models import Post, Comment, Like


class PostSerializer(serializers.ModelSerializer):
    """
    Serializer for Post model.
    """
    user_username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = Post
        fields = ['id', 'user', 'user_username', 'caption', 'image', 'likes_count', 
                  'comments_count', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'likes_count', 'comments_count', 'created_at', 'updated_at']


class CommentSerializer(serializers.ModelSerializer):
    """
    Serializer for Comment model.
    """
    user_username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = Comment
        fields = ['id', 'post', 'user', 'user_username', 'text', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']


class LikeSerializer(serializers.ModelSerializer):
    """
    Serializer for Like model.
    """
    class Meta:
        model = Like
        fields = ['id', 'post', 'user', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']
