"""
Serializers for the notifications app.
"""

from rest_framework import serializers
from .models import Notification, NotificationPreference


class NotificationSerializer(serializers.ModelSerializer):
    """
    Serializer for Notification model.
    """
    sender_username = serializers.CharField(source='sender.username', read_only=True, allow_null=True)
    sender_profile_picture = serializers.SerializerMethodField()
    sender_full_name = serializers.SerializerMethodField()
    text = serializers.SerializerMethodField()
    link = serializers.SerializerMethodField()
    time_ago = serializers.ReadOnlyField()
    content_object_data = serializers.SerializerMethodField()
    
    class Meta:
        model = Notification
        fields = [
            'id', 'recipient', 'sender', 'sender_username', 'sender_profile_picture',
            'sender_full_name', 'notification_type', 'text', 'link', 'content_type',
            'object_id', 'content_object_data', 'is_read', 'created_at', 'time_ago'
        ]
        read_only_fields = ['id', 'created_at', 'sender', 'recipient', 'notification_type',
                           'content_type', 'object_id']
    
    def get_sender_profile_picture(self, obj):
        """Get sender's profile picture URL."""
        if obj.sender and obj.sender.profile_picture:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.sender.profile_picture.url)
            return obj.sender.profile_picture.url
        return None
    
    def get_sender_full_name(self, obj):
        """Get sender's full name."""
        if obj.sender:
            return obj.sender.get_full_name() or obj.sender.username
        return None
    
    def get_text(self, obj):
        """Get notification text."""
        return obj.get_notification_text()
    
    def get_link(self, obj):
        """Get notification link."""
        return obj.get_notification_link()
    
    def get_content_object_data(self, obj):
        """
        Get serialized data of the content object.
        """
        if not obj.content_object:
            return None
        
        content_type = obj.content_type.model
        content_obj = obj.content_object
        
        # Basic data for all content types
        data = {
            'type': content_type,
            'id': obj.object_id,
        }
        
        # Add type-specific data
        if content_type == 'post':
            data.update({
                'caption': getattr(content_obj, 'caption', '')[:100],
                'image': content_obj.image.url if hasattr(content_obj, 'image') and content_obj.image else None,
            })
        elif content_type == 'reel':
            data.update({
                'caption': getattr(content_obj, 'caption', '')[:100],
                'thumbnail': content_obj.thumbnail.url if hasattr(content_obj, 'thumbnail') and content_obj.thumbnail else None,
            })
        elif content_type == 'story':
            data.update({
                'content': content_obj.content.url if hasattr(content_obj, 'content') and content_obj.content else None,
            })
        elif content_type == 'comment':
            data.update({
                'text': getattr(content_obj, 'text', '')[:100],
            })
        elif content_type == 'user':
            data.update({
                'username': getattr(content_obj, 'username', ''),
                'profile_picture': content_obj.profile_picture.url if hasattr(content_obj, 'profile_picture') and content_obj.profile_picture else None,
            })
        
        return data


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    """
    Serializer for NotificationPreference model.
    """
    class Meta:
        model = NotificationPreference
        fields = [
            'id', 'user',
            'like_push', 'like_email', 'like_in_app',
            'comment_push', 'comment_email', 'comment_in_app',
            'follow_push', 'follow_email', 'follow_in_app',
            'message_push', 'message_email', 'message_in_app',
            'mention_push', 'mention_email', 'mention_in_app',
            'fcm_tokens', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']


class GroupedNotificationSerializer(serializers.Serializer):
    """
    Serializer for grouped notifications.
    """
    notification_type = serializers.CharField()
    count = serializers.IntegerField()
    is_read = serializers.BooleanField()
    latest_created_at = serializers.DateTimeField()
    notifications = NotificationSerializer(many=True, read_only=True)
    content_object_data = serializers.SerializerMethodField()
    text = serializers.SerializerMethodField()
    
    def get_content_object_data(self, obj):
        """Get content object data from the first notification."""
        if obj['notifications']:
            first_notification = obj['notifications'][0]
            serializer = NotificationSerializer(first_notification, context=self.context)
            return serializer.data.get('content_object_data')
        return None
    
    def get_text(self, obj):
        """Generate grouped notification text."""
        count = obj['count']
        notification_type = obj['notification_type']
        
        if count == 1 and obj['notifications']:
            return obj['notifications'][0].get_notification_text()
        
        # Get first sender name
        first_notification = obj['notifications'][0] if obj['notifications'] else None
        if not first_notification or not first_notification.sender:
            return f"You have {count} new notifications"
        
        first_sender = first_notification.sender.get_full_name() or first_notification.sender.username
        
        if count == 2:
            second_sender = obj['notifications'][1].sender.get_full_name() or obj['notifications'][1].sender.username if len(obj['notifications']) > 1 else "someone"
            text_templates = {
                'like': f"{first_sender} and {second_sender} liked your post",
                'comment': f"{first_sender} and {second_sender} commented on your post",
                'follow': f"{first_sender} and {second_sender} started following you",
            }
        else:
            others_count = count - 1
            text_templates = {
                'like': f"{first_sender} and {others_count} others liked your post",
                'comment': f"{first_sender} and {others_count} others commented on your post",
                'follow': f"{first_sender} and {others_count} others started following you",
            }
        
        return text_templates.get(notification_type, f"You have {count} new {notification_type} notifications")

