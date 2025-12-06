"""
Signal handlers for live streaming notifications.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import LiveStream
from notifications.utils import create_notification


@receiver(post_save, sender=LiveStream)
def notify_followers_on_live(sender, instance, created, **kwargs):
    """
    Notify followers when a user goes live.
    """
    if created and instance.status == 'waiting':
        # Get all followers of the streamer
        from users.models import Follow
        
        followers = Follow.objects.filter(
            following=instance.streamer,
            is_active=True
        ).select_related('follower')
        
        # Create notifications for all followers
        for follow in followers:
            create_notification(
                recipient=follow.follower,
                sender=instance.streamer,
                notification_type='live',
                content_object=instance
            )


@receiver(post_save, sender=LiveStream)
def notify_streamer_milestones(sender, instance, **kwargs):
    """
    Notify streamer when reaching viewer milestones.
    """
    if instance.status == 'live':
        milestones = [10, 50, 100, 500, 1000, 5000, 10000]
        
        # Check if viewer count just crossed a milestone
        if instance.viewer_count in milestones:
            create_notification(
                recipient=instance.streamer,
                sender=None,
                notification_type='milestone',
                content_object=instance
            )
