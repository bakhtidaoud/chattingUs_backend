"""
Views for comment management.
"""

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404

from .models import Post, Comment, CommentLike
from .serializers import CommentSerializer, CreateCommentSerializer, CommentLikeSerializer
from .utils import extract_mentions, create_comment_notification


class CommentPagination(PageNumberPagination):
    """
    Pagination for comments.
    """
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class CommentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Comment model with nested replies.
    """
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    pagination_class = CommentPagination
    
    def get_queryset(self):
        """Get comments for a specific post (top-level only)."""
        post_pk = self.kwargs.get('post_pk')  # Changed from post_id
        if post_pk:
            # Only get top-level comments (no parent)
            return Comment.objects.filter(
                post_id=post_pk,
                parent_comment__isnull=True
            ).select_related('user').prefetch_related('replies__user')
        return Comment.objects.none()
    
    def get_serializer_class(self):
        if self.action == 'create':
            return CreateCommentSerializer
        return CommentSerializer
    
    def create(self, request, post_pk=None):  # Changed from post_id
        """Create a comment on a post."""
        post = get_object_or_404(Post, id=post_pk)
        
        serializer = CreateCommentSerializer(
            data=request.data,
            context={'request': request, 'post': post}
        )
        
        if serializer.is_valid():
            # Save comment
            comment = serializer.save(user=request.user, post=post)
            
            # Update post's comments count (only for top-level comments)
            if not comment.parent_comment:
                post.comments_count += 1
                post.save()
            
            # Extract mentions and create notifications
            mentioned_users = extract_mentions(comment.text)
            create_comment_notification(comment, mentioned_users)
            
            # Return full comment data
            response_serializer = CommentSerializer(comment, context={'request': request})
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def update(self, request, pk=None, post_pk=None):  # Changed from post_id
        """Update a comment."""
        comment = self.get_object()
        
        # Only comment owner can edit
        if comment.user != request.user:
            return Response(
                {'error': 'You can only edit your own comments.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Only allow editing text
        comment.text = request.data.get('text', comment.text)
        comment.save()
        
        serializer = CommentSerializer(comment, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def destroy(self, request, pk=None, post_pk=None):  # Changed from post_id
        """Delete a comment."""
        comment = self.get_object()
        
        # Only comment owner can delete
        if comment.user != request.user:
            return Response(
                {'error': 'You can only delete your own comments.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        post = comment.post
        
        # Update post's comments count (only for top-level comments)
        if not comment.parent_comment:
            post.comments_count = max(0, post.comments_count - 1)
            post.save()
        
        comment.delete()
        
        return Response(
            {'message': 'Comment deleted successfully.'},
            status=status.HTTP_204_NO_CONTENT
        )
    
    @action(detail=True, methods=['post'])
    def like(self, request, pk=None, post_pk=None):  # Changed from post_id
        """Like a comment."""
        comment = self.get_object()
        
        # Create like
        like, created = CommentLike.objects.get_or_create(
            user=request.user,
            comment=comment
        )
        
        if created:
            # Increment likes count
            comment.likes_count += 1
            comment.save()
            
            return Response({
                'message': 'Comment liked successfully.',
                'likes_count': comment.likes_count
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'message': 'You have already liked this comment.',
            'likes_count': comment.likes_count
        }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['delete'])
    def unlike(self, request, pk=None, post_pk=None):  # Changed from post_id
        """Unlike a comment."""
        comment = self.get_object()
        
        deleted_count, _ = CommentLike.objects.filter(
            user=request.user,
            comment=comment
        ).delete()
        
        if deleted_count > 0:
            # Decrement likes count
            comment.likes_count = max(0, comment.likes_count - 1)
            comment.save()
            
            return Response({
                'message': 'Comment unliked successfully.',
                'likes_count': comment.likes_count
            }, status=status.HTTP_200_OK)
        
        return Response({
            'message': 'You have not liked this comment.',
            'likes_count': comment.likes_count
        }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def reply(self, request, pk=None, post_pk=None):  # Changed from post_id
        """Reply to a comment."""
        parent_comment = self.get_object()
        post = parent_comment.post
        
        # Check nesting level
        if parent_comment.reply_level >= 2:
            return Response(
                {'error': 'Maximum reply depth (2 levels) exceeded.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = CreateCommentSerializer(
            data={'text': request.data.get('text'), 'parent_comment': parent_comment.id},
            context={'request': request, 'post': post}
        )
        
        if serializer.is_valid():
            # Save reply
            reply = serializer.save(user=request.user, post=post)
            
            # Extract mentions and create notifications
            mentioned_users = extract_mentions(reply.text)
            create_comment_notification(reply, mentioned_users)
            
            # Return full reply data
            response_serializer = CommentSerializer(reply, context={'request': request})
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def likes(self, request, pk=None, post_pk=None):  # Changed from post_id
        """Get users who liked the comment."""
        comment = self.get_object()
        likes = CommentLike.objects.filter(comment=comment).select_related('user')
        serializer = CommentLikeSerializer(likes, many=True, context={'request': request})
        
        return Response({
            'count': likes.count(),
            'likes': serializer.data
        }, status=status.HTTP_200_OK)
