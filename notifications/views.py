"""
Views for the notifications app.
"""

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q
from .models import Notification, NotificationPreference
from .serializers import (
    NotificationSerializer, 
    NotificationPreferenceSerializer,
    GroupedNotificationSerializer
)
from .utils import group_notifications


class NotificationPagination(PageNumberPagination):
    """
    Custom pagination for notifications.
    """
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class NotificationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Notification model.
    
    Endpoints:
    - GET /api/notifications/ - List all notifications
    - GET /api/notifications/{id}/ - Get single notification
    - PUT /api/notifications/{id}/read/ - Mark notification as read
    - PUT /api/notifications/read-all/ - Mark all notifications as read
    - DELETE /api/notifications/{id}/ - Delete notification
    - GET /api/notifications/unread-count/ - Get unread notification count
    - GET /api/notifications/grouped/ - Get grouped notifications
    """
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = NotificationPagination

    def get_queryset(self):
        """
        Filter notifications to only show user's notifications.
        """
        queryset = Notification.objects.filter(
            recipient=self.request.user
        ).select_related('sender', 'content_type').order_by('-created_at')
        
        # Filter by read status
        is_read = self.request.query_params.get('is_read', None)
        if is_read is not None:
            is_read_bool = is_read.lower() == 'true'
            queryset = queryset.filter(is_read=is_read_bool)
        
        # Filter by notification type
        notification_type = self.request.query_params.get('type', None)
        if notification_type:
            queryset = queryset.filter(notification_type=notification_type)
        
        return queryset

    def destroy(self, request, *args, **kwargs):
        """
        Delete a notification.
        """
        notification = self.get_object()
        
        # Ensure user can only delete their own notifications
        if notification.recipient != request.user:
            return Response(
                {'error': 'You can only delete your own notifications'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        notification.delete()
        return Response(
            {'status': 'notification deleted'},
            status=status.HTTP_204_NO_CONTENT
        )

    @action(detail=False, methods=['put'], url_path='read-all')
    def read_all(self, request):
        """
        Mark all notifications as read.
        """
        updated_count = Notification.objects.filter(
            recipient=request.user,
            is_read=False
        ).update(is_read=True)
        
        return Response({
            'status': 'all notifications marked as read',
            'updated_count': updated_count
        })
    
    @action(detail=False, methods=['put'], url_path='mark-all-read')
    def mark_all_read(self, request):
        """
        Alias for read_all - Mark all notifications as read.
        """
        return self.read_all(request)

    @action(detail=True, methods=['put'])
    def read(self, request, pk=None):
        """
        Mark a single notification as read.
        """
        notification = self.get_object()
        
        # Ensure user can only mark their own notifications as read
        if notification.recipient != request.user:
            return Response(
                {'error': 'You can only mark your own notifications as read'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        notification.is_read = True
        notification.save()
        
        serializer = self.get_serializer(notification)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='unread-count')
    def unread_count(self, request):
        """
        Get count of unread notifications.
        """
        count = Notification.objects.filter(
            recipient=request.user,
            is_read=False
        ).count()
        
        return Response({'unread_count': count})

    @action(detail=False, methods=['get'])
    def grouped(self, request):
        """
        Get grouped notifications.
        """
        # Get all notifications for the user
        notifications = self.get_queryset()
        
        # Limit to recent notifications for grouping
        limit = int(request.query_params.get('limit', 50))
        notifications = notifications[:limit]
        
        # Group notifications
        grouped = group_notifications(notifications)
        
        # Serialize
        serializer = GroupedNotificationSerializer(
            grouped, 
            many=True, 
            context={'request': request}
        )
        
        return Response(serializer.data)


class NotificationPreferenceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for NotificationPreference model.
    
    Endpoints:
    - GET /api/notifications/preferences/ - Get user preferences
    - PUT /api/notifications/preferences/{id}/ - Update preferences
    - PATCH /api/notifications/preferences/{id}/ - Partial update preferences
    - POST /api/notifications/preferences/add-fcm-token/ - Add FCM token
    - POST /api/notifications/preferences/remove-fcm-token/ - Remove FCM token
    """
    queryset = NotificationPreference.objects.all()
    serializer_class = NotificationPreferenceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Filter preferences to only show user's preferences.
        """
        return NotificationPreference.objects.filter(user=self.request.user)

    def get_object(self):
        """
        Get or create user's notification preferences.
        """
        obj, created = NotificationPreference.objects.get_or_create(
            user=self.request.user
        )
        return obj

    def list(self, request, *args, **kwargs):
        """
        Get user's notification preferences.
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], url_path='add-fcm-token')
    def add_fcm_token(self, request):
        """
        Add FCM token for push notifications.
        """
        token = request.data.get('token')
        
        if not token:
            return Response(
                {'error': 'Token is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        preferences = self.get_object()
        preferences.add_fcm_token(token)
        
        serializer = self.get_serializer(preferences)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], url_path='remove-fcm-token')
    def remove_fcm_token(self, request):
        """
        Remove FCM token.
        """
        token = request.data.get('token')
        
        if not token:
            return Response(
                {'error': 'Token is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        preferences = self.get_object()
        preferences.remove_fcm_token(token)
        
        serializer = self.get_serializer(preferences)
        return Response(serializer.data)

