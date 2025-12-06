"""
Views for Firebase social authentication (Google, Microsoft).
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from .firebase_auth import (
    verify_firebase_token,
    get_or_create_user_from_firebase,
    link_social_account,
    validate_provider
)
from .social_serializers import (
    FirebaseAuthSerializer,
    SocialAuthResponseSerializer,
    LinkSocialAccountSerializer
)


@api_view(['POST'])
@permission_classes([AllowAny])
def firebase_auth(request):
    """
    Authenticate user with Firebase ID token (Google or Microsoft).
    
    POST /api/users/auth/firebase/
    {
        "id_token": "firebase_id_token",
        "provider": "google"  // or "microsoft"
    }
    
    Returns JWT tokens and user data.
    """
    serializer = FirebaseAuthSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    id_token = serializer.validated_data['id_token']
    provider = serializer.validated_data['provider']
    
    try:
        # Validate provider
        validate_provider(provider)
        
        # Verify Firebase token
        decoded_token = verify_firebase_token(id_token)
        
        # Get or create user
        user, created = get_or_create_user_from_firebase(decoded_token, provider)
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        # Prepare response
        response_serializer = SocialAuthResponseSerializer(user)
        response_data = response_serializer.data
        response_data['access'] = str(refresh.access_token)
        response_data['refresh'] = str(refresh)
        response_data['created'] = created
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def link_social_account_view(request):
    """
    Link a social account (Google or Microsoft) to existing user.
    
    POST /api/users/auth/link-social/
    Authorization: Bearer <jwt_token>
    {
        "id_token": "firebase_id_token",
        "provider": "google"  // or "microsoft"
    }
    
    Returns updated user data.
    """
    serializer = LinkSocialAccountSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    id_token = serializer.validated_data['id_token']
    provider = serializer.validated_data['provider']
    
    try:
        # Validate provider
        validate_provider(provider)
        
        # Verify Firebase token
        decoded_token = verify_firebase_token(id_token)
        firebase_uid = decoded_token.get('uid')
        
        if not firebase_uid:
            return Response(
                {'error': 'Firebase UID not found in token'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Link social account
        user = link_social_account(request.user, firebase_uid, provider)
        
        # Prepare response
        response_serializer = SocialAuthResponseSerializer(user)
        
        return Response(response_serializer.data, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def unlink_social_account_view(request):
    """
    Unlink social account from user (if they have a password set).
    
    POST /api/users/auth/unlink-social/
    Authorization: Bearer <jwt_token>
    
    Returns updated user data.
    """
    user = request.user
    
    # Check if user has a usable password
    if not user.has_usable_password():
        return Response(
            {'error': 'Cannot unlink social account. Please set a password first.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Unlink social account
    user.firebase_uid = None
    user.auth_provider = 'email'
    user.is_social_auth = False
    user.save()
    
    # Prepare response
    response_serializer = SocialAuthResponseSerializer(user)
    
    return Response(response_serializer.data, status=status.HTTP_200_OK)
