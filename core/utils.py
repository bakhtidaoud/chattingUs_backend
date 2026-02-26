from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from twilio.rest import Client
from moviepy import VideoFileClip
from django.core.files.base import ContentFile
import os
import logging
import re

logger = logging.getLogger(__name__)

def extract_hashtags(text):
    if not text:
        return []
    return list(set(re.findall(r"#(\w+)", text)))

def extract_mentions(text):
    if not text:
        return []
    return list(set(re.findall(r"@(\w+)", text)))

def send_sms(to_number, body):
    try:
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        message = client.messages.create(
            body=body,
            from_=settings.TWILIO_PHONE_NUMBER,
            to=to_number
        )
        return message.sid
    except Exception as e:
        logger.error(f"Error sending SMS: {e}")
        return None

def generate_video_thumbnail(post_media):
    if post_media.media_type != 'video' or not post_media.file:
        return
    
    try:
        # Create thumbnail from video at 1.0s
        clip = VideoFileClip(post_media.file.path)
        thumbnail_path = f"thumb_{os.path.basename(post_media.file.name)}.jpg"
        clip.save_frame(thumbnail_path, t=1.0)
        
        with open(thumbnail_path, 'rb') as f:
            post_media.thumbnail.save(
                os.path.basename(thumbnail_path),
                ContentFile(f.read()),
                save=True
            )
        
        # Cleanup temp file
        os.remove(thumbnail_path)
        clip.close()
    except Exception as e:
        logger.error(f"Error generating thumbnail: {e}")

def send_verification_email(user):
    verification = user.email_verification
    context = {
        'user': user,
        'verification_url': f"http://localhost:3000/verify-email/{verification.token}/",
    }
    
    html_content = render_to_string('emails/verify_email.html', context)
    text_content = strip_tags(html_content)
    
    email = EmailMultiAlternatives(
        "Verify your ChattingUs account",
        text_content,
        settings.DEFAULT_FROM_EMAIL or 'noreply@chattingus.com',
        [user.email]
    )
    email.attach_alternative(html_content, "text/html")
    email.attach_alternative(html_content, "text/html")
    email.send()

def send_notification(recipient, sender, notification_type, post=None, comment=None, listing=None, priority='normal'):
    from .models import Notification, NotificationSetting
    
    # Get settings for this type
    setting, created = NotificationSetting.objects.get_or_create(
        user=recipient,
        type=notification_type,
        defaults={'email_enabled': True, 'push_enabled': True, 'in_app_enabled': True}
    )
    
    if setting.in_app_enabled:
        Notification.objects.create(
            recipient=recipient,
            sender=sender,
            notification_type=notification_type,
            post=post,
            comment=comment,
            listing=listing
        )
    
    if setting.email_enabled:
        # Mocking email trigger
        # send_mail(...)
        pass
        
    if setting.push_enabled:
        # Mocking rich push notification with Android channels and deep linking
        # payload = {
        #     'to': recipient.fcm_token,
        #     'notification': {
        #         'title': 'New activity!',
        #         'body': f'You have a new {notification_type}',
        #         'android_channel_id': notification_type, # Using type as channel ID
        #     },
        #     'data': {
        #         'screen': 'NotificationDetail',
        #         'id': post.id if post else (listing.id if listing else None),
        #         'priority': priority
        #     }
        # }
        pass
