"""
Security middleware for additional protection.
"""

import logging
from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse

logger = logging.getLogger('security')


class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Add security headers to all responses.
    """
    def process_response(self, request, response):
        # X-Content-Type-Options
        response['X-Content-Type-Options'] = 'nosniff'
        
        # X-Frame-Options
        response['X-Frame-Options'] = 'DENY'
        
        # X-XSS-Protection
        response['X-XSS-Protection'] = '1; mode=block'
        
        # Referrer-Policy
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Permissions-Policy (formerly Feature-Policy)
        response['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        
        # Content-Security-Policy (updated for admin dashboard)
        if not response.get('Content-Security-Policy'):
            response['Content-Security-Policy'] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdnjs.cloudflare.com; "
                "font-src 'self' data: https://fonts.gstatic.com https://cdnjs.cloudflare.com; "
                "img-src 'self' data: https: http:; "
                "connect-src 'self' ws: wss: https://cdn.jsdelivr.net;"
            )
        
        return response


class RequestLoggingMiddleware(MiddlewareMixin):
    """
    Log security-relevant requests.
    """
    def process_request(self, request):
        # Log authentication attempts
        if request.path in ['/api/token/', '/api/users/login/']:
            logger.info(
                f'Authentication attempt from {self.get_client_ip(request)} '
                f'to {request.path}'
            )
        
        # Log sensitive operations
        sensitive_paths = [
            '/api/users/password-reset/',
            '/api/users/change-password/',
            '/api/security/2fa/',
        ]
        
        if any(request.path.startswith(path) for path in sensitive_paths):
            logger.info(
                f'Sensitive operation: {request.method} {request.path} '
                f'from {self.get_client_ip(request)}'
            )
        
        return None
    
    @staticmethod
    def get_client_ip(request):
        """Get client IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class FailedLoginMiddleware(MiddlewareMixin):
    """
    Track failed login attempts and implement temporary IP blocking.
    """
    # In-memory storage (use Redis in production)
    failed_attempts = {}
    blocked_ips = {}
    
    MAX_ATTEMPTS = 10
    BLOCK_DURATION = 3600  # 1 hour in seconds
    
    def process_request(self, request):
        if request.path in ['/api/token/', '/api/users/login/']:
            ip = self.get_client_ip(request)
            
            # Check if IP is blocked
            if ip in self.blocked_ips:
                import time
                if time.time() < self.blocked_ips[ip]:
                    logger.warning(f'Blocked IP attempted login: {ip}')
                    return JsonResponse({
                        'error': 'Too many failed login attempts',
                        'detail': 'Your IP has been temporarily blocked. Please try again later.'
                    }, status=403)
                else:
                    # Unblock if time has passed
                    del self.blocked_ips[ip]
                    if ip in self.failed_attempts:
                        del self.failed_attempts[ip]
        
        return None
    
    def process_response(self, request, response):
        if request.path in ['/api/token/', '/api/users/login/']:
            ip = self.get_client_ip(request)
            
            # Track failed attempts
            if response.status_code in [401, 403]:
                self.failed_attempts[ip] = self.failed_attempts.get(ip, 0) + 1
                logger.warning(
                    f'Failed login attempt #{self.failed_attempts[ip]} from {ip}'
                )
                
                # Block if too many attempts
                if self.failed_attempts[ip] >= self.MAX_ATTEMPTS:
                    import time
                    self.blocked_ips[ip] = time.time() + self.BLOCK_DURATION
                    logger.error(f'IP blocked due to too many failed attempts: {ip}')
            
            # Reset on successful login
            elif response.status_code == 200:
                if ip in self.failed_attempts:
                    del self.failed_attempts[ip]
                logger.info(f'Successful login from {ip}')
        
        return response
    
    @staticmethod
    def get_client_ip(request):
        """Get client IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class SuspiciousActivityMiddleware(MiddlewareMixin):
    """
    Detect and log suspicious activity.
    """
    def process_request(self, request):
        # Check for suspicious patterns in request
        suspicious_patterns = [
            '../',  # Path traversal
            '<script',  # XSS attempt
            'UNION SELECT',  # SQL injection
            'DROP TABLE',  # SQL injection
            'javascript:',  # XSS attempt
        ]
        
        # Check URL and query parameters
        full_path = request.get_full_path().lower()
        for pattern in suspicious_patterns:
            if pattern.lower() in full_path:
                logger.warning(
                    f'Suspicious activity detected: {pattern} in URL from '
                    f'{self.get_client_ip(request)}'
                )
        
        # Check POST data
        if request.method == 'POST':
            try:
                body = request.body.decode('utf-8').lower()
                for pattern in suspicious_patterns:
                    if pattern.lower() in body:
                        logger.warning(
                            f'Suspicious activity detected: {pattern} in POST data from '
                            f'{self.get_client_ip(request)}'
                        )
            except:
                pass
        
        return None
    
    @staticmethod
    def get_client_ip(request):
        """Get client IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
