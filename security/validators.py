"""
Security validators for input validation and sanitization.
"""

import re
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


# Username validator
username_validator = RegexValidator(
    regex=r'^[a-zA-Z0-9_]{3,30}$',
    message=_('Username must be 3-30 characters and contain only letters, numbers, and underscores')
)


# Phone number validator
phone_validator = RegexValidator(
    regex=r'^\+?1?\d{9,15}$',
    message=_('Phone number must be in format: +999999999. Up to 15 digits allowed.')
)


class PasswordStrengthValidator:
    """
    Validate password strength.
    """
    def validate(self, password, user=None):
        if len(password) < 8:
            raise ValidationError(
                _('Password must be at least 8 characters long.'),
                code='password_too_short'
            )
        
        if not re.search(r'[A-Z]', password):
            raise ValidationError(
                _('Password must contain at least one uppercase letter.'),
                code='password_no_upper'
            )
        
        if not re.search(r'[a-z]', password):
            raise ValidationError(
                _('Password must contain at least one lowercase letter.'),
                code='password_no_lower'
            )
        
        if not re.search(r'[0-9]', password):
            raise ValidationError(
                _('Password must contain at least one number.'),
                code='password_no_digit'
            )
        
        # Optional: Check for special characters
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise ValidationError(
                _('Password must contain at least one special character.'),
                code='password_no_special'
            )
    
    def get_help_text(self):
        return _(
            'Your password must contain at least 8 characters, including uppercase, '
            'lowercase, numbers, and special characters.'
        )


def validate_no_sql_injection(value):
    """
    Prevent SQL injection in user inputs.
    """
    sql_keywords = [
        'SELECT', 'INSERT', 'UPDATE', 'DELETE', 'DROP',
        'CREATE', 'ALTER', 'EXEC', 'EXECUTE', 'UNION',
        'SCRIPT', 'JAVASCRIPT', 'ONERROR', 'ONLOAD',
        '--', ';--', '/*', '*/', 'XP_', 'SP_'
    ]
    
    value_upper = str(value).upper()
    for keyword in sql_keywords:
        if keyword in value_upper:
            raise ValidationError(
                _('Invalid input detected. Please remove special SQL characters.'),
                code='sql_injection_attempt'
            )


def validate_email_domain(email):
    """
    Validate email domain against blacklist.
    """
    blacklisted_domains = [
        'tempmail.com',
        'throwaway.email',
        'guerrillamail.com',
        '10minutemail.com',
        'mailinator.com',
        'trashmail.com'
    ]
    
    domain = email.split('@')[-1].lower()
    if domain in blacklisted_domains:
        raise ValidationError(
            _('This email domain is not allowed. Please use a valid email address.'),
            code='blacklisted_domain'
        )


def validate_url_safe(value):
    """
    Validate that value is URL-safe (no XSS attempts).
    """
    dangerous_patterns = [
        r'javascript:',
        r'data:',
        r'vbscript:',
        r'on\w+\s*=',  # Event handlers like onclick=
        r'<script',
        r'</script>',
    ]
    
    value_lower = str(value).lower()
    for pattern in dangerous_patterns:
        if re.search(pattern, value_lower):
            raise ValidationError(
                _('Invalid input detected. Please remove potentially dangerous content.'),
                code='xss_attempt'
            )


def validate_safe_filename(filename):
    """
    Validate filename is safe (no path traversal).
    """
    dangerous_patterns = [
        r'\.\.',  # Parent directory
        r'/',     # Path separator
        r'\\',    # Windows path separator
        r'\0',    # Null byte
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, filename):
            raise ValidationError(
                _('Invalid filename. Please use only alphanumeric characters and basic punctuation.'),
                code='unsafe_filename'
            )
    
    # Check for valid filename
    if not re.match(r'^[a-zA-Z0-9_\-. ]+$', filename):
        raise ValidationError(
            _('Filename contains invalid characters.'),
            code='invalid_filename'
        )
