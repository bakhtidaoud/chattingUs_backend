from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
import random
from django.utils import timezone
from .models import CustomUser, UserEmailVerification, SMSDevice, Post, PostMedia, Like, Comment
from .utils import send_verification_email, send_sms
from django_otp.plugins.otp_static.models import StaticDevice, StaticToken
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from .serializers import (
    RegisterSerializer, UserSerializer, CustomTokenObtainPairSerializer, 
    CustomTokenObtainSlidingSerializer, PasswordChangeSerializer,
    PostSerializer, PostMediaSerializer, LikeSerializer, CommentSerializer
)
from rest_framework import viewsets
from rest_framework.decorators import action
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.conf import settings

User = get_user_model()

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

from rest_framework_simplejwt.views import TokenObtainSlidingView

class CustomTokenObtainSlidingView(TokenObtainSlidingView):
    serializer_class = CustomTokenObtainSlidingSerializer

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = RegisterSerializer

class LogoutView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response(status=status.HTTP_400_BAD_REQUEST)

class PasswordChangeView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        serializer = PasswordChangeSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            if user.check_password(serializer.validated_data.get('old_password')):
                user.set_password(serializer.validated_data.get('new_password'))
                user.save()
                update_session_auth_hash(request, user)
                return Response({'message': 'Password changed successfully.'}, status=status.HTTP_200_OK)
            return Response({'error': 'Incorrect old password.'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PasswordResetRequestView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response({'error': 'Email is required.'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'message': 'If an account exists with this email, a reset link has been sent.'}, status=status.HTTP_200_OK)

        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        reset_url = f"http://localhost:3000/reset-password/{uid}/{token}/"  # Placeholder UI URL
        
        send_mail(
            'Password Reset Request',
            f'Click the link to reset your password: {reset_url}',
            settings.DEFAULT_FROM_EMAIL or 'noreply@chattingus.com',
            [email],
            fail_silently=False,
        )
        return Response({'message': 'If an account exists with this email, a reset link has been sent.'}, status=status.HTTP_200_OK)

class PasswordResetConfirmView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user is not None and default_token_generator.check_token(user, token):
            new_password = request.data.get('new_password')
            if not new_password:
                return Response({'error': 'New password is required.'}, status=status.HTTP_400_BAD_REQUEST)
            user.set_password(new_password)
            user.save()
            return Response({'message': 'Password has been reset successfully.'}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Invalid reset link.'}, status=status.HTTP_400_BAD_REQUEST)

class VerifyEmailView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        token = request.data.get('token')
        if not token:
            return Response({'error': 'Token is required.'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            verification = UserEmailVerification.objects.get(token=token)
            if verification.is_expired():
                return Response({'error': 'Token has expired.'}, status=status.HTTP_400_BAD_REQUEST)
            
            user = verification.user
            user.is_verified = True
            user.save()
            
            # Optionally delete token after verification
            verification.delete()
            
            return Response({'message': 'Email verified successfully.'}, status=status.HTTP_200_OK)
        except UserEmailVerification.DoesNotExist:
            return Response({'error': 'Invalid token.'}, status=status.HTTP_400_BAD_REQUEST)

class ResendVerificationView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response({'error': 'Email is required.'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(email=email)
            if user.is_verified:
                return Response({'message': 'Email is already verified.'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Update token or create new one
            verification, created = UserEmailVerification.objects.get_or_create(user=user)
            if not created:
                verification.token = uuid.uuid4()
                verification.expires_at = timezone.now() + timezone.timedelta(hours=24)
                verification.save()
            
            send_verification_email(user)
            return Response({'message': 'Verification email resent.'}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({'message': 'If an account exists with this email, a verification link has been sent.'}, status=status.HTTP_200_OK)

class EnableSMSView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        phone_number = request.data.get('phone_number')
        if not phone_number:
            return Response({'error': 'Phone number is required.'}, status=status.HTTP_400_BAD_REQUEST)
        
        device, created = SMSDevice.objects.get_or_create(user=request.user)
        device.phone_number = phone_number
        device.otp_code = str(random.randint(100000, 999999))
        device.otp_expiry = timezone.now() + timezone.timedelta(minutes=5)
        device.is_confirmed = False
        device.save()
        
        send_sms(phone_number, f"Your ChattingUs verification code is: {device.otp_code}")
        return Response({'message': 'Verification code sent to your phone.'}, status=status.HTTP_200_OK)

class VerifySMSView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        code = request.data.get('code')
        try:
            device = request.user.sms_device
            if device.otp_code == code and device.is_valid():
                device.is_confirmed = True
                device.save()
                
                user = request.user
                user.is_2fa_enabled = True
                user.save()
                
                # Generate static backup codes if they don't exist
                static_device, created = StaticDevice.objects.get_or_create(user=user, name='backup-codes')
                if created:
                    for _ in range(10):
                        token = str(random.randint(10000000, 99999999))
                        StaticToken.objects.create(device=static_device, token=token)
                
                return Response({'message': '2FA enabled successfully.'}, status=status.HTTP_200_OK)
            return Response({'error': 'Invalid or expired code.'}, status=status.HTTP_400_BAD_REQUEST)
        except SMSDevice.DoesNotExist:
            return Response({'error': 'No SMS device found.'}, status=status.HTTP_400_BAD_REQUEST)

class Disable2FAView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        user = request.user
        user.is_2fa_enabled = False
        user.save()
        
        if hasattr(user, 'sms_device'):
            user.sms_device.delete()
            
        StaticDevice.objects.filter(user=user).delete()
        
        return Response({'message': '2FA disabled successfully.'}, status=status.HTTP_200_OK)

class StaticBackupCodesView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        try:
            device = StaticDevice.objects.get(user=request.user, name='backup-codes')
            tokens = StaticToken.objects.filter(device=device).values_list('token', flat=True)
            return Response({'backup_codes': tokens}, status=status.HTTP_200_OK)
        except StaticDevice.DoesNotExist:
            return Response({'error': 'No backup codes found.'}, status=status.HTTP_400_BAD_REQUEST)

class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all().order_by('-created_at')
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        post = serializer.save(user=self.request.user)
        
        # Handle media files if any
        files = self.request.FILES.getlist('media_files')
        for i, file in enumerate(files):
            # Simple detection of media type
            media_type = 'video' if file.content_type.startswith('video') else 'image'
            PostMedia.objects.create(
                post=post,
                file=file,
                order=i,
                media_type=media_type
            )
        
        # Tags are handled by TaggitSerializer automaticaly if present in data

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def react(self, request, pk=None):
        post = self.get_object()
        reaction_type = request.data.get('reaction_type', 'like')
        
        valid_reactions = [choice[0] for choice in Like.REACTION_CHOICES]
        if reaction_type not in valid_reactions:
            return Response({'error': f'Invalid reaction type. Choose from: {", ".join(valid_reactions)}'}, 
                            status=status.HTTP_400_BAD_REQUEST)
            
        like, created = Like.objects.get_or_create(
            user=request.user, 
            post=post,
            defaults={'reaction_type': reaction_type}
        )
        
        if not created:
            if like.reaction_type == reaction_type:
                like.delete()
                return Response({'status': 'reaction removed'}, status=status.HTTP_200_OK)
            else:
                like.reaction_type = reaction_type
                like.save()
                return Response({'status': 'reaction updated'}, status=status.HTTP_200_OK)
                
        return Response({'status': 'reaction added'}, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'])
    def comments(self, request, pk=None):
        post = self.get_object()
        # Fetch only top-level comments; replies are nested via serializer
        comments = post.comments.filter(parent=None).order_by('-created_at')
        serializer = CommentSerializer(comments, many=True)
        return Response(serializer.data)

class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
