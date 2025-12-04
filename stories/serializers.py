"""
Serializers for the stories app.
"""

from rest_framework import serializers
from .models import Story, StoryView


class StorySerializer(serializers.ModelSerializer):
    """
    Serializer for Story model.
    """
    user_username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = Story
        fields = ['id', 'user', 'user_username', 'image', 'video', 'text', 
                  'views_count', 'created_at', 'expires_at']
        read_only_fields = ['id', 'user', 'views_count', 'created_at']


class StoryViewSerializer(serializers.ModelSerializer):
    """
    Serializer for StoryView model.
    """
    class Meta:
        model = StoryView
        fields = ['id', 'story', 'user', 'viewed_at']
        read_only_fields = ['id', 'user', 'viewed_at']
