"""
Serializers for Firebase social authentication.
"""

from rest_framework import serializers
from .models import User


class FirebaseAuthSerializer(serializers.Serializer):
    """
    Serializer for Firebase token authentication.
    """
    id_token = serializers.CharField(required=True, help_text="Firebase ID token from client")
    provider = serializers.ChoiceField(
        choices=['google', 'microsoft'],
        required=True,
        help_text="Authentication provider"
    )


class SocialAuthResponseSerializer(serializers.ModelSerializer):
    """
    Serializer for social authentication response.
    """
    access = serializers.CharField(read_only=True)
    refresh = serializers.CharField(read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'profile_picture', 'is_social_auth', 'auth_provider',
            'email_verified', 'access', 'refresh'
        ]
        read_only_fields = fields


class LinkSocialAccountSerializer(serializers.Serializer):
    """
    Serializer for linking social account to existing user.
    """
    id_token = serializers.CharField(required=True, help_text="Firebase ID token")
    provider = serializers.ChoiceField(
        choices=['google', 'microsoft'],
        required=True,
        help_text="Authentication provider"
    )
