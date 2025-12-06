"""
Views for the reels app.
"""

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes
from django.db.models import F
from .models import Reel, ReelComment, ReelLike
from .serializers import ReelSerializer, ReelCommentSerializer, ReelLikeSerializer
from .tasks import process_reel_upload

class ReelViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Reel model.
    """
    queryset = Reel.objects.all()
    serializer_class = ReelSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        reel = serializer.save(user=self.request.user)
        # Trigger background processing
        process_reel_upload.delay(reel.id)

    def list(self, request, *args, **kwargs):
        """
        Get reels feed (infinite scroll).
        For now, just return latest reels.
        """
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    @extend_schema(
        summary="Get trending reels",
        description="Get trending reels based on engagement (likes + comments + views).",
        responses={200: ReelSerializer(many=True)}
    )
    def trending(self, request):
        """
        Get trending reels based on engagement.
        """
        # Simple algorithm: likes + comments + views
        # Note: This is a heavy query for large datasets, should be cached or pre-calculated
        reels = Reel.objects.annotate(
            score=F('likes_count') + F('comments_count') + F('views_count')
        ).order_by('-score')[:20]
        
        serializer = self.get_serializer(reels, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    @extend_schema(
        summary="Like reel",
        description="Like a specific reel.",
        responses={200: OpenApiTypes.OBJECT}
    )
    def like(self, request, pk=None):
        """
        Like a reel.
        """
        reel = self.get_object()
        like, created = ReelLike.objects.get_or_create(reel=reel, user=request.user)
        
        if created:
            reel.likes_count += 1
            reel.save()
            return Response({'status': 'liked'})
        return Response({'status': 'already liked'})

    @action(detail=True, methods=['post'])
    @extend_schema(
        summary="Unlike reel",
        description="Unlike a specific reel.",
        responses={200: OpenApiTypes.OBJECT}
    )
    def unlike(self, request, pk=None):
        """
        Unlike a reel.
        """
        reel = self.get_object()
        deleted = ReelLike.objects.filter(reel=reel, user=request.user).delete()
        
        if deleted[0] > 0:
            reel.likes_count -= 1
            reel.save()
            return Response({'status': 'unliked'})
        return Response({'status': 'not liked'})

    @action(detail=True, methods=['post'])
    @extend_schema(
        summary="View reel",
        description="Increment the view count for a reel.",
        responses={200: OpenApiTypes.OBJECT}
    )
    def view(self, request, pk=None):
        """
        Increment view count.
        """
        reel = self.get_object()
        reel.views_count += 1
        reel.save()
        return Response({'status': 'viewed', 'views_count': reel.views_count})
