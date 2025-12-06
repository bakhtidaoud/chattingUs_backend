"""
Utility functions for user authentication.
"""

import secrets
import random
from datetime import datetime, timedelta
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags


def generate_verification_token():
    """Generate a secure random token for email verification."""
    return secrets.token_urlsafe(32)


def generate_verification_code():
    """Generate a 6-digit verification code for phone verification."""
    return str(random.randint(100000, 999999))


def is_token_expired(token_created_at, expiry_hours=24):
    """Check if a token has expired."""
    if not token_created_at:
        return True
    expiry_time = token_created_at + timedelta(hours=expiry_hours)
    return datetime.now() > expiry_time


def send_verification_email(user, request=None):
    """Send email verification email to user."""
    from .models import User
    
    # Generate verification token
    token = generate_verification_token()
    user.email_verification_token = token
    user.token_created_at = datetime.now()
    user.save()
    
    # Build verification URL
    if request:
        domain = request.get_host()
        protocol = 'https' if request.is_secure() else 'http'
    else:
        domain = settings.ALLOWED_HOSTS[0] if settings.ALLOWED_HOSTS else 'localhost:8000'
        protocol = 'http'
    
    verification_url = f"{protocol}://{domain}/api/users/verify-email/?token={token}"
    
    # Prepare email
    subject = 'Verify Your Email - Chattingus'
    html_message = render_to_string('users/email_verification.html', {
        'user': user,
        'verification_url': verification_url,
    })
    plain_message = strip_tags(html_message)
    
    send_mail(
        subject,
        plain_message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        html_message=html_message,
        fail_silently=False,
    )


def send_password_reset_email(user, request=None):
    """Send password reset email to user with deep link for mobile app."""
    # Generate reset token
    token = generate_verification_token()
    user.password_reset_token = token
    user.token_created_at = datetime.now()
    user.save()
    
    # Build reset URL for mobile app deep linking
    reset_url = f"https://www.chatting-us.com/editpassword/{token}"
    
    # Prepare email
    subject = 'Reset Your Password - Chattingus'
    html_message = render_to_string('users/password_reset.html', {
        'user': user,
        'reset_url': reset_url,
        'expiry_hours': 1,
    })
    plain_message = strip_tags(html_message)
    
    send_mail(
        subject,
        plain_message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        html_message=html_message,
        fail_silently=False,
    )


def send_phone_verification(user):
    """Send SMS verification code to user's phone."""
    # Generate verification code
    code = generate_verification_code()
    user.phone_verification_code = code
    user.token_created_at = datetime.now()
    user.save()
    
    # TODO: Integrate with SMS service (Twilio, AWS SNS, etc.)
    # For now, just print to console in development
    print(f"Phone verification code for {user.username}: {code}")
    
    return code


def send_welcome_email(user):
    """Send welcome email to newly registered user."""
    subject = 'Welcome to Chattingus!'
    html_message = render_to_string('users/welcome.html', {
        'user': user,
    })
    plain_message = strip_tags(html_message)
    
    send_mail(
        subject,
        plain_message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        html_message=html_message,
        fail_silently=True,  # Don't fail registration if welcome email fails
    )
