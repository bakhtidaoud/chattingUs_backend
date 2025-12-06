"""
Profile management views for users app.
"""

from rest_framework import status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from django.db.models import Q
from django.shortcuts import get_object_or_404

from .models import User, UserProfile, Follow, Block
from .serializers import (
    UserSerializer, PublicUserSerializer, UpdateProfileSerializer,
    ProfilePictureSerializer, FollowSerializer, BlockSerializer
)
from .profile_utils import compress_image


class ProfileManagementView(APIView):
    """
    Enhanced profile management view with GET and PUT.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get current user's full profile."""
        user = request.user
        serializer = UserSerializer(user)
        
        # Add additional profile stats
        data = serializer.data
        try:
            profile = user.profile
            data['followers_count'] = profile.followers_count
            data['following_count'] = profile.following_count
            data['posts_count'] = profile.posts_count
        except:
            data['followers_count'] = 0
            data['following_count'] = 0
            data['posts_count'] = 0
        
        return Response(data, status=status.HTTP_200_OK)
    
    def put(self, request):
        """Update user profile."""
        user = request.user
        serializer = UpdateProfileSerializer(
            user, 
            data=request.data, 
            partial=True,
            context={'request': request}
        )
        
        if serializer.is_valid():
            serializer.save()
            
            # Update privacy setting in UserProfile
            if 'is_private' in request.data:
                try:
                    profile = user.profile
                    profile.is_private = request.data['is_private']
                    profile.save()
                except:
                    pass
            
            return Response(UserSerializer(user).data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProfilePictureUploadView(APIView):
    """
    Upload and compress profile picture.
    """
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    def post(self, request):
        serializer = ProfilePictureSerializer(data=request.data)
        
        if serializer.is_valid():
            picture = serializer.validated_data['picture']
            
            # Compress the image
            try:
                compressed_picture = compress_image(picture, max_size=(800, 800), quality=85)
                
                # Save to user profile
                user = request.user
                user.profile_picture = compressed_picture
                user.save()
                
                return Response({
                    'message': 'Profile picture updated successfully.',
                    'profile_picture': request.build_absolute_uri(user.profile_picture.url) if user.profile_picture else None
                }, status=status.HTTP_200_OK)
            
            except Exception as e:
                return Response(
                    {'error': f'Failed to process image: {str(e)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PublicProfileView(APIView):
    """
    Get public profile by username.
    """
    permission_classes = [permissions.AllowAny]
    
    def get(self, request, username):
        user = get_object_or_404(User, username=username)
        
        # Check if user is blocked
        if request.user.is_authenticated:
            is_blocked_by_viewer = Block.objects.filter(
                blocker=request.user, blocked=user
            ).exists()
            is_blocking_viewer = Block.objects.filter(
                blocker=user, blocked=request.user
            ).exists()
            
            if is_blocked_by_viewer or is_blocking_viewer:
                return Response(
                    {'error': 'This profile is not available.'},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        serializer = PublicUserSerializer(user, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class UserSearchView(APIView):
    """
    Search users by username, first name, or last name.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        query = request.query_params.get('q', '').strip()
        
        if not query:
            return Response(
                {'error': 'Search query is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if len(query) < 2:
            return Response(
                {'error': 'Search query must be at least 2 characters.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get blocked users
        blocked_users = Block.objects.filter(
            Q(blocker=request.user) | Q(blocked=request.user)
        ).values_list('blocked_id', 'blocker_id')
        
        blocked_ids = set()
        for blocked_id, blocker_id in blocked_users:
            blocked_ids.add(blocked_id)
            blocked_ids.add(blocker_id)
        
        # Search users (exclude blocked and self)
        users = User.objects.filter(
            Q(username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query)
        ).exclude(
            id__in=blocked_ids
        ).exclude(
            id=request.user.id
        )[:20]  # Limit to 20 results
        
        serializer = PublicUserSerializer(users, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class FollowUserView(APIView):
    """
    Follow a user.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, user_id):
        user_to_follow = get_object_or_404(User, id=user_id)
        
        if request.user == user_to_follow:
            return Response(
                {'error': 'You cannot follow yourself.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if blocked
        is_blocked = Block.objects.filter(
            Q(blocker=request.user, blocked=user_to_follow) |
            Q(blocker=user_to_follow, blocked=request.user)
        ).exists()
        
        if is_blocked:
            return Response(
                {'error': 'Cannot follow this user.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Create follow relationship
        follow, created = Follow.objects.get_or_create(
            follower=request.user,
            following=user_to_follow
        )
        
        if created:
            # Update follower/following counts
            try:
                request.user.profile.following_count += 1
                request.user.profile.save()
                
                user_to_follow.profile.followers_count += 1
                user_to_follow.profile.save()
            except:
                pass
            
            return Response({
                'message': f'You are now following {user_to_follow.username}.',
                'status': 'following'
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'message': f'You are already following {user_to_follow.username}.',
            'status': 'already_following'
        }, status=status.HTTP_200_OK)


class UnfollowUserView(APIView):
    """
    Unfollow a user.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def delete(self, request, user_id):
        user_to_unfollow = get_object_or_404(User, id=user_id)
        
        deleted_count, _ = Follow.objects.filter(
            follower=request.user,
            following=user_to_unfollow
        ).delete()
        
        if deleted_count > 0:
            # Update follower/following counts
            try:
                request.user.profile.following_count = max(0, request.user.profile.following_count - 1)
                request.user.profile.save()
                
                user_to_unfollow.profile.followers_count = max(0, user_to_unfollow.profile.followers_count - 1)
                user_to_unfollow.profile.save()
            except:
                pass
            
            return Response({
                'message': f'You have unfollowed {user_to_unfollow.username}.',
                'status': 'unfollowed'
            }, status=status.HTTP_200_OK)
        
        return Response({
            'message': f'You are not following {user_to_unfollow.username}.',
            'status': 'not_following'
        }, status=status.HTTP_400_BAD_REQUEST)


class FollowersListView(APIView):
    """
    Get list of followers.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        followers = Follow.objects.filter(following=request.user).select_related('follower')
        users = [follow.follower for follow in followers]
        serializer = PublicUserSerializer(users, many=True, context={'request': request})
        
        return Response({
            'count': len(users),
            'followers': serializer.data
        }, status=status.HTTP_200_OK)


class FollowingListView(APIView):
    """
    Get list of users being followed.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        following = Follow.objects.filter(follower=request.user).select_related('following')
        users = [follow.following for follow in following]
        serializer = PublicUserSerializer(users, many=True, context={'request': request})
        
        return Response({
            'count': len(users),
            'following': serializer.data
        }, status=status.HTTP_200_OK)


class BlockUserView(APIView):
    """
    Block a user.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, user_id):
        user_to_block = get_object_or_404(User, id=user_id)
        
        if request.user == user_to_block:
            return Response(
                {'error': 'You cannot block yourself.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create block relationship
        block, created = Block.objects.get_or_create(
            blocker=request.user,
            blocked=user_to_block
        )
        
        if created:
            # Remove follow relationships
            Follow.objects.filter(
                Q(follower=request.user, following=user_to_block) |
                Q(follower=user_to_block, following=request.user)
            ).delete()
            
            return Response({
                'message': f'You have blocked {user_to_block.username}.',
                'status': 'blocked'
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'message': f'You have already blocked {user_to_block.username}.',
            'status': 'already_blocked'
        }, status=status.HTTP_200_OK)


class UnblockUserView(APIView):
    """
    Unblock a user.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def delete(self, request, user_id):
        user_to_unblock = get_object_or_404(User, id=user_id)
        
        deleted_count, _ = Block.objects.filter(
            blocker=request.user,
            blocked=user_to_unblock
        ).delete()
        
        if deleted_count > 0:
            return Response({
                'message': f'You have unblocked {user_to_unblock.username}.',
                'status': 'unblocked'
            }, status=status.HTTP_200_OK)
        
        return Response({
            'message': f'{user_to_unblock.username} is not blocked.',
            'status': 'not_blocked'
        }, status=status.HTTP_400_BAD_REQUEST)


class BlockedUsersListView(APIView):
    """
    Get list of blocked users.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        blocks = Block.objects.filter(blocker=request.user).select_related('blocked')
        users = [block.blocked for block in blocks]
        serializer = PublicUserSerializer(users, many=True, context={'request': request})
        
        return Response({
            'count': len(users),
            'blocked_users': serializer.data
        }, status=status.HTTP_200_OK)
