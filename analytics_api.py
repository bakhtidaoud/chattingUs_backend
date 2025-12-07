"""
Analytics API for Admin Dashboard
Provides real statistics from the database
"""

from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from datetime import datetime, timedelta
from django.utils import timezone

User = get_user_model()


@api_view(['GET'])
@authentication_classes([])  # Bypass authentication for now
@permission_classes([AllowAny])  # Allow anyone to access
def dashboard_stats(request):
    """
    Get dashboard statistics from real database
    """
    # Get total counts
    total_users = User.objects.count()
    
    # Try to get counts from other models if they exist
    try:
        from posts.models import Post
        total_posts = Post.objects.count()
    except:
        total_posts = 0
    
    try:
        from stories.models import Story
        total_stories = Story.objects.count()
    except:
        total_stories = 0
    
    try:
        from reels.models import Reel
        total_reels = Reel.objects.count()
    except:
        total_reels = 0
    
    try:
        from live.models import LiveStream
        active_streams = LiveStream.objects.filter(is_active=True).count()
    except:
        active_streams = 0
    
    try:
        from moderation.models import Report
        total_reports = Report.objects.count()
        pending_reports = Report.objects.filter(status='pending').count()
    except:
        total_reports = 0
        pending_reports = 0
    
    # Get user growth data (last 7 months)
    user_growth = []
    for i in range(6, -1, -1):
        date = timezone.now() - timedelta(days=i*30)
        count = User.objects.filter(date_joined__lte=date).count()
        user_growth.append({
            'date': date.strftime('%Y-%m-%d'),
            'count': count
        })
    
    # Get content activity
    content_activity = [
        {'type': 'Posts', 'count': total_posts},
        {'type': 'Stories', 'count': total_stories},
        {'type': 'Reels', 'count': total_reels},
        {'type': 'Live Streams', 'count': active_streams},
    ]
    
    # Get recent activity counts
    last_week = timezone.now() - timedelta(days=7)
    new_users_week = User.objects.filter(date_joined__gte=last_week).count()
    
    try:
        new_posts_week = Post.objects.filter(created_at__gte=last_week).count()
    except:
        new_posts_week = 0
    
    return Response({
        'total_users': total_users,
        'total_posts': total_posts,
        'total_stories': total_stories,
        'total_reels': total_reels,
        'total_reports': total_reports,
        'pending_reports': pending_reports,
        'active_streams': active_streams,
        'new_users_this_week': new_users_week,
        'new_posts_this_week': new_posts_week,
        'user_growth': user_growth,
        'content_activity': content_activity,
    })


@api_view(['GET'])
@authentication_classes([])
@permission_classes([AllowAny])
def user_growth_stats(request):
    """
    Get detailed user growth statistics
    """
    days = int(request.GET.get('days', 30))
    
    growth_data = []
    for i in range(days, -1, -1):
        date = timezone.now() - timedelta(days=i)
        count = User.objects.filter(date_joined__date=date.date()).count()
        growth_data.append({
            'date': date.strftime('%Y-%m-%d'),
            'count': count
        })
    
    return Response(growth_data)


@api_view(['GET'])
@authentication_classes([])
@permission_classes([AllowAny])
def content_activity_stats(request):
    """
    Get content activity statistics
    """
    days = int(request.GET.get('days', 30))
    start_date = timezone.now() - timedelta(days=days)
    
    activity_data = []
    
    try:
        from posts.models import Post
        posts_count = Post.objects.filter(created_at__gte=start_date).count()
    except:
        posts_count = 0
    
    try:
        from stories.models import Story
        stories_count = Story.objects.filter(created_at__gte=start_date).count()
    except:
        stories_count = 0
    
    try:
        from reels.models import Reel
        reels_count = Reel.objects.filter(created_at__gte=start_date).count()
    except:
        reels_count = 0
    
    activity_data = [
        {'type': 'Posts', 'count': posts_count},
        {'type': 'Stories', 'count': stories_count},
        {'type': 'Reels', 'count': reels_count},
    ]
    
    return Response(activity_data)
