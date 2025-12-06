"""
Celery tasks for notifications app.
"""

from celery import shared_task
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from .utils import send_push_notification, send_email_notification
from .models import Notification

User = get_user_model()


@shared_task
def send_push_notification_task(notification_id, fcm_tokens):
    """
    Async task to send push notification.
    
    Args:
        notification_id: ID of the notification
        fcm_tokens: List of FCM device tokens
    """
    try:
        notification = Notification.objects.get(id=notification_id)
        return send_push_notification(notification, fcm_tokens)
    except Notification.DoesNotExist:
        return False


@shared_task
def send_email_notification_task(notification_id):
    """
    Async task to send email notification.
    
    Args:
        notification_id: ID of the notification
    """
    try:
        notification = Notification.objects.get(id=notification_id)
        return send_email_notification(notification)
    except Notification.DoesNotExist:
        return False


@shared_task
def cleanup_old_notifications(days=30):
    """
    Clean up old read notifications.
    
    Args:
        days: Number of days to keep notifications (default: 30)
    """
    from django.utils import timezone
    from datetime import timedelta
    
    cutoff_date = timezone.now() - timedelta(days=days)
    deleted_count = Notification.objects.filter(
        is_read=True,
        created_at__lt=cutoff_date
    ).delete()[0]
    
    return f"Deleted {deleted_count} old notifications"
