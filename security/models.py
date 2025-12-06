"""
Two-Factor Authentication models.
"""

from django.db import models
from django.conf import settings
import pyotp
import secrets
import qrcode
from io import BytesIO
import base64


class TwoFactorAuth(models.Model):
    """
    Two-Factor Authentication settings for users.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='two_factor_auth'
    )
    secret_key = models.CharField(max_length=32, blank=True)
    is_enabled = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Two-Factor Authentication'
        verbose_name_plural = 'Two-Factor Authentications'
    
    def __str__(self):
        return f"2FA for {self.user.username}"
    
    def generate_secret_key(self):
        """Generate a new secret key for TOTP."""
        self.secret_key = pyotp.random_base32()
        self.save()
        return self.secret_key
    
    def get_totp_uri(self):
        """Get TOTP URI for QR code generation."""
        if not self.secret_key:
            self.generate_secret_key()
        
        return pyotp.totp.TOTP(self.secret_key).provisioning_uri(
            name=self.user.email or self.user.username,
            issuer_name='ChattingUs'
        )
    
    def get_qr_code(self):
        """Generate QR code as base64 image."""
        uri = self.get_totp_uri()
        
        # Generate QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        return f"data:image/png;base64,{img_str}"
    
    def verify_token(self, token):
        """Verify TOTP token."""
        if not self.secret_key:
            return False
        
        totp = pyotp.TOTP(self.secret_key)
        return totp.verify(token, valid_window=1)
    
    def enable(self):
        """Enable 2FA."""
        self.is_enabled = True
        self.is_verified = True
        self.save()
    
    def disable(self):
        """Disable 2FA."""
        self.is_enabled = False
        self.is_verified = False
        self.save()


class BackupCode(models.Model):
    """
    Backup codes for 2FA recovery.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='backup_codes'
    )
    code = models.CharField(max_length=10, unique=True)
    used = models.BooleanField(default=False)
    used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Backup Code'
        verbose_name_plural = 'Backup Codes'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Backup code for {self.user.username}"
    
    @staticmethod
    def generate_code():
        """Generate a random backup code."""
        return ''.join(secrets.choice('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ') for _ in range(10))
    
    @classmethod
    def generate_codes_for_user(cls, user, count=10):
        """
        Generate backup codes for a user.
        
        Args:
            user: User instance
            count: Number of codes to generate (default: 10)
        
        Returns:
            List of generated codes
        """
        # Delete existing unused codes
        cls.objects.filter(user=user, used=False).delete()
        
        codes = []
        for _ in range(count):
            code = cls.generate_code()
            backup_code = cls.objects.create(user=user, code=code)
            codes.append(code)
        
        return codes
    
    def use(self):
        """Mark backup code as used."""
        from django.utils import timezone
        self.used = True
        self.used_at = timezone.now()
        self.save()
    
    @classmethod
    def verify_code(cls, user, code):
        """
        Verify backup code for user.
        
        Args:
            user: User instance
            code: Backup code to verify
        
        Returns:
            bool: True if code is valid and unused
        """
        try:
            backup_code = cls.objects.get(user=user, code=code, used=False)
            backup_code.use()
            return True
        except cls.DoesNotExist:
            return False
