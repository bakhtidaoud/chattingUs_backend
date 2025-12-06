from rest_framework import viewsets, permissions, status, decorators
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes
from django.utils import timezone
from .models import Story, StoryView, StoryHighlight, StoryReply
from .serializers import StorySerializer, StoryViewSerializer, StoryHighlightSerializer, StoryReplySerializer
from users.models import User

class StoryViewSet(viewsets.ModelViewSet):
    queryset = Story.objects.all()
    serializer_class = StorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Return active stories from followed users and self.
        """
        user = self.request.user
        now = timezone.now()
        # Assuming 'following' is the relation name for followed users
        # If not, adjust based on User model
        following_users = user.following.all()
        return Story.objects.filter(
            user__in=[user] + list(following_users),
            expires_at__gt=now
        ).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @decorators.action(detail=True, methods=['post'])
    @extend_schema(
        summary="View story",
        description="Mark a story as viewed by the current user.",
        responses={200: OpenApiTypes.OBJECT}
    )
    def view(self, request, pk=None):
        story = self.get_object()
        if not StoryView.objects.filter(story=story, user=request.user).exists():
            StoryView.objects.create(story=story, user=request.user)
            story.views_count += 1
            story.save()
        return Response({'status': 'viewed'})

    @decorators.action(detail=True, methods=['get'])
    @extend_schema(
        summary="Get story viewers",
        description="Get a list of users who viewed the story.",
        responses={200: StoryViewSerializer(many=True)}
    )
    def viewers(self, request, pk=None):
        story = self.get_object()
        if story.user != request.user:
            return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)
        views = StoryView.objects.filter(story=story)
        serializer = StoryViewSerializer(views, many=True)
        return Response(serializer.data)

    @decorators.action(detail=False, methods=['get'], url_path='user/(?P<user_id>[^/.]+)')
    @extend_schema(
        summary="Get user stories",
        description="Get active stories for a specific user.",
        responses={200: StorySerializer(many=True)}
    )
    def user_stories(self, request, user_id=None):
        now = timezone.now()
        stories = Story.objects.filter(user_id=user_id, expires_at__gt=now)
        serializer = self.get_serializer(stories, many=True)
        return Response(serializer.data)

class StoryHighlightViewSet(viewsets.ModelViewSet):
    queryset = StoryHighlight.objects.all()
    serializer_class = StoryHighlightSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_queryset(self):
        return StoryHighlight.objects.filter(user=self.request.user)

class StoryReplyViewSet(viewsets.ModelViewSet):
    queryset = StoryReply.objects.all()
    serializer_class = StoryReplySerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
