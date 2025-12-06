"""
Views for the mediafiles app.
"""

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.db.models import Q
from .models import Media
from .serializers import MediaUploadSerializer, MediaSerializer, MediaListSerializer
from .tasks import process_media_task
import logging

logger = logging.getLogger(__name__)


class MediaViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Media model.
    
    Endpoints:
    - POST /api/media/upload/ - Upload media file
    - GET /api/media/ - List user's media files
    - GET /api/media/{id}/ - Get media details
    - DELETE /api/media/{id}/ - Delete media file
    """
    queryset = Media.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    def get_serializer_class(self):
        """
        Return appropriate serializer based on action.
        """
        if self.action == 'upload':
            return MediaUploadSerializer
        elif self.action == 'list':
            return MediaListSerializer
        return MediaSerializer
    
    def get_queryset(self):
        """
        Filter media to only show user's files.
        """
        queryset = Media.objects.filter(user=self.request.user)
        
        # Filter by file type
        file_type = self.request.query_params.get('type', None)
        if file_type in ['image', 'video', 'audio']:
            queryset = queryset.filter(file_type=file_type)
        
        # Filter by status
        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset.order_by('-created_at')
    
    @action(detail=False, methods=['post'])
    def upload(self, request):
        """
        Upload a media file.
        
        Request:
            - file: The media file to upload
        
        Response:
            - Media object with processing status
        """
        serializer = MediaUploadSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            # Save media instance
            media = serializer.save()
            
            # Trigger async processing
            try:
                process_media_task.delay(media.id)
                logger.info(f"Triggered processing for media {media.id}")
            except Exception as e:
                logger.error(f"Error triggering processing task: {e}")
                # Processing will still happen, just not async
                media.status = 'failed'
                media.metadata['error'] = 'Could not trigger async processing'
                media.save()
            
            # Return media details
            response_serializer = MediaSerializer(media, context={'request': request})
            return Response(
                response_serializer.data,
                status=status.HTTP_201_CREATED
            )
        
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )
    
    def retrieve(self, request, *args, **kwargs):
        """
        Get media details.
        """
        media = self.get_object()
        
        # Check permissions
        if media.user != request.user and not media.is_public:
            return Response(
                {'error': 'You do not have permission to access this media'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = self.get_serializer(media)
        return Response(serializer.data)
    
    def destroy(self, request, *args, **kwargs):
        """
        Delete media file.
        """
        media = self.get_object()
        
        # Check permissions
        if media.user != request.user:
            return Response(
                {'error': 'You can only delete your own media'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Delete media (this will also delete files via model's delete method)
        media.delete()
        
        return Response(
            {'status': 'media deleted'},
            status=status.HTTP_204_NO_CONTENT
        )
    
    @action(detail=True, methods=['post'])
    def reprocess(self, request, pk=None):
        """
        Reprocess a failed media file.
        """
        media = self.get_object()
        
        # Check permissions
        if media.user != request.user:
            return Response(
                {'error': 'You can only reprocess your own media'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Only reprocess failed media
        if media.status != 'failed':
            return Response(
                {'error': 'Only failed media can be reprocessed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Reset status and trigger processing
        media.status = 'uploading'
        media.metadata.pop('error', None)
        media.save()
        
        try:
            process_media_task.delay(media.id)
            logger.info(f"Triggered reprocessing for media {media.id}")
        except Exception as e:
            logger.error(f"Error triggering reprocessing task: {e}")
            return Response(
                {'error': 'Could not trigger reprocessing'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        serializer = self.get_serializer(media)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        Get media statistics for the user.
        """
        user_media = Media.objects.filter(user=request.user)
        
        stats = {
            'total': user_media.count(),
            'by_type': {
                'image': user_media.filter(file_type='image').count(),
                'video': user_media.filter(file_type='video').count(),
                'audio': user_media.filter(file_type='audio').count(),
            },
            'by_status': {
                'ready': user_media.filter(status='ready').count(),
                'processing': user_media.filter(status='processing').count(),
                'failed': user_media.filter(status='failed').count(),
                'uploading': user_media.filter(status='uploading').count(),
            },
            'total_size': sum(m.file_size for m in user_media),
        }
        
        return Response(stats)
