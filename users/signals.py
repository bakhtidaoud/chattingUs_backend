"""
Signals for the users app.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Follow
from notifications.utils import notify_user


@receiver(post_save, sender=Follow)
def create_follow_notification(sender, instance, created, **kwargs):
    """
    Create notification when a user follows another user.
    """
    if created:
        # Notify the user being followed
        notify_user(
            recipient=instance.following,
            notification_type='follow',
            sender=instance.follower,
            content_object=instance
        )
