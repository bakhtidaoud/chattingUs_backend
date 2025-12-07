"""
Mock API for Admin Dashboard Testing
Provides fake data for testing the frontend without full backend implementation
"""

from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from datetime import datetime, timedelta
import random


# ============================================
# AUTHENTICATION ENDPOINTS
# ============================================

@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
def mock_login(request):
    """Mock login endpoint"""
    email = request.data.get('email')
    password = request.data.get('password')
    
    # Accept any credentials for testing
    return Response({
        'access': 'mock_access_token_12345',
        'refresh': 'mock_refresh_token_67890',
        'user': {
            'id': 1,
            'email': email,
            'username': 'admin',
            'first_name': 'Admin',
            'last_name': 'User',
            'is_staff': True,
            'is_superuser': True
        }
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def mock_logout(request):
    """Mock logout endpoint"""
    return Response({'message': 'Logged out successfully'})


@api_view(['GET'])
@permission_classes([AllowAny])
def mock_current_user(request):
    """Mock current user endpoint"""
    return Response({
        'id': 1,
        'email': 'admin@chattingus.com',
        'username': 'admin',
        'first_name': 'Admin',
        'last_name': 'User',
        'profile_picture': 'https://ui-avatars.com/api/?name=Admin+User',
        'is_staff': True,
        'is_superuser': True
    })


# ============================================
# DASHBOARD ANALYTICS
# ============================================

@api_view(['GET'])
@authentication_classes([])
@permission_classes([AllowAny])
def mock_dashboard_stats(request):
    """Mock dashboard statistics"""
    return Response({
        'total_users': 15234,
        'total_posts': 45678,
        'total_reports': 234,
        'active_streams': 12,
        'user_growth': [
            {'date': '2024-01-01', 'count': 1000},
            {'date': '2024-02-01', 'count': 2500},
            {'date': '2024-03-01', 'count': 4200},
            {'date': '2024-04-01', 'count': 6800},
            {'date': '2024-05-01', 'count': 9500},
            {'date': '2024-06-01', 'count': 12300},
            {'date': '2024-07-01', 'count': 15234},
        ],
        'content_activity': [
            {'type': 'Posts', 'count': 45678},
            {'type': 'Stories', 'count': 23456},
            {'type': 'Reels', 'count': 12345},
            {'type': 'Live Streams', 'count': 567},
        ]
    })


# ============================================
# USERS ENDPOINTS
# ============================================

@api_view(['GET'])
@authentication_classes([])
@permission_classes([AllowAny])
def mock_users_list(request):
    """Mock users list"""
    users = []
    for i in range(1, 21):
        users.append({
            'id': i,
            'username': f'user{i}',
            'email': f'user{i}@example.com',
            'first_name': f'User',
            'last_name': f'{i}',
            'profile_picture': f'https://ui-avatars.com/api/?name=User+{i}',
            'is_active': random.choice([True, True, True, False]),
            'is_verified': random.choice([True, True, False]),
            'date_joined': (datetime.now() - timedelta(days=random.randint(1, 365))).isoformat(),
            'last_login': (datetime.now() - timedelta(hours=random.randint(1, 72))).isoformat(),
        })
    
    return Response({
        'count': 100,
        'next': None,
        'previous': None,
        'results': users
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def mock_user_detail(request, pk):
    """Mock user detail"""
    return Response({
        'id': pk,
        'username': f'user{pk}',
        'email': f'user{pk}@example.com',
        'first_name': 'User',
        'last_name': str(pk),
        'profile_picture': f'https://ui-avatars.com/api/?name=User+{pk}',
        'bio': 'This is a test user bio',
        'is_active': True,
        'is_verified': True,
        'date_joined': datetime.now().isoformat(),
        'posts_count': random.randint(10, 100),
        'followers_count': random.randint(100, 1000),
        'following_count': random.randint(50, 500),
    })


# ============================================
# POSTS ENDPOINTS
# ============================================

@api_view(['GET'])
@permission_classes([AllowAny])
def mock_posts_list(request):
    """Mock posts list"""
    posts = []
    for i in range(1, 21):
        posts.append({
            'id': i,
            'user': {
                'id': i,
                'username': f'user{i}',
                'profile_picture': f'https://ui-avatars.com/api/?name=User+{i}'
            },
            'caption': f'This is test post #{i}',
            'image': f'https://picsum.photos/400/400?random={i}',
            'likes_count': random.randint(10, 1000),
            'comments_count': random.randint(5, 100),
            'created_at': (datetime.now() - timedelta(hours=random.randint(1, 72))).isoformat(),
            'is_archived': False,
        })
    
    return Response({
        'count': 100,
        'next': None,
        'previous': None,
        'results': posts
    })


# ============================================
# STORIES ENDPOINTS
# ============================================

@api_view(['GET'])
@permission_classes([AllowAny])
def mock_stories_list(request):
    """Mock stories list"""
    stories = []
    for i in range(1, 21):
        expires_at = datetime.now() + timedelta(hours=random.randint(1, 24))
        stories.append({
            'id': i,
            'user': {
                'id': i,
                'username': f'user{i}',
                'profile_picture': f'https://ui-avatars.com/api/?name=User+{i}'
            },
            'media_type': random.choice(['image', 'video']),
            'media_url': f'https://picsum.photos/400/600?random={i}',
            'created_at': (datetime.now() - timedelta(hours=random.randint(1, 12))).isoformat(),
            'expires_at': expires_at.isoformat(),
            'is_expired': False,
            'views_count': random.randint(10, 500),
        })
    
    return Response({
        'count': 50,
        'next': None,
        'previous': None,
        'results': stories
    })


# ============================================
# SECURITY ENDPOINTS
# ============================================

@api_view(['GET'])
@permission_classes([AllowAny])
def mock_security_overview(request):
    """Mock security overview"""
    return Response({
        'users_with_2fa': 1234,
        'failed_logins_24h': 45,
        'suspicious_activities': 8,
        'blocked_ips': 23,
        'active_sessions': 567,
    })


# ============================================
# SETTINGS ENDPOINTS
# ============================================

@api_view(['GET'])
@permission_classes([AllowAny])
def mock_settings_get(request):
    """Mock get settings"""
    return Response({
        'site_name': 'ChattingUs',
        'site_description': 'Social Media Platform',
        'contact_email': 'contact@chattingus.com',
        'support_email': 'support@chattingus.com',
        'smtp_host': 'smtp.gmail.com',
        'smtp_port': 587,
        'max_file_size': 10485760,  # 10MB
        'allowed_file_types': 'jpg,jpeg,png,gif,mp4,mov',
        'jwt_lifetime': 3600,
        'min_password_length': 8,
        'require_uppercase': True,
        'require_numbers': True,
        'require_special_chars': False,
        'enforce_2fa': False,
        'session_timeout': 86400,
        'api_rate_limit': 1000,
        'pagination_size': 20,
    })


@api_view(['PUT'])
@permission_classes([AllowAny])
def mock_settings_update(request):
    """Mock update settings"""
    return Response({
        'message': 'Settings updated successfully',
        **request.data
    })


# ============================================
# MODERATION ENDPOINTS
# ============================================

@api_view(['GET'])
@permission_classes([AllowAny])
def mock_reports_list(request):
    """Mock reports list"""
    reports = []
    report_types = ['spam', 'harassment', 'hate_speech', 'violence', 'nudity']
    priorities = ['low', 'medium', 'high', 'urgent']
    
    for i in range(1, 21):
        reports.append({
            'id': i,
            'reporter': {
                'id': i,
                'username': f'reporter{i}',
                'profile_picture': f'https://ui-avatars.com/api/?name=Reporter+{i}'
            },
            'reported_user': {
                'id': i + 100,
                'username': f'reported{i}',
            },
            'type': random.choice(report_types),
            'priority': random.choice(priorities),
            'description': f'This is a test report #{i}',
            'status': 'pending',
            'created_at': (datetime.now() - timedelta(hours=random.randint(1, 48))).isoformat(),
        })
    
    return Response({
        'count': 50,
        'next': None,
        'previous': None,
        'results': reports
    })


# URL patterns for mock API
from django.urls import path

urlpatterns = [
    # Auth
    path('auth/login/', mock_login),
    path('auth/logout/', mock_logout),
    path('auth/me/', mock_current_user),
    
    # Analytics
    path('analytics/dashboard/', mock_dashboard_stats),
    
    # Users
    path('users/', mock_users_list),
    path('users/<int:pk>/', mock_user_detail),
    
    # Posts
    path('posts/', mock_posts_list),
    
    # Stories
    path('stories/', mock_stories_list),
    
    # Security
    path('security/overview/', mock_security_overview),
    
    # Settings
    path('settings/', mock_settings_get),
    
    # Moderation
    path('moderation/reports/', mock_reports_list),
]
