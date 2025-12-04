"""
Views for the stories app.
"""

from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from datetime import timedelta
from .models import Story, StoryView
from .serializers import StorySerializer, StoryViewSerializer


class StoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Story model.
    """
    queryset = Story.objects.filter(expires_at__gt=timezone.now())
    serializer_class = StorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        # Stories expire after 24 hours
        expires_at = timezone.now() + timedelta(hours=24)
        serializer.save(user=self.request.user, expires_at=expires_at)

    @action(detail=True, methods=['post'])
    def view(self, request, pk=None):
        """
        Mark a story as viewed.
        """
        story = self.get_object()
        view, created = StoryView.objects.get_or_create(story=story, user=request.user)
        
        if created:
            story.views_count += 1
            story.save()
            return Response({'status': 'viewed'})
        return Response({'status': 'already viewed'})
