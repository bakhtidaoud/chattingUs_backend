"""
Views for the users app - Enhanced for mobile app deep linking.
"""

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from django.utils import timezone
from datetime import datetime
from django.contrib.auth import authenticate

from .models import User, UserProfile, Follow
from .serializers import (
    RegisterSerializer, LoginSerializer, UserSerializer, UserProfileSerializer,
    PasswordResetRequestSerializer, PasswordResetConfirmSerializer,
    EmailVerificationSerializer, PhoneVerificationSerializer,
    ChangePasswordSerializer, FollowSerializer
)
from .utils import (
    send_verification_email, send_password_reset_email,
    send_phone_verification, is_token_expired
)


class RegisterView(APIView):
    """
    API view for user registration.
    """
    permission_classes = [permissions.AllowAny]
    
    @extend_schema(
        summary="Register a new user",
        description="Register a new user with email, username, password, and optional phone number.",
        responses={201: UserSerializer}
    )
    def post(self, request):
        serializer = RegisterSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = serializer.save()
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'user': UserSerializer(user).data,
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                },
                'message': 'Registration successful. Please check your email to verify your account.'
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    """
    API view for user login with email, username, or phone.
    """
    permission_classes = [permissions.AllowAny]
    
    @extend_schema(
        summary="Login user",
        description="Login with email, username, or phone number and password.",
        responses={200: UserSerializer}
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'user': UserSerializer(user).data,
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                },
                'message': 'Login successful.'
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    """
    API view for user logout (blacklist refresh token).
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @extend_schema(
        summary="Logout user",
        description="Blacklist the refresh token to logout the user.",
        request=OpenApiTypes.OBJECT,
        parameters=[
            OpenApiParameter(
                name='refresh',
                description='Refresh token to blacklist',
                required=True,
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY
            )
        ],
        responses={200: OpenApiTypes.OBJECT}
    )
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if not refresh_token:
                return Response(
                    {'error': 'Refresh token is required.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            token = RefreshToken(refresh_token)
            token.blacklist()
            
            return Response({
                'message': 'Logout successful.'
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class ForgotPasswordView(APIView):
    """
    API view for forgot password - accepts email, username, or phone.
    Sends reset link for mobile app deep linking.
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        identifier = request.data.get('identifier')
        
        if not identifier:
            return Response(
                {'error': 'Email, username, or phone number is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Find user by email, username, or phone
        user = None
        if '@' in identifier:
            try:
                user = User.objects.get(email=identifier)
            except User.DoesNotExist:
                pass
        elif identifier.isdigit():
            try:
                user = User.objects.get(phone_number=identifier)
            except User.DoesNotExist:
                pass
        else:
            try:
                user = User.objects.get(username=identifier)
            except User.DoesNotExist:
                pass
        
        if not user:
            # Return success even if user not found (security best practice)
            return Response({
                'message': 'If an account exists with that information, a password reset link has been sent.'
            }, status=status.HTTP_200_OK)
        
        try:
            send_password_reset_email(user, request)
            return Response({
                'message': 'Password reset link sent. Please check your email.',
                'email': user.email  # Show which email it was sent to
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {'error': f'Failed to send email: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class VerifyResetTokenView(APIView):
    """
    API view for verifying password reset token validity.
    """
    permission_classes = [permissions.AllowAny]
    
    """
    API view for verifying password reset token validity.
    """
    permission_classes = [permissions.AllowAny]
    
    @extend_schema(
        summary="Verify reset token",
        description="Check if the password reset token is valid and not expired.",
        parameters=[
            OpenApiParameter(name='token', description='Password reset token', required=True, type=str, location=OpenApiParameter.PATH)
        ],
        responses={200: OpenApiTypes.OBJECT}
    )
    def get(self, request, token):
        try:
            user = User.objects.get(password_reset_token=token)
        except User.DoesNotExist:
            return Response(
                {'valid': False, 'error': 'Invalid or expired token.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if token is expired (1 hour)
        if is_token_expired(user.token_created_at, expiry_hours=1):
            return Response(
                {'valid': False, 'error': 'Token has expired. Please request a new password reset.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return Response({
            'valid': True,
            'message': 'Token is valid.',
            'email': user.email
        }, status=status.HTTP_200_OK)


class ResetPasswordView(APIView):
    """
    API view for resetting password with token.
    Token is one-time use only.
    """
    permission_classes = [permissions.AllowAny]
    
    @extend_schema(
        summary="Reset password",
        description="Reset the user's password using a valid token.",
        request=PasswordResetConfirmSerializer,
        responses={200: OpenApiTypes.OBJECT}
    )
    def post(self, request):
        token = request.data.get('token')
        password = request.data.get('password')
        password2 = request.data.get('password2')
        
        if not all([token, password, password2]):
            return Response(
                {'error': 'Token, password, and password confirmation are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if password != password2:
            return Response(
                {'error': 'Passwords do not match.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user = User.objects.get(password_reset_token=token)
        except User.DoesNotExist:
            return Response(
                {'error': 'Invalid or expired token.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if token is expired (1 hour)
        if is_token_expired(user.token_created_at, expiry_hours=1):
            # Clear the token
            user.password_reset_token = ''
            user.token_created_at = None
            user.save()
            
            return Response(
                {'error': 'Token has expired. Please request a new password reset.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate password strength
        from django.contrib.auth.password_validation import validate_password
        from django.core.exceptions import ValidationError
        
        try:
            validate_password(password, user)
        except ValidationError as e:
            return Response(
                {'error': list(e.messages)},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Reset password and invalidate token (one-time use)
        user.set_password(password)
        user.password_reset_token = ''
        user.token_created_at = None
        user.save()
        
        return Response({
            'message': 'Password reset successful. You can now login with your new password.'
        }, status=status.HTTP_200_OK)


class PasswordResetRequestView(APIView):
    """
    Legacy API view for password reset request (kept for backward compatibility).
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            user = User.objects.get(email=email)
            
            try:
                send_password_reset_email(user, request)
                return Response({
                    'message': 'Password reset email sent. Please check your email.'
                }, status=status.HTTP_200_OK)
            except Exception as e:
                return Response(
                    {'error': f'Failed to send email: {str(e)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetConfirmView(APIView):
    """
    Legacy API view for confirming password reset (kept for backward compatibility).
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        if serializer.is_valid():
            token = serializer.validated_data['token']
            password = serializer.validated_data['password']
            
            try:
                user = User.objects.get(password_reset_token=token)
            except User.DoesNotExist:
                return Response(
                    {'error': 'Invalid or expired token.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check if token is expired (1 hour)
            if is_token_expired(user.token_created_at, expiry_hours=1):
                return Response(
                    {'error': 'Token has expired. Please request a new password reset.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Reset password
            user.set_password(password)
            user.password_reset_token = ''
            user.token_created_at = None
            user.save()
            
            return Response({
                'message': 'Password reset successful. You can now login with your new password.'
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EmailVerificationView(APIView):
    """
    API view for email verification.
    """
    permission_classes = [permissions.AllowAny]
    
    @extend_schema(
        summary="Verify email",
        description="Verify the user's email address using a token.",
        parameters=[
            OpenApiParameter(name='token', description='Email verification token', required=True, type=str, location=OpenApiParameter.QUERY)
        ],
        responses={200: OpenApiTypes.OBJECT}
    )
    def get(self, request):
        token = request.query_params.get('token')
        if not token:
            return Response(
                {'error': 'Token is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user = User.objects.get(email_verification_token=token)
        except User.DoesNotExist:
            return Response(
                {'error': 'Invalid or expired token.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if token is expired (24 hours)
        if is_token_expired(user.token_created_at, expiry_hours=24):
            return Response(
                {'error': 'Token has expired. Please request a new verification email.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verify email
        user.email_verified = True
        user.is_verified = True
        user.email_verification_token = ''
        user.token_created_at = None
        user.save()
        
        return Response({
            'message': 'Email verified successfully!'
        }, status=status.HTTP_200_OK)


class PhoneVerificationView(APIView):
    """
    API view for phone verification.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @extend_schema(
        summary="Verify phone number",
        description="Verify the user's phone number using a code.",
        request=PhoneVerificationSerializer,
        responses={200: OpenApiTypes.OBJECT}
    )
    def post(self, request):
        serializer = PhoneVerificationSerializer(data=request.data)
        if serializer.is_valid():
            code = serializer.validated_data['code']
            user = request.user
            
            if user.phone_verification_code != code:
                return Response(
                    {'error': 'Invalid verification code.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check if code is expired (10 minutes)
            if is_token_expired(user.token_created_at, expiry_hours=0.167):  # 10 minutes
                return Response(
                    {'error': 'Verification code has expired. Please request a new code.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Verify phone
            user.phone_verified = True
            user.phone_verification_code = ''
            user.token_created_at = None
            user.save()
            
            return Response({
                'message': 'Phone number verified successfully!'
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ResendVerificationView(APIView):
    """
    API view for resending verification email or SMS.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @extend_schema(
        summary="Resend verification",
        description="Resend the email or phone verification code.",
        request=OpenApiTypes.OBJECT,
        responses={200: OpenApiTypes.OBJECT}
    )
    def post(self, request):
        verification_type = request.data.get('type')  # 'email' or 'phone'
        user = request.user
        
        if verification_type == 'email':
            if user.email_verified:
                return Response(
                    {'message': 'Email is already verified.'},
                    status=status.HTTP_200_OK
                )
            
            try:
                send_verification_email(user, request)
                return Response({
                    'message': 'Verification email sent. Please check your email.'
                }, status=status.HTTP_200_OK)
            except Exception as e:
                return Response(
                    {'error': f'Failed to send email: {str(e)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        elif verification_type == 'phone':
            if user.phone_verified:
                return Response(
                    {'message': 'Phone number is already verified.'},
                    status=status.HTTP_200_OK
                )
            
            if not user.phone_number:
                return Response(
                    {'error': 'No phone number associated with this account.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            try:
                code = send_phone_verification(user)
                return Response({
                    'message': 'Verification code sent to your phone.',
                    'code': code  # Remove this in production!
                }, status=status.HTTP_200_OK)
            except Exception as e:
                return Response(
                    {'error': f'Failed to send SMS: {str(e)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        else:
            return Response(
                {'error': 'Invalid verification type. Use "email" or "phone".'},
                status=status.HTTP_400_BAD_REQUEST
            )


class ChangePasswordView(APIView):
    """
    API view for changing password.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @extend_schema(
        summary="Change password",
        description="Change the authenticated user's password.",
        request=ChangePasswordSerializer,
        responses={200: OpenApiTypes.OBJECT}
    )
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = request.user
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            
            return Response({
                'message': 'Password changed successfully.'
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserProfileView(APIView):
    """
    API view for getting and updating user profile.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @extend_schema(
        summary="Get user profile",
        description="Get the profile of the authenticated user.",
        responses={200: UserSerializer}
    )
    def get(self, request):
        user = request.user
        serializer = UserSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
        serializer = UserSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @extend_schema(
        summary="Update user profile",
        description="Update the profile of the authenticated user.",
        request=UserSerializer,
        responses={200: UserSerializer}
    )
    def put(self, request):
        user = request.user
        serializer = UserSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for User model.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    @extend_schema(
        summary="Get current user",
        description="Get the profile of the currently authenticated user.",
        responses={200: UserSerializer}
    )
    def me(self, request):
        """
        Get current user profile.
        """
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
    def update(self, request, *args, **kwargs):
        """
        Update user profile (only own profile).
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        # Only allow users to update their own profile
        if instance != request.user and not request.user.is_staff:
            return Response(
                {'error': 'You can only update your own profile'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)
    
    def partial_update(self, request, *args, **kwargs):
        """
        Partially update user profile.
        """
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    @action(detail=True, methods=['post'])
    @action(detail=True, methods=['post'])
    @extend_schema(
        summary="Follow user",
        description="Follow another user.",
        responses={200: OpenApiTypes.OBJECT}
    )
    def follow(self, request, pk=None):
        """
        Follow a user.
        """
        user_to_follow = self.get_object()
        if request.user == user_to_follow:
            return Response({'error': 'You cannot follow yourself'}, status=400)
        
        follow, created = Follow.objects.get_or_create(
            follower=request.user,
            following=user_to_follow
        )
        
        if created:
            return Response({'status': 'following'})
        return Response({'status': 'already following'})

    @action(detail=True, methods=['post'])
    @action(detail=True, methods=['post'])
    @extend_schema(
        summary="Unfollow user",
        description="Unfollow another user.",
        responses={200: OpenApiTypes.OBJECT}
    )
    def unfollow(self, request, pk=None):
        """
        Unfollow a user.
        """
        user_to_unfollow = self.get_object()
        Follow.objects.filter(
            follower=request.user,
            following=user_to_unfollow
        ).delete()
        
        return Response({'status': 'unfollowed'})

