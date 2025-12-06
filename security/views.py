"""
Views for security features including 2FA.
"""

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from .models import TwoFactorAuth, BackupCode
from .serializers import (
    TwoFactorAuthSerializer,
    Enable2FASerializer,
    Verify2FASerializer,
    Disable2FASerializer,
    BackupCodeSerializer,
    Login2FASerializer
)
import logging

logger = logging.getLogger('security')
User = get_user_model()


class TwoFactorAuthViewSet(viewsets.ViewSet):
    """
    ViewSet for Two-Factor Authentication management.
    
    Endpoints:
    - GET /api/security/2fa/ - Get 2FA status
    - POST /api/security/2fa/enable/ - Enable 2FA
    - POST /api/security/2fa/verify/ - Verify 2FA token
    - POST /api/security/2fa/disable/ - Disable 2FA
    - GET /api/security/2fa/backup-codes/ - Get backup codes
    - POST /api/security/2fa/regenerate-codes/ - Regenerate backup codes
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def list(self, request):
        """Get 2FA status for current user."""
        two_fa, created = TwoFactorAuth.objects.get_or_create(user=request.user)
        serializer = TwoFactorAuthSerializer(two_fa)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def enable(self, request):
        """
        Enable 2FA for user.
        Generates secret key and returns QR code.
        """
        two_fa, created = TwoFactorAuth.objects.get_or_create(user=request.user)
        
        if two_fa.is_enabled:
            return Response(
                {'error': '2FA is already enabled'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Generate new secret key
        two_fa.generate_secret_key()
        
        serializer = TwoFactorAuthSerializer(two_fa)
        
        logger.info(f'2FA setup initiated for user {request.user.username}')
        
        return Response({
            'message': 'Scan the QR code with your authenticator app',
            'qr_code': two_fa.get_qr_code(),
            'secret_key': two_fa.secret_key,  # For manual entry
            'next_step': 'Verify with a token from your app'
        })
    
    @action(detail=False, methods=['post'])
    def verify(self, request):
        """
        Verify 2FA token and complete setup.
        """
        serializer = Verify2FASerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            two_fa = TwoFactorAuth.objects.get(user=request.user)
        except TwoFactorAuth.DoesNotExist:
            return Response(
                {'error': '2FA not set up. Please enable 2FA first.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        token = serializer.validated_data['token']
        
        if two_fa.verify_token(token):
            two_fa.enable()
            
            # Generate backup codes
            codes = BackupCode.generate_codes_for_user(request.user)
            
            logger.info(f'2FA enabled for user {request.user.username}')
            
            return Response({
                'message': '2FA enabled successfully',
                'backup_codes': codes,
                'warning': 'Save these backup codes in a safe place. You will need them if you lose access to your authenticator app.'
            })
        else:
            logger.warning(f'Invalid 2FA token for user {request.user.username}')
            return Response(
                {'error': 'Invalid token'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['post'])
    def disable(self, request):
        """
        Disable 2FA for user.
        Requires password confirmation.
        """
        serializer = Disable2FASerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        try:
            two_fa = TwoFactorAuth.objects.get(user=request.user)
            two_fa.disable()
            
            # Delete backup codes
            BackupCode.objects.filter(user=request.user).delete()
            
            logger.info(f'2FA disabled for user {request.user.username}')
            
            return Response({'message': '2FA disabled successfully'})
        except TwoFactorAuth.DoesNotExist:
            return Response(
                {'error': '2FA is not enabled'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def backup_codes(self, request):
        """
        Get unused backup codes for user.
        """
        try:
            two_fa = TwoFactorAuth.objects.get(user=request.user)
            if not two_fa.is_enabled:
                return Response(
                    {'error': '2FA is not enabled'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except TwoFactorAuth.DoesNotExist:
            return Response(
                {'error': '2FA is not enabled'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        codes = BackupCode.objects.filter(user=request.user, used=False)
        serializer = BackupCodeSerializer(codes, many=True)
        
        return Response({
            'backup_codes': serializer.data,
            'count': codes.count()
        })
    
    @action(detail=False, methods=['post'])
    def regenerate_codes(self, request):
        """
        Regenerate backup codes.
        Requires password confirmation.
        """
        serializer = Disable2FASerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        try:
            two_fa = TwoFactorAuth.objects.get(user=request.user)
            if not two_fa.is_enabled:
                return Response(
                    {'error': '2FA is not enabled'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except TwoFactorAuth.DoesNotExist:
            return Response(
                {'error': '2FA is not enabled'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Generate new codes
        codes = BackupCode.generate_codes_for_user(request.user)
        
        logger.info(f'Backup codes regenerated for user {request.user.username}')
        
        return Response({
            'message': 'Backup codes regenerated successfully',
            'backup_codes': codes,
            'warning': 'Old backup codes are no longer valid. Save these new codes in a safe place.'
        })


class Login2FAView(viewsets.ViewSet):
    """
    ViewSet for 2FA login verification.
    """
    permission_classes = [permissions.AllowAny]
    
    @action(detail=False, methods=['post'])
    def verify(self, request):
        """
        Verify 2FA token during login.
        This should be called after successful username/password authentication.
        """
        serializer = Login2FASerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Get user from session or token
        # This is a placeholder - implement based on your auth flow
        user_id = request.session.get('pending_2fa_user_id')
        if not user_id:
            return Response(
                {'error': 'No pending 2FA verification'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user = User.objects.get(id=user_id)
            two_fa = TwoFactorAuth.objects.get(user=user, is_enabled=True)
        except (User.DoesNotExist, TwoFactorAuth.DoesNotExist):
            return Response(
                {'error': 'Invalid request'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        token = serializer.validated_data['token']
        
        # Try TOTP token first
        if len(token) == 6 and two_fa.verify_token(token):
            # Clear pending session
            del request.session['pending_2fa_user_id']
            
            logger.info(f'2FA login successful for user {user.username}')
            
            return Response({
                'message': '2FA verification successful',
                'user_id': user.id
            })
        
        # Try backup code
        elif len(token) == 10 and BackupCode.verify_code(user, token):
            # Clear pending session
            del request.session['pending_2fa_user_id']
            
            logger.info(f'2FA login with backup code for user {user.username}')
            
            # Warn about remaining codes
            remaining = BackupCode.objects.filter(user=user, used=False).count()
            
            return Response({
                'message': '2FA verification successful',
                'user_id': user.id,
                'warning': f'You have {remaining} backup codes remaining. Consider regenerating them.'
            })
        
        else:
            logger.warning(f'Invalid 2FA token during login for user {user.username}')
            return Response(
                {'error': 'Invalid token or backup code'},
                status=status.HTTP_400_BAD_REQUEST
            )
