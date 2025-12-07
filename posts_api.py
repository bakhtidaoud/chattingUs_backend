"""
Posts API for Admin Dashboard
Provides real post data from the database
"""

from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.core.paginator import Paginator


@api_view(['GET'])
@authentication_classes([])
@permission_classes([AllowAny])
def posts_list(request):
    """
    Get list of posts from database
    """
    try:
        from posts.models import Post
        
        # Get query parameters
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 20))
        search = request.GET.get('search', '')
        
        # Get all posts
        posts = Post.objects.all().order_by('-created_at')
        
        # Apply search filter if provided
        if search:
            from django.db.models import Q
            posts = posts.filter(
                Q(caption__icontains=search) |
                Q(user__username__icontains=search)
            )
        
        # Paginate
        paginator = Paginator(posts, page_size)
        page_obj = paginator.get_page(page)
        
        # Serialize posts
        posts_data = []
        for post in page_obj:
            # Build absolute URL for image
            image_url = None
            if post.image:
                image_url = request.build_absolute_uri(post.image.url)
            
            # Build absolute URL for user profile picture
            profile_picture_url = None
            if hasattr(post.user, 'profile_picture') and post.user.profile_picture:
                profile_picture_url = request.build_absolute_uri(post.user.profile_picture.url)
            
            posts_data.append({
                'id': post.id,
                'user': {
                    'id': post.user.id,
                    'username': post.user.username,
                    'email': post.user.email,
                    'profile_picture': profile_picture_url,
                },
                'image': image_url,
                'caption': post.caption or '',
                'location': post.location or '',
                'created_at': post.created_at.isoformat(),
                'updated_at': post.updated_at.isoformat() if hasattr(post, 'updated_at') else None,
                'likes_count': post.likes_count if hasattr(post, 'likes_count') else (post.likes.count() if hasattr(post, 'likes') else 0),
                'comments_count': post.comments_count if hasattr(post, 'comments_count') else (post.comments.count() if hasattr(post, 'comments') else 0),
                'shares_count': post.shares_count if hasattr(post, 'shares_count') else 0,
                'is_archived': post.is_archived if hasattr(post, 'is_archived') else False,
            })
        
        return Response({
            'count': paginator.count,
            'next': page_obj.has_next(),
            'previous': page_obj.has_previous(),
            'results': posts_data,
            'total_pages': paginator.num_pages,
            'current_page': page
        })
    
    except ImportError:
        # Posts model doesn't exist, return empty list
        return Response({
            'count': 0,
            'next': False,
            'previous': False,
            'results': [],
            'total_pages': 0,
            'current_page': 1
        })


@api_view(['GET'])
@authentication_classes([])
@permission_classes([AllowAny])
def post_detail(request, pk):
    """
    Get single post details with comments
    """
    try:
        from posts.models import Post
        
        try:
            post = Post.objects.get(pk=pk)
        except Post.DoesNotExist:
            return Response({'error': 'Post not found'}, status=404)
        
        # Get comments if they exist
        comments_data = []
        if hasattr(post, 'comments'):
            comments = post.comments.all().order_by('-created_at')[:10]  # Get latest 10 comments
            for comment in comments:
                comments_data.append({
                    'id': comment.id,
                    'user': {
                        'id': comment.user.id,
                        'username': comment.user.username,
                    },
                    'text': comment.text if hasattr(comment, 'text') else comment.content if hasattr(comment, 'content') else '',
                    'created_at': comment.created_at.isoformat(),
                })
        
        # Build absolute URL for image
        image_url = None
        if post.image:
            image_url = request.build_absolute_uri(post.image.url)
        
        # Build absolute URL for user profile picture
        profile_picture_url = None
        if hasattr(post.user, 'profile_picture') and post.user.profile_picture:
            profile_picture_url = request.build_absolute_uri(post.user.profile_picture.url)
        
        return Response({
            'id': post.id,
            'user': {
                'id': post.user.id,
                'username': post.user.username,
                'email': post.user.email,
                'profile_picture': profile_picture_url,
            },
            'image': image_url,
            'caption': post.caption or '',
            'location': post.location or '',
            'created_at': post.created_at.isoformat(),
            'updated_at': post.updated_at.isoformat() if hasattr(post, 'updated_at') else None,
            'likes_count': post.likes_count if hasattr(post, 'likes_count') else (post.likes.count() if hasattr(post, 'likes') else 0),
            'comments_count': post.comments_count if hasattr(post, 'comments_count') else (post.comments.count() if hasattr(post, 'comments') else 0),
            'shares_count': post.shares_count if hasattr(post, 'shares_count') else 0,
            'is_archived': post.is_archived if hasattr(post, 'is_archived') else False,
            'comments': comments_data,
        })
    
    except ImportError:
        return Response({'error': 'Posts model not found'}, status=404)
