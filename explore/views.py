from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q, F
from django.contrib.auth import get_user_model
from posts.models import Post
from reels.models import Reel
from posts.serializers import PostSerializer
from reels.serializers import ReelSerializer
from users.serializers import UserSerializer
from .models import Hashtag, SearchHistory
from .serializers import HashtagSerializer, SearchHistorySerializer
from .utils import extract_hashtags

User = get_user_model()

class ExploreViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def list(self, request):
        """
        Get explore feed (mix of posts and reels).
        """
        # Simple algorithm: random posts/reels from non-followed users
        # In a real app, this would be much more complex
        posts = Post.objects.all().order_by('?')[:10]
        reels = Reel.objects.all().order_by('?')[:10]
        
        post_serializer = PostSerializer(posts, many=True, context={'request': request})
        reel_serializer = ReelSerializer(reels, many=True, context={'request': request})
        
        # Interleave results
        feed = []
        for p, r in zip(post_serializer.data, reel_serializer.data):
            p['type'] = 'post'
            r['type'] = 'reel'
            feed.extend([p, r])
            
        # Add remaining if any (though zip truncates to shortest)
        
        return Response(feed)

    @action(detail=False, methods=['get'])
    def search(self, request):
        """
        Search for users, posts, reels, hashtags.
        
        Query Parameters:
        - q: Search query (required)
        - type: Search type - 'all', 'users', 'posts', 'reels', 'hashtags' (default: 'all')
        - limit: Number of results per type (default: 10, max: 50)
        
        Example: /api/explore/search/?q=test&type=users&limit=20
        """
        query = request.query_params.get('q', '').strip()
        search_type = request.query_params.get('type', 'all')
        
        # Get limit parameter with validation
        try:
            limit = int(request.query_params.get('limit', 10))
            limit = min(max(limit, 1), 50)  # Clamp between 1 and 50
        except ValueError:
            limit = 10
        
        if not query:
            return Response({
                'users': [],
                'posts': [],
                'reels': [],
                'hashtags': []
            })
            
        # Save search history if authenticated
        if request.user.is_authenticated:
            SearchHistory.objects.create(user=request.user, query=query)
            
        results = {}
        
        if search_type in ['all', 'users']:
            # Search in username, first_name, last_name, and bio
            users = User.objects.filter(
                Q(username__icontains=query) | 
                Q(first_name__icontains=query) |
                Q(last_name__icontains=query) |
                Q(bio__icontains=query)
            ).distinct().order_by('-is_verified', '-created_at')[:limit]
            results['users'] = UserSerializer(users, many=True, context={'request': request}).data
            
        if search_type in ['all', 'posts']:
            # Search in caption and location
            posts = Post.objects.filter(
                Q(caption__icontains=query) | 
                Q(location__icontains=query)
            ).select_related('user').order_by('-created_at')[:limit]
            results['posts'] = PostSerializer(posts, many=True, context={'request': request}).data
            
        if search_type in ['all', 'reels']:
            # Search in caption
            reels = Reel.objects.filter(
                caption__icontains=query
            ).select_related('user').order_by('-created_at')[:limit]
            results['reels'] = ReelSerializer(reels, many=True, context={'request': request}).data
            
        if search_type in ['all', 'hashtags']:
            hashtags = Hashtag.objects.filter(
                name__icontains=query
            ).order_by('-posts_count', '-reels_count')[:limit]
            results['hashtags'] = HashtagSerializer(hashtags, many=True).data
            
        return Response(results)

    @action(detail=False, methods=['get'])
    def trending(self, request):
        """
        Get trending content.
        """
        # Trending hashtags
        hashtags = Hashtag.objects.annotate(
            total_count=F('posts_count') + F('reels_count')
        ).order_by('-total_count')[:5]
        
        # Trending posts (likes + comments)
        posts = Post.objects.annotate(
            score=F('likes_count') + F('comments_count')
        ).order_by('-score')[:5]
        
        # Trending reels (likes + views)
        reels = Reel.objects.annotate(
            score=F('likes_count') + F('views_count')
        ).order_by('-score')[:5]
        
        return Response({
            'hashtags': HashtagSerializer(hashtags, many=True).data,
            'posts': PostSerializer(posts, many=True, context={'request': request}).data,
            'reels': ReelSerializer(reels, many=True, context={'request': request}).data
        })

class HashtagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Hashtag.objects.all()
    serializer_class = HashtagSerializer
    lookup_field = 'name'
    
    @action(detail=True, methods=['get'])
    def posts(self, request, name=None):
        hashtag = self.get_object()
        # Find posts containing this hashtag
        # Note: This is a simple text search, ideally we'd have a ManyToMany relation
        posts = Post.objects.filter(caption__icontains=f"#{name}")
        serializer = PostSerializer(posts, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def reels(self, request, name=None):
        hashtag = self.get_object()
        reels = Reel.objects.filter(caption__icontains=f"#{name}")
        serializer = ReelSerializer(reels, many=True, context={'request': request})
        return Response(serializer.data)
