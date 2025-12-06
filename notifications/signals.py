"""
Signals for the notifications app.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .models import NotificationPreference


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_notification_preferences(sender, instance, created, **kwargs):
    """
    Create notification preferences for new users.
    """
    if created:
        NotificationPreference.objects.create(user=instance)


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def save_notification_preferences(sender, instance, **kwargs):
    """
    Ensure notification preferences exist for all users.
    """
    if not hasattr(instance, 'notification_preferences'):
        NotificationPreference.objects.create(user=instance)
