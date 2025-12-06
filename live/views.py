"""
Views for live streaming functionality.
"""

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from .models import LiveStream, LiveViewer, LiveComment, LiveReaction
from .serializers import (
    LiveStreamSerializer,
    LiveStreamCreateSerializer,
    LiveViewerSerializer,
    LiveCommentSerializer,
    LiveReactionSerializer
)


class LiveStreamViewSet(viewsets.ModelViewSet):
    """
    ViewSet for LiveStream model.
    
    Endpoints:
    - GET /api/live/streams/ - List active live streams
    - POST /api/live/streams/ - Start a new live stream
    - GET /api/live/streams/{id}/ - Get stream details
    - PUT /api/live/streams/{id}/ - Update stream (owner only)
    - DELETE /api/live/streams/{id}/ - Delete stream (owner only)
    - POST /api/live/streams/{id}/start/ - Start the stream
    - POST /api/live/streams/{id}/end/ - End the stream
    - POST /api/live/streams/{id}/join/ - Join as viewer
    - POST /api/live/streams/{id}/leave/ - Leave stream
    - GET /api/live/streams/{id}/viewers/ - Get current viewers
    - POST /api/live/streams/{id}/comments/ - Post a comment
    - GET /api/live/streams/{id}/comments/ - Get comments
    - POST /api/live/streams/{id}/reactions/ - Send a reaction
    """
    queryset = LiveStream.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        """Return appropriate serializer class."""
        if self.action == 'create':
            return LiveStreamCreateSerializer
        return LiveStreamSerializer
    
    def get_queryset(self):
        """
        Filter streams based on query parameters.
        """
        queryset = LiveStream.objects.select_related('streamer').all()
        
        # Filter by status
        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        else:
            # By default, show only live and waiting streams
            queryset = queryset.filter(status__in=['live', 'waiting'])
        
        # Filter by streamer
        streamer_id = self.request.query_params.get('streamer', None)
        if streamer_id:
            queryset = queryset.filter(streamer_id=streamer_id)
        
        # Show user's own streams
        my_streams = self.request.query_params.get('my_streams', None)
        if my_streams:
            queryset = queryset.filter(streamer=self.request.user)
        
        return queryset.order_by('-created_at')
    
    def perform_create(self, serializer):
        """Create a new live stream."""
        # Check if user already has an active stream
        active_stream = LiveStream.objects.filter(
            streamer=self.request.user,
            status__in=['live', 'waiting']
        ).first()
        
        if active_stream:
            raise serializers.ValidationError(
                "You already have an active live stream. Please end it before starting a new one."
            )
        
        serializer.save(streamer=self.request.user)
    
    def perform_destroy(self, instance):
        """Only allow owner to delete stream."""
        if instance.streamer != self.request.user:
            raise permissions.PermissionDenied("You can only delete your own streams.")
        instance.delete()
    
    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        """
        Start the live stream.
        """
        stream = self.get_object()
        
        # Only owner can start
        if stream.streamer != request.user:
            return Response(
                {'error': 'Only the stream owner can start the stream'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if stream.status != 'waiting':
            return Response(
                {'error': 'Stream is already started or ended'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        stream.start_stream()
        serializer = self.get_serializer(stream)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def end(self, request, pk=None):
        """
        End the live stream.
        """
        stream = self.get_object()
        
        # Only owner can end
        if stream.streamer != request.user:
            return Response(
                {'error': 'Only the stream owner can end the stream'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if stream.status != 'live':
            return Response(
                {'error': 'Stream is not live'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        stream.end_stream()
        serializer = self.get_serializer(stream)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def join(self, request, pk=None):
        """
        Join a live stream as a viewer.
        """
        stream = self.get_object()
        
        if stream.status != 'live':
            return Response(
                {'error': 'Stream is not live'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create or update viewer
        viewer, created = LiveViewer.objects.get_or_create(
            stream=stream,
            user=request.user,
            defaults={'is_active': True}
        )
        
        if not created and not viewer.is_active:
            viewer.is_active = True
            viewer.save()
        
        # Update viewer count
        stream.update_viewer_count()
        
        serializer = LiveViewerSerializer(viewer)
        return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'])
    def leave(self, request, pk=None):
        """
        Leave a live stream.
        """
        stream = self.get_object()
        
        try:
            viewer = LiveViewer.objects.get(stream=stream, user=request.user)
            viewer.leave()
            
            # Update viewer count
            stream.update_viewer_count()
            
            return Response({'status': 'left stream'})
        except LiveViewer.DoesNotExist:
            return Response(
                {'error': 'You are not viewing this stream'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['get'])
    def viewers(self, request, pk=None):
        """
        Get current viewers of the stream.
        """
        stream = self.get_object()
        viewers = stream.viewers.filter(is_active=True).select_related('user')
        serializer = LiveViewerSerializer(viewers, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get', 'post'])
    def comments(self, request, pk=None):
        """
        Get or post comments for the stream.
        """
        stream = self.get_object()
        
        if request.method == 'GET':
            # Get recent comments
            limit = int(request.query_params.get('limit', 50))
            comments = stream.comments.select_related('user').order_by('-created_at')[:limit]
            serializer = LiveCommentSerializer(comments, many=True)
            return Response(serializer.data)
        
        elif request.method == 'POST':
            # Post a new comment
            serializer = LiveCommentSerializer(data=request.data, context={'request': request})
            if serializer.is_valid():
                serializer.save(stream=stream)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def reactions(self, request, pk=None):
        """
        Send a reaction to the stream.
        """
        stream = self.get_object()
        
        serializer = LiveReactionSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save(stream=stream)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
