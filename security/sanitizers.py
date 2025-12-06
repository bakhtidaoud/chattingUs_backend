"""
Input sanitization utilities for XSS prevention.
"""

import bleach
from django.utils.html import escape, strip_tags


# Allowed HTML tags for rich text (very restrictive)
ALLOWED_TAGS = ['p', 'br', 'strong', 'em', 'u', 'a', 'ul', 'ol', 'li']

# Allowed attributes for specific tags
ALLOWED_ATTRIBUTES = {
    'a': ['href', 'title', 'target'],
}

# Allowed protocols for links
ALLOWED_PROTOCOLS = ['http', 'https', 'mailto']


def sanitize_html(text, allowed_tags=None, allowed_attributes=None):
    """
    Sanitize HTML input to prevent XSS while allowing safe tags.
    
    Args:
        text: Input text with HTML
        allowed_tags: List of allowed HTML tags (default: ALLOWED_TAGS)
        allowed_attributes: Dict of allowed attributes per tag (default: ALLOWED_ATTRIBUTES)
    
    Returns:
        Sanitized HTML string
    """
    if text is None:
        return ''
    
    tags = allowed_tags if allowed_tags is not None else ALLOWED_TAGS
    attrs = allowed_attributes if allowed_attributes is not None else ALLOWED_ATTRIBUTES
    
    # Clean HTML
    cleaned = bleach.clean(
        text,
        tags=tags,
        attributes=attrs,
        protocols=ALLOWED_PROTOCOLS,
        strip=True
    )
    
    # Link URLs
    cleaned = bleach.linkify(
        cleaned,
        callbacks=[],
        skip_tags=['pre', 'code']
    )
    
    return cleaned


def sanitize_text(text):
    """
    Completely escape all HTML in text (no HTML allowed).
    
    Args:
        text: Input text
    
    Returns:
        Escaped text string
    """
    if text is None:
        return ''
    
    return escape(str(text))


def strip_all_tags(text):
    """
    Remove all HTML tags from text.
    
    Args:
        text: Input text with HTML
    
    Returns:
        Plain text without any HTML
    """
    if text is None:
        return ''
    
    return strip_tags(str(text))


def sanitize_username(username):
    """
    Sanitize username input.
    
    Args:
        username: Username string
    
    Returns:
        Sanitized username
    """
    if username is None:
        return ''
    
    # Remove all HTML and special characters
    cleaned = strip_tags(str(username))
    
    # Remove any non-alphanumeric characters except underscore
    cleaned = ''.join(c for c in cleaned if c.isalnum() or c == '_')
    
    return cleaned[:30]  # Limit length


def sanitize_email(email):
    """
    Sanitize email input.
    
    Args:
        email: Email string
    
    Returns:
        Sanitized email
    """
    if email is None:
        return ''
    
    # Remove HTML and whitespace
    cleaned = strip_tags(str(email)).strip().lower()
    
    return cleaned


def sanitize_url(url):
    """
    Sanitize URL input to prevent XSS.
    
    Args:
        url: URL string
    
    Returns:
        Sanitized URL or empty string if dangerous
    """
    if url is None:
        return ''
    
    url = str(url).strip()
    
    # Check for dangerous protocols
    dangerous_protocols = ['javascript:', 'data:', 'vbscript:', 'file:']
    url_lower = url.lower()
    
    for protocol in dangerous_protocols:
        if url_lower.startswith(protocol):
            return ''
    
    # Only allow http and https
    if not (url_lower.startswith('http://') or url_lower.startswith('https://')):
        return ''
    
    return url


def sanitize_filename(filename):
    """
    Sanitize filename to prevent path traversal.
    
    Args:
        filename: Filename string
    
    Returns:
        Safe filename
    """
    if filename is None:
        return ''
    
    # Remove path components
    filename = str(filename).split('/')[-1].split('\\')[-1]
    
    # Remove dangerous characters
    safe_chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._- '
    filename = ''.join(c for c in filename if c in safe_chars)
    
    # Remove leading dots (hidden files)
    filename = filename.lstrip('.')
    
    return filename[:255]  # Limit length


def sanitize_search_query(query):
    """
    Sanitize search query input.
    
    Args:
        query: Search query string
    
    Returns:
        Sanitized query
    """
    if query is None:
        return ''
    
    # Remove HTML
    cleaned = strip_tags(str(query))
    
    # Remove special SQL characters
    dangerous_chars = ['--', ';', '/*', '*/', 'xp_', 'sp_']
    for char in dangerous_chars:
        cleaned = cleaned.replace(char, '')
    
    return cleaned.strip()[:200]  # Limit length
