"""
Signals for the stories app.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import StoryReply
from notifications.utils import notify_user


@receiver(post_save, sender=StoryReply)
def create_story_reply_notification(sender, instance, created, **kwargs):
    """
    Create notification when someone replies to a story.
    """
    if created:
        # Notify the story owner
        notify_user(
            recipient=instance.story.user,
            notification_type='comment',
            sender=instance.user,
            content_object=instance
        )
