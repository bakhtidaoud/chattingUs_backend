"""
Firebase authentication utilities for social login (Google, Microsoft).
"""

import firebase_admin
from firebase_admin import auth, credentials
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework.exceptions import AuthenticationFailed
import os

User = get_user_model()

# Initialize Firebase Admin SDK
if not firebase_admin._apps:
    cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
    firebase_admin.initialize_app(cred)


def verify_firebase_token(id_token):
    """
    Verify Firebase ID token and return decoded token data.
    
    Args:
        id_token (str): Firebase ID token from client
        
    Returns:
        dict: Decoded token containing user information
        
    Raises:
        AuthenticationFailed: If token is invalid or expired
    """
    try:
        decoded_token = auth.verify_id_token(id_token)
        return decoded_token
    except auth.InvalidIdTokenError:
        raise AuthenticationFailed('Invalid Firebase token')
    except auth.ExpiredIdTokenError:
        raise AuthenticationFailed('Firebase token has expired')
    except auth.RevokedIdTokenError:
        raise AuthenticationFailed('Firebase token has been revoked')
    except Exception as e:
        raise AuthenticationFailed(f'Firebase token verification failed: {str(e)}')


def get_or_create_user_from_firebase(decoded_token, provider='google'):
    """
    Get existing user or create new user from Firebase token data.
    
    Args:
        decoded_token (dict): Decoded Firebase token
        provider (str): Authentication provider ('google' or 'microsoft')
        
    Returns:
        tuple: (User instance, created boolean)
    """
    firebase_uid = decoded_token.get('uid')
    email = decoded_token.get('email', '')
    name = decoded_token.get('name', '')
    picture = decoded_token.get('picture', '')
    email_verified = decoded_token.get('email_verified', False)
    
    if not firebase_uid:
        raise AuthenticationFailed('Firebase UID not found in token')
    
    if not email:
        raise AuthenticationFailed('Email not found in token')
    
    # Try to find user by Firebase UID first
    try:
        user = User.objects.get(firebase_uid=firebase_uid)
        created = False
        
        # Update user info if needed
        if user.email != email:
            user.email = email
        if name and not user.first_name:
            name_parts = name.split(' ', 1)
            user.first_name = name_parts[0]
            if len(name_parts) > 1:
                user.last_name = name_parts[1]
        if email_verified:
            user.email_verified = True
        
        user.save()
        return user, created
        
    except User.DoesNotExist:
        pass
    
    # Try to find user by email
    try:
        user = User.objects.get(email=email)
        
        # Link Firebase account to existing user
        if not user.firebase_uid:
            user.firebase_uid = firebase_uid
            user.auth_provider = provider
            user.is_social_auth = True
            if email_verified:
                user.email_verified = True
            user.save()
            return user, False
        else:
            # User already has a different Firebase UID
            raise AuthenticationFailed(
                'This email is already associated with a different social account'
            )
            
    except User.DoesNotExist:
        pass
    
    # Create new user
    # Generate username from email
    username = email.split('@')[0]
    base_username = username
    counter = 1
    
    # Ensure username is unique
    while User.objects.filter(username=username).exists():
        username = f"{base_username}{counter}"
        counter += 1
    
    # Split name into first and last name
    first_name = ''
    last_name = ''
    if name:
        name_parts = name.split(' ', 1)
        first_name = name_parts[0]
        if len(name_parts) > 1:
            last_name = name_parts[1]
    
    # Create user
    user = User.objects.create(
        username=username,
        email=email,
        first_name=first_name,
        last_name=last_name,
        firebase_uid=firebase_uid,
        auth_provider=provider,
        is_social_auth=True,
        email_verified=email_verified,
    )
    
    # Set unusable password for social auth users
    user.set_unusable_password()
    user.save()
    
    return user, True


def link_social_account(user, firebase_uid, provider):
    """
    Link a social account (Firebase) to an existing user.
    
    Args:
        user (User): Existing user instance
        firebase_uid (str): Firebase UID to link
        provider (str): Authentication provider ('google' or 'microsoft')
        
    Returns:
        User: Updated user instance
        
    Raises:
        AuthenticationFailed: If Firebase UID is already linked to another user
    """
    # Check if Firebase UID is already used by another user
    if User.objects.filter(firebase_uid=firebase_uid).exclude(id=user.id).exists():
        raise AuthenticationFailed(
            'This social account is already linked to another user'
        )
    
    # Link the account
    user.firebase_uid = firebase_uid
    user.auth_provider = provider
    user.is_social_auth = True
    user.save()
    
    return user


def validate_provider(provider):
    """
    Validate that the provider is supported.
    
    Args:
        provider (str): Provider name
        
    Raises:
        AuthenticationFailed: If provider is not supported
    """
    valid_providers = ['google', 'microsoft']
    if provider not in valid_providers:
        raise AuthenticationFailed(
            f'Invalid provider. Must be one of: {", ".join(valid_providers)}'
        )
