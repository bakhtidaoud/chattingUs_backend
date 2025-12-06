"""
Serializers for the messages app.
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Chat, Message, Reaction

User = get_user_model()

class ReactionSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = Reaction
        fields = ['id', 'message', 'user', 'user_username', 'reaction', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']

class MessageSerializer(serializers.ModelSerializer):
    """
    Serializer for Message model.
    """
    sender_username = serializers.CharField(source='sender.username', read_only=True)
    reactions = ReactionSerializer(many=True, read_only=True)
    forwarded_from_id = serializers.PrimaryKeyRelatedField(
        queryset=Message.objects.all(), source='forwarded_from', write_only=True, required=False, allow_null=True
    )
    
    class Meta:
        model = Message
        fields = ['id', 'chat', 'sender', 'sender_username', 'message_type', 'content', 'media', 
                  'is_read', 'forwarded_from', 'forwarded_from_id', 'reactions', 'created_at']
        read_only_fields = ['id', 'sender', 'created_at', 'forwarded_from']

class ChatSerializer(serializers.ModelSerializer):
    """
    Serializer for Chat model.
    """
    last_message = serializers.SerializerMethodField()
    participants_usernames = serializers.SerializerMethodField()
    participants = serializers.PrimaryKeyRelatedField(many=True, queryset=User.objects.all())
    
    class Meta:
        model = Chat
        fields = ['id', 'participants', 'participants_usernames', 'last_message', 
                  'is_group', 'group_name', 'group_image', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_last_message(self, obj):
        last_message = obj.messages.last()
        if last_message:
            return MessageSerializer(last_message).data
        return None
    
    def get_participants_usernames(self, obj):
        return [user.username for user in obj.participants.all()]
