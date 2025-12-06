"""
Utility functions for creating and sending notifications.
"""

import json
import logging
from typing import Optional, List
from django.contrib.contenttypes.models import ContentType
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import Notification, NotificationPreference

logger = logging.getLogger(__name__)

# Firebase Admin SDK
try:
    import firebase_admin
    from firebase_admin import credentials, messaging
    
    # Initialize Firebase Admin SDK
    if not firebase_admin._apps:
        cred_path = getattr(settings, 'FIREBASE_CREDENTIALS_PATH', None)
        if cred_path:
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
            logger.info("Firebase Admin SDK initialized successfully")
    
    FIREBASE_AVAILABLE = True
except Exception as e:
    logger.warning(f"Firebase Admin SDK not available: {e}")
    FIREBASE_AVAILABLE = False


def create_notification(
    recipient,
    notification_type: str,
    sender=None,
    content_object=None,
    **kwargs
) -> Optional[Notification]:
    """
    Create a notification in the database.
    
    Args:
        recipient: User object who will receive the notification
        notification_type: Type of notification ('like', 'comment', 'follow', 'message', 'mention')
        sender: User object who triggered the notification (optional)
        content_object: The related object (Post, Comment, etc.) (optional)
        **kwargs: Additional fields for the notification
    
    Returns:
        Notification object or None if creation failed
    """
    try:
        # Get user preferences
        preferences = getattr(recipient, 'notification_preferences', None)
        
        # Check if in-app notifications are enabled for this type
        if preferences and not preferences.is_enabled(notification_type, 'in_app'):
            logger.info(f"In-app notifications disabled for {recipient.username} - {notification_type}")
            return None
        
        # Prepare notification data
        notification_data = {
            'recipient': recipient,
            'sender': sender,
            'notification_type': notification_type,
        }
        
        # Add content object if provided
        if content_object:
            notification_data['content_type'] = ContentType.objects.get_for_model(content_object)
            notification_data['object_id'] = content_object.id
        
        # Create notification
        notification = Notification.objects.create(**notification_data)
        logger.info(f"Created notification {notification.id} for {recipient.username}")
        
        return notification
        
    except Exception as e:
        logger.error(f"Error creating notification: {e}")
        return None


def send_push_notification(
    notification: Notification,
    fcm_tokens: List[str]
) -> bool:
    """
    Send push notification via Firebase Cloud Messaging.
    
    Args:
        notification: Notification object
        fcm_tokens: List of FCM device tokens
    
    Returns:
        bool: True if successful, False otherwise
    """
    if not FIREBASE_AVAILABLE:
        logger.warning("Firebase not available, skipping push notification")
        return False
    
    if not fcm_tokens:
        logger.info("No FCM tokens available")
        return False
    
    try:
        # Prepare notification payload
        title = "ChattingUs"
        body = notification.get_notification_text()
        
        # Get sender profile picture URL if available
        image_url = None
        if notification.sender and notification.sender.profile_picture:
            image_url = notification.sender.profile_picture.url
        
        # Create message
        message_data = {
            'notification_id': str(notification.id),
            'notification_type': notification.notification_type,
            'sender_id': str(notification.sender.id) if notification.sender else None,
            'link': notification.get_notification_link(),
        }
        
        # Send to each token
        success_count = 0
        failed_tokens = []
        
        for token in fcm_tokens:
            try:
                message = messaging.Message(
                    notification=messaging.Notification(
                        title=title,
                        body=body,
                        image=image_url,
                    ),
                    data=message_data,
                    token=token,
                    android=messaging.AndroidConfig(
                        priority='high',
                        notification=messaging.AndroidNotification(
                            sound='default',
                            color='#FF69B4',
                        ),
                    ),
                    apns=messaging.APNSConfig(
                        payload=messaging.APNSPayload(
                            aps=messaging.Aps(
                                sound='default',
                                badge=1,
                            ),
                        ),
                    ),
                )
                
                response = messaging.send(message)
                success_count += 1
                logger.info(f"Push notification sent successfully: {response}")
                
            except messaging.UnregisteredError:
                logger.warning(f"Invalid FCM token: {token}")
                failed_tokens.append(token)
            except Exception as e:
                logger.error(f"Error sending push notification to {token}: {e}")
                failed_tokens.append(token)
        
        # Remove failed tokens from user preferences
        if failed_tokens and hasattr(notification.recipient, 'notification_preferences'):
            prefs = notification.recipient.notification_preferences
            for token in failed_tokens:
                prefs.remove_fcm_token(token)
        
        return success_count > 0
        
    except Exception as e:
        logger.error(f"Error sending push notification: {e}")
        return False


def send_email_notification(notification: Notification) -> bool:
    """
    Send email notification.
    
    Args:
        notification: Notification object
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        recipient = notification.recipient
        
        if not recipient.email:
            logger.info(f"No email address for {recipient.username}")
            return False
        
        # Prepare email content
        subject = f"ChattingUs - {notification.get_notification_text()}"
        
        # Create plain text message
        message = f"""
        Hi {recipient.get_full_name() or recipient.username},
        
        {notification.get_notification_text()}
        
        View on ChattingUs: {notification.get_notification_link()}
        
        ---
        You're receiving this email because you have email notifications enabled.
        To change your notification preferences, visit your settings.
        """
        
        # Send email
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient.email],
            fail_silently=False,
        )
        
        logger.info(f"Email notification sent to {recipient.email}")
        return True
        
    except Exception as e:
        logger.error(f"Error sending email notification: {e}")
        return False


def send_realtime_notification(notification: Notification) -> bool:
    """
    Send real-time notification via WebSocket.
    
    Args:
        notification: Notification object
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        channel_layer = get_channel_layer()
        
        if not channel_layer:
            logger.warning("Channel layer not configured")
            return False
        
        # Prepare notification data
        notification_data = {
            'id': notification.id,
            'type': notification.notification_type,
            'text': notification.get_notification_text(),
            'link': notification.get_notification_link(),
            'sender': {
                'id': notification.sender.id if notification.sender else None,
                'username': notification.sender.username if notification.sender else None,
                'profile_picture': notification.sender.profile_picture.url if notification.sender and notification.sender.profile_picture else None,
            },
            'is_read': notification.is_read,
            'created_at': notification.created_at.isoformat(),
            'time_ago': notification.time_ago,
        }
        
        # Send to user's notification group
        group_name = f'notifications_{notification.recipient.id}'
        
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                'type': 'send_notification',
                'notification': notification_data,
            }
        )
        
        logger.info(f"Real-time notification sent to group {group_name}")
        return True
        
    except Exception as e:
        logger.error(f"Error sending real-time notification: {e}")
        return False


def notify_user(
    recipient,
    notification_type: str,
    sender=None,
    content_object=None,
    **kwargs
) -> Optional[Notification]:
    """
    Main function to create and send notifications through all enabled channels.
    
    Args:
        recipient: User object who will receive the notification
        notification_type: Type of notification ('like', 'comment', 'follow', 'message', 'mention')
        sender: User object who triggered the notification (optional)
        content_object: The related object (Post, Comment, etc.) (optional)
        **kwargs: Additional fields
    
    Returns:
        Notification object or None if creation failed
    """
    # Don't notify users about their own actions
    if sender and recipient.id == sender.id:
        logger.info(f"Skipping self-notification for {recipient.username}")
        return None
    
    # Create notification in database
    notification = create_notification(
        recipient=recipient,
        notification_type=notification_type,
        sender=sender,
        content_object=content_object,
        **kwargs
    )
    
    if not notification:
        return None
    
    # Get user preferences
    preferences = getattr(recipient, 'notification_preferences', None)
    
    # Send real-time notification
    send_realtime_notification(notification)
    
    # Send push notification if enabled
    if preferences and preferences.is_enabled(notification_type, 'push'):
        if preferences.fcm_tokens:
            send_push_notification(notification, preferences.fcm_tokens)
    
    # Send email notification if enabled
    if preferences and preferences.is_enabled(notification_type, 'email'):
        send_email_notification(notification)
    
    return notification


def group_notifications(notifications):
    """
    Group similar notifications together.
    
    Args:
        notifications: QuerySet of Notification objects
    
    Returns:
        List of grouped notification dictionaries
    """
    grouped = {}
    
    for notification in notifications:
        # Create a key for grouping
        # Group by: notification_type + content_object
        key = f"{notification.notification_type}_{notification.content_type_id}_{notification.object_id}"
        
        if key not in grouped:
            grouped[key] = {
                'notification_type': notification.notification_type,
                'content_type': notification.content_type,
                'object_id': notification.object_id,
                'content_object': notification.content_object,
                'notifications': [],
                'count': 0,
                'is_read': True,  # Will be False if any notification is unread
                'latest_created_at': notification.created_at,
            }
        
        grouped[key]['notifications'].append(notification)
        grouped[key]['count'] += 1
        
        if not notification.is_read:
            grouped[key]['is_read'] = False
        
        if notification.created_at > grouped[key]['latest_created_at']:
            grouped[key]['latest_created_at'] = notification.created_at
    
    # Convert to list and sort by latest_created_at
    result = list(grouped.values())
    result.sort(key=lambda x: x['latest_created_at'], reverse=True)
    
    return result
