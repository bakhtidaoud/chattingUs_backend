"""
Views for the users app.
"""

from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import User, UserProfile, Follow
from .serializers import UserSerializer, UserProfileSerializer, FollowSerializer


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for User model.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    @action(detail=True, methods=['post'])
    def follow(self, request, pk=None):
        """
        Follow a user.
        """
        user_to_follow = self.get_object()
        if request.user == user_to_follow:
            return Response({'error': 'You cannot follow yourself'}, status=400)
        
        follow, created = Follow.objects.get_or_create(
            follower=request.user,
            following=user_to_follow
        )
        
        if created:
            return Response({'status': 'following'})
        return Response({'status': 'already following'})

    @action(detail=True, methods=['post'])
    def unfollow(self, request, pk=None):
        """
        Unfollow a user.
        """
        user_to_unfollow = self.get_object()
        Follow.objects.filter(
            follower=request.user,
            following=user_to_unfollow
        ).delete()
        
        return Response({'status': 'unfollowed'})
