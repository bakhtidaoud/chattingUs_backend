"""
Rate limiting decorators and utilities.
"""

from django_ratelimit.decorators import ratelimit
from django.http import JsonResponse
from functools import wraps


def ratelimit_handler(request, exception):
    """
    Custom handler for rate limit exceeded.
    """
    return JsonResponse({
        'error': 'Rate limit exceeded',
        'detail': 'Too many requests. Please try again later.'
    }, status=429)


# Login rate limit: 5 attempts per 15 minutes per IP
login_ratelimit = ratelimit(
    key='ip',
    rate='5/15m',
    method='POST',
    block=True
)


# Password reset: 3 attempts per hour per IP
password_reset_ratelimit = ratelimit(
    key='ip',
    rate='3/h',
    method='POST',
    block=True
)


# Registration: 3 attempts per hour per IP
registration_ratelimit = ratelimit(
    key='ip',
    rate='3/h',
    method='POST',
    block=True
)


# API calls: 100 per minute per user
def api_ratelimit(func):
    """
    Rate limit for authenticated API calls.
    100 requests per minute per user.
    """
    @wraps(func)
    @ratelimit(key='user', rate='100/m', method=ratelimit.ALL, block=True)
    def wrapper(request, *args, **kwargs):
        return func(request, *args, **kwargs)
    return wrapper


# Strict API rate limit: 30 per minute per user (for sensitive operations)
def strict_api_ratelimit(func):
    """
    Strict rate limit for sensitive API operations.
    30 requests per minute per user.
    """
    @wraps(func)
    @ratelimit(key='user', rate='30/m', method=ratelimit.ALL, block=True)
    def wrapper(request, *args, **kwargs):
        return func(request, *args, **kwargs)
    return wrapper


# File upload rate limit: 10 per hour per user
file_upload_ratelimit = ratelimit(
    key='user',
    rate='10/h',
    method='POST',
    block=True
)


# Email sending rate limit: 5 per hour per user
email_ratelimit = ratelimit(
    key='user',
    rate='5/h',
    method='POST',
    block=True
)


# Search rate limit: 60 per minute per IP
search_ratelimit = ratelimit(
    key='ip',
    rate='60/m',
    method='GET',
    block=True
)


def custom_ratelimit(key='ip', rate='100/m', method='POST'):
    """
    Create a custom rate limit decorator.
    
    Args:
        key: Rate limit key ('ip', 'user', or custom function)
        rate: Rate limit (e.g., '100/m', '5/h', '1000/d')
        method: HTTP method(s) to limit
    
    Returns:
        Decorator function
    """
    return ratelimit(key=key, rate=rate, method=method, block=True)


def get_client_ip(request):
    """
    Get client IP address from request.
    Handles proxy headers.
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
