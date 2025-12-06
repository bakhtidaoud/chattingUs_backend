"""
Models for the notifications app.
"""

from django.db import models
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from datetime import timedelta


class Notification(models.Model):
    """
    Model for user notifications with GenericForeignKey support.
    """
    NOTIFICATION_TYPES = (
        ('like', 'Like'),
        ('comment', 'Comment'),
        ('follow', 'Follow'),
        ('message', 'Message'),
        ('mention', 'Mention'),
    )
    
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='notifications'
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='sent_notifications', 
        null=True, 
        blank=True
    )
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    
    # GenericForeignKey for flexible content object references
    content_type = models.ForeignKey(
        ContentType, 
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'is_read', '-created_at']),
            models.Index(fields=['recipient', 'notification_type', '-created_at']),
        ]

    def __str__(self):
        return f"Notification for {self.recipient.username}: {self.notification_type}"
    
    def get_notification_text(self):
        """
        Generate notification text based on type and content.
        """
        if not self.sender:
            return "You have a new notification"
        
        sender_name = self.sender.get_full_name() or self.sender.username
        
        text_templates = {
            'like': f"{sender_name} liked your post",
            'comment': f"{sender_name} commented on your post",
            'follow': f"{sender_name} started following you",
            'message': f"{sender_name} sent you a message",
            'mention': f"{sender_name} mentioned you",
        }
        
        return text_templates.get(self.notification_type, "New notification")
    
    def get_notification_link(self):
        """
        Generate notification link based on content object.
        """
        if not self.content_object:
            return ""
        
        content_type_name = self.content_type.model
        
        # Map content types to URL patterns
        url_patterns = {
            'post': f'/posts/{self.object_id}/',
            'reel': f'/reels/{self.object_id}/',
            'story': f'/stories/{self.object_id}/',
            'comment': f'/posts/{getattr(self.content_object, "post_id", "")}/',
            'user': f'/profile/{self.sender.username}/',
            'message': f'/chat/{getattr(self.content_object, "chat_id", "")}/',
        }
        
        return url_patterns.get(content_type_name, "")
    
    @property
    def time_ago(self):
        """
        Get human-readable time difference.
        """
        now = timezone.now()
        diff = now - self.created_at
        
        if diff < timedelta(minutes=1):
            return "just now"
        elif diff < timedelta(hours=1):
            minutes = int(diff.total_seconds() / 60)
            return f"{minutes}m ago"
        elif diff < timedelta(days=1):
            hours = int(diff.total_seconds() / 3600)
            return f"{hours}h ago"
        elif diff < timedelta(days=7):
            days = diff.days
            return f"{days}d ago"
        else:
            return self.created_at.strftime("%b %d")


class NotificationPreference(models.Model):
    """
    Model for user notification preferences.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notification_preferences'
    )
    
    # Notification type preferences
    like_push = models.BooleanField(default=True)
    like_email = models.BooleanField(default=False)
    like_in_app = models.BooleanField(default=True)
    
    comment_push = models.BooleanField(default=True)
    comment_email = models.BooleanField(default=True)
    comment_in_app = models.BooleanField(default=True)
    
    follow_push = models.BooleanField(default=True)
    follow_email = models.BooleanField(default=False)
    follow_in_app = models.BooleanField(default=True)
    
    message_push = models.BooleanField(default=True)
    message_email = models.BooleanField(default=False)
    message_in_app = models.BooleanField(default=True)
    
    mention_push = models.BooleanField(default=True)
    mention_email = models.BooleanField(default=True)
    mention_in_app = models.BooleanField(default=True)
    
    # FCM device tokens (can store multiple devices)
    fcm_tokens = models.JSONField(default=list, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Notification Preference"
        verbose_name_plural = "Notification Preferences"
    
    def __str__(self):
        return f"{self.user.username}'s notification preferences"
    
    def is_enabled(self, notification_type, channel):
        """
        Check if a notification type is enabled for a specific channel.
        
        Args:
            notification_type: 'like', 'comment', 'follow', 'message', 'mention'
            channel: 'push', 'email', 'in_app'
        
        Returns:
            bool: True if enabled, False otherwise
        """
        field_name = f"{notification_type}_{channel}"
        return getattr(self, field_name, True)
    
    def add_fcm_token(self, token):
        """
        Add a new FCM token if it doesn't exist.
        """
        if token and token not in self.fcm_tokens:
            self.fcm_tokens.append(token)
            self.save()
    
    def remove_fcm_token(self, token):
        """
        Remove an FCM token.
        """
        if token in self.fcm_tokens:
            self.fcm_tokens.remove(token)
            self.save()
