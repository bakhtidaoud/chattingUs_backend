"""
Serializers for the users app.
"""

from rest_framework import serializers
from .models import User, UserProfile, Follow


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for User model.
    """
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'bio', 
                  'profile_picture', 'date_of_birth', 'phone_number', 'is_verified', 
                  'created_at', 'updated_at']
        read_only_fields = ['id', 'is_verified', 'created_at', 'updated_at']
        extra_kwargs = {'password': {'write_only': True}}


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for UserProfile model.
    """
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = UserProfile
        fields = ['user', 'followers_count', 'following_count', 'posts_count', 'is_private']


class FollowSerializer(serializers.ModelSerializer):
    """
    Serializer for Follow model.
    """
    follower = UserSerializer(read_only=True)
    following = UserSerializer(read_only=True)
    
    class Meta:
        model = Follow
        fields = ['id', 'follower', 'following', 'created_at']
        read_only_fields = ['id', 'created_at']
