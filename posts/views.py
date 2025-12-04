"""
Views for the posts app.
"""

from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Post, Comment, Like
from .serializers import PostSerializer, CommentSerializer, LikeSerializer


class PostViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Post model.
    """
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        """
        Like a post.
        """
        post = self.get_object()
        like, created = Like.objects.get_or_create(post=post, user=request.user)
        
        if created:
            post.likes_count += 1
            post.save()
            return Response({'status': 'liked'})
        return Response({'status': 'already liked'})

    @action(detail=True, methods=['post'])
    def unlike(self, request, pk=None):
        """
        Unlike a post.
        """
        post = self.get_object()
        deleted = Like.objects.filter(post=post, user=request.user).delete()
        
        if deleted[0] > 0:
            post.likes_count -= 1
            post.save()
            return Response({'status': 'unliked'})
        return Response({'status': 'not liked'})
