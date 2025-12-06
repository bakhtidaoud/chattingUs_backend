"""
Signals for the chat app.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Message
from notifications.utils import notify_user


@receiver(post_save, sender=Message)
def create_message_notification(sender, instance, created, **kwargs):
    """
    Create notification when a new message is sent in a chat.
    Notifies all chat participants except the sender.
    """
    if created:
        # Get all chat participants except the sender
        participants = instance.chat.participants.exclude(id=instance.sender.id)
        
        # Notify each participant
        for participant in participants:
            notify_user(
                recipient=participant,
                notification_type='message',
                sender=instance.sender,
                content_object=instance
            )
