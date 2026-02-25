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
    email.send()
