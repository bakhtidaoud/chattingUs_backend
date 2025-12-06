"""
Serializers for security features.
"""

from rest_framework import serializers
from .models import TwoFactorAuth, BackupCode


class TwoFactorAuthSerializer(serializers.ModelSerializer):
    """
    Serializer for 2FA settings.
    """
    qr_code = serializers.SerializerMethodField()
    
    class Meta:
        model = TwoFactorAuth
        fields = ['is_enabled', 'is_verified', 'qr_code', 'created_at', 'updated_at']
        read_only_fields = ['is_verified', 'created_at', 'updated_at']
    
    def get_qr_code(self, obj):
        """Get QR code only if not yet verified."""
        if not obj.is_verified and obj.secret_key:
            return obj.get_qr_code()
        return None


class Enable2FASerializer(serializers.Serializer):
    """
    Serializer for enabling 2FA.
    """
    pass  # No input needed


class Verify2FASerializer(serializers.Serializer):
    """
    Serializer for verifying 2FA token.
    """
    token = serializers.CharField(max_length=6, min_length=6)
    
    def validate_token(self, value):
        """Validate token format."""
        if not value.isdigit():
            raise serializers.ValidationError('Token must be 6 digits')
        return value


class Disable2FASerializer(serializers.Serializer):
    """
    Serializer for disabling 2FA.
    """
    password = serializers.CharField(write_only=True)
    
    def validate_password(self, value):
        """Verify user password."""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Invalid password')
        return value


class BackupCodeSerializer(serializers.ModelSerializer):
    """
    Serializer for backup codes.
    """
    class Meta:
        model = BackupCode
        fields = ['code', 'used', 'used_at', 'created_at']
        read_only_fields = ['code', 'used', 'used_at', 'created_at']


class Login2FASerializer(serializers.Serializer):
    """
    Serializer for 2FA login verification.
    """
    token = serializers.CharField(max_length=10)
    
    def validate_token(self, value):
        """Validate token format (6 digits or 10-char backup code)."""
        if len(value) == 6 and value.isdigit():
            return value
        elif len(value) == 10 and value.isalnum():
            return value.upper()
        else:
            raise serializers.ValidationError(
                'Token must be 6 digits (TOTP) or 10 characters (backup code)'
            )
