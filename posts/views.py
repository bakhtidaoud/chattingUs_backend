"""
Enhanced views for posts app with feed algorithm.
"""

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes
from django.db.models import Q
from django.shortcuts import get_object_or_404
import random

from .models import Post, Comment, Like
from .serializers import (
    PostSerializer, CreatePostSerializer, UpdatePostSerializer,
    CommentSerializer, LikeSerializer
)
from users.models import Follow, Block


class PostPagination(PageNumberPagination):
    """
    Pagination for posts feed.
    """
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class PostViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Post model with feed algorithm.
    """
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    pagination_class = PostPagination
    
    def get_queryset(self):
        """
        Get posts based on context.
        """
        user = self.request.user
        
        if self.action == 'list':
            # Feed algorithm
            if user.is_authenticated:
                # Get followed users
                following_ids = Follow.objects.filter(
                    follower=user
                ).values_list('following_id', flat=True)
                
                # Get blocked users
                blocked_ids = Block.objects.filter(
                    Q(blocker=user) | Q(blocked=user)
                ).values_list('blocked_id', 'blocker_id')
                
                blocked_user_ids = set()
                for blocked_id, blocker_id in blocked_ids:
                    blocked_user_ids.add(blocked_id)
                    blocked_user_ids.add(blocker_id)
                
                # Get posts from followed users (excluding blocked)
                followed_posts = Post.objects.filter(
                    user_id__in=following_ids,
                    is_archived=False
                ).exclude(
                    user_id__in=blocked_user_ids
                ).select_related('user')
                
                # Get suggested posts (random posts from non-followed, non-blocked users)
                suggested_posts = Post.objects.filter(
                    is_archived=False
                ).exclude(
                    user_id__in=list(following_ids) + [user.id]
                ).exclude(
                    user_id__in=blocked_user_ids
                ).select_related('user')[:10]
                
                # Combine and sort by recency
                all_posts = (followed_posts | suggested_posts).distinct().order_by('-created_at')
                
                return all_posts
            else:
                # Public feed for unauthenticated users
                return Post.objects.filter(
                    is_archived=False,
                    user__is_private=False
                ).select_related('user').order_by('-created_at')
        
        # For other actions, return all posts
        return Post.objects.filter(is_archived=False).select_related('user')
    
    def get_serializer_class(self):
        """
        Return appropriate serializer based on action.
        """
        if self.action == 'create':
            return CreatePostSerializer
        elif self.action in ['update', 'partial_update']:
            return UpdatePostSerializer
        return PostSerializer
    
    def perform_create(self, serializer):
        """
        Create post and update user's posts count.
        """
        post = serializer.save(user=self.request.user)
        
        # Update user's posts count
        try:
            profile = self.request.user.profile
            profile.posts_count += 1
            profile.save()
        except:
            pass
    
    def perform_destroy(self, instance):
        """
        Delete post and update user's posts count.
        """
        user = instance.user
        instance.delete()
        
        # Update user's posts count
        try:
            profile = user.profile
            profile.posts_count = max(0, profile.posts_count - 1)
            profile.save()
        except:
            pass
    
    @action(detail=True, methods=['post'])
    @extend_schema(
        summary="Like post",
        description="Like a specific post.",
        responses={201: OpenApiTypes.OBJECT, 200: OpenApiTypes.OBJECT}
    )
    def like(self, request, pk=None):
        """
        Like a post.
        """
        post = self.get_object()
        
        # Check if already liked
        like, created = Like.objects.get_or_create(
            user=request.user,
            post=post
        )
        
        if created:
            # Increment likes count
            post.likes_count += 1
            post.save()
            
            return Response({
                'message': 'Post liked successfully.',
                'likes_count': post.likes_count
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'message': 'You have already liked this post.',
            'likes_count': post.likes_count
        }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['delete'])
    @extend_schema(
        summary="Unlike post",
        description="Unlike a specific post.",
        responses={200: OpenApiTypes.OBJECT}
    )
    def unlike(self, request, pk=None):
        """
        Unlike a post.
        """
        post = self.get_object()
        
        deleted_count, _ = Like.objects.filter(
            user=request.user,
            post=post
        ).delete()
        
        if deleted_count > 0:
            # Decrement likes count
            post.likes_count = max(0, post.likes_count - 1)
            post.save()
            
            return Response({
                'message': 'Post unliked successfully.',
                'likes_count': post.likes_count
            }, status=status.HTTP_200_OK)
        
        return Response({
            'message': 'You have not liked this post.',
            'likes_count': post.likes_count
        }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    @extend_schema(
        summary="Get post likes",
        description="Get a list of users who liked the post.",
        responses={200: LikeSerializer(many=True)}
    )
    def likes(self, request, pk=None):
        """
        Get list of users who liked the post.
        """
        post = self.get_object()
        likes = Like.objects.filter(post=post).select_related('user')
        serializer = LikeSerializer(likes, many=True, context={'request': request})
        
        return Response({
            'count': likes.count(),
            'likes': serializer.data
        }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'])
    @extend_schema(
        summary="Archive post",
        description="Archive or unarchive a post.",
        responses={200: OpenApiTypes.OBJECT}
    )
    def archive(self, request, pk=None):
        """
        Archive/unarchive a post.
        """
        post = self.get_object()
        
        # Only post owner can archive
        if post.user != request.user:
            return Response({
                'error': 'You can only archive your own posts.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Toggle archive status
        post.is_archived = not post.is_archived
        post.save()
        
        status_text = 'archived' if post.is_archived else 'unarchived'
        
        return Response({
            'message': f'Post {status_text} successfully.',
            'is_archived': post.is_archived
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'])
    @extend_schema(
        summary="Get my posts",
        description="Get all posts created by the current user.",
        responses={200: PostSerializer(many=True)}
    )
    def my_posts(self, request):
        """
        Get current user's posts (including archived).
        """
        posts = Post.objects.filter(user=request.user).order_by('-created_at')
        
        page = self.paginate_queryset(posts)
        if page is not None:
            serializer = PostSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = PostSerializer(posts, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    @extend_schema(
        summary="Get archived posts",
        description="Get all archived posts of the current user.",
        responses={200: PostSerializer(many=True)}
    )
    def archived(self, request):
        """
        Get current user's archived posts.
        """
        posts = Post.objects.filter(
            user=request.user,
            is_archived=True
        ).order_by('-created_at')
        
        serializer = PostSerializer(posts, many=True, context={'request': request})
        return Response({
            'count': posts.count(),
            'posts': serializer.data
        }, status=status.HTTP_200_OK)
    

