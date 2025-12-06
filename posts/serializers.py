"""
Enhanced serializers for posts app.
"""

from rest_framework import serializers
from .models import Post, Comment, Like, CommentLike
from users.serializers import PublicUserSerializer


class PostSerializer(serializers.ModelSerializer):
    """
    Serializer for Post model with user details.
    """
    user = PublicUserSerializer(read_only=True)
    is_liked = serializers.SerializerMethodField()
    
    class Meta:
        model = Post
        fields = ['id', 'user', 'image', 'caption', 'location', 'likes_count', 
                  'comments_count', 'shares_count', 'is_archived', 'is_liked',
                  'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'likes_count', 'comments_count', 
                           'shares_count', 'created_at', 'updated_at']
    
    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Like.objects.filter(user=request.user, post=obj).exists()
        return False


class CreatePostSerializer(serializers.ModelSerializer):
    """
    Serializer for creating posts.
    """
    image = serializers.ImageField(required=False, allow_null=True)
    
    class Meta:
        model = Post
        fields = ['id', 'image', 'caption', 'location']
        read_only_fields = ['id']
    
    def validate_image(self, value):
        if not value:
            return value
            
        # Validate file size (max 10MB)
        if value.size > 10 * 1024 * 1024:
            raise serializers.ValidationError("Image file size cannot exceed 10MB.")
        
        # Validate file type
        allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp']
        if value.content_type not in allowed_types:
            raise serializers.ValidationError("Only JPEG, PNG, and WebP images are allowed.")
        
        return value


class UpdatePostSerializer(serializers.ModelSerializer):
    """
    Serializer for updating posts.
    """
    class Meta:
        model = Post
        fields = ['caption', 'location']


class CommentSerializer(serializers.ModelSerializer):
    """
    Serializer for Comment model with nested replies.
    """
    user = PublicUserSerializer(read_only=True)
    replies = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    reply_level = serializers.ReadOnlyField()
    
    class Meta:
        model = Comment
        fields = ['id', 'user', 'post', 'text', 'parent_comment', 'likes_count',
                  'replies', 'is_liked', 'reply_level', 'created_at']
        read_only_fields = ['id', 'user', 'likes_count', 'created_at']
    
    def get_replies(self, obj):
        """Get nested replies (only 1 level deep to avoid recursion)."""
        if obj.parent_comment is None:  # Only show replies for top-level comments
            replies = obj.replies.all()[:5]  # Limit to 5 replies
            return CommentSerializer(replies, many=True, context=self.context).data
        return []
    
    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            from .models import CommentLike
            return CommentLike.objects.filter(user=request.user, comment=obj).exists()
        return False


class CreateCommentSerializer(serializers.ModelSerializer):
    """
    Serializer for creating comments.
    """
    class Meta:
        model = Comment
        fields = ['text', 'parent_comment']
    
    def validate_text(self, value):
        if not value.strip():
            raise serializers.ValidationError("Comment text cannot be empty.")
        return value
    
    def validate_parent_comment(self, value):
        if value:
            # Check nesting level (max 2 levels)
            if value.reply_level >= 2:
                raise serializers.ValidationError("Maximum reply depth (2 levels) exceeded.")
        return value
    
    def validate(self, attrs):
        # Ensure parent comment belongs to the same post
        parent_comment = attrs.get('parent_comment')
        post = self.context.get('post')
        
        if parent_comment and parent_comment.post != post:
            raise serializers.ValidationError("Parent comment must belong to the same post.")
        
        return attrs


class CommentLikeSerializer(serializers.ModelSerializer):
    """
    Serializer for CommentLike model.
    """
    user = PublicUserSerializer(read_only=True)
    
    class Meta:
        model = CommentLike
        fields = ['id', 'user', 'comment', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']


class LikeSerializer(serializers.ModelSerializer):
    """
    Serializer for Like model.
    """
    user = PublicUserSerializer(read_only=True)
    
    class Meta:
        model = Like
        fields = ['id', 'user', 'post', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']
