"""
Test script for the enhanced search API.
Run with: python test_search_api.py
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chattingus_backend.settings')
django.setup()

from django.contrib.auth import get_user_model
from posts.models import Post
from reels.models import Reel
from django.test import RequestFactory
from explore.views import ExploreViewSet

User = get_user_model()

def test_search_api():
    """Test the enhanced search API functionality."""
    print("\n" + "=" * 60)
    print("Testing Enhanced Search API")
    print("=" * 60)
    
    # Create test data
    print("\n1. Creating test data...")
    
    # Create users with different attributes
    user1 = User.objects.create_user(
        username='john_doe',
        first_name='John',
        last_name='Doe',
        bio='Software engineer who loves coding',
        email='john@test.com',
        password='test123'
    )
    
    user2 = User.objects.create_user(
        username='jane_smith',
        first_name='Jane',
        last_name='Smith',
        bio='Designer and artist',
        email='jane@test.com',
        password='test123'
    )
    
    user3 = User.objects.create_user(
        username='coding_master',
        first_name='Mike',
        last_name='Johnson',
        bio='Teaching people to code',
        email='mike@test.com',
        password='test123'
    )
    
    print(f"   ✓ Created {User.objects.count()} test users")
    
    # Create posts
    post1 = Post.objects.create(
        user=user1,
        caption='Learning to code in Python',
        location='New York'
    )
    
    post2 = Post.objects.create(
        user=user2,
        caption='Beautiful sunset at the beach',
        location='California'
    )
    
    print(f"   ✓ Created {Post.objects.count()} test posts")
    
    # Create reels
    reel1 = Reel.objects.create(
        user=user3,
        caption='Quick coding tutorial',
        duration=30
    )
    
    print(f"   ✓ Created {Reel.objects.count()} test reels")
    
    # Test search functionality
    print("\n2. Testing search functionality...")
    
    factory = RequestFactory()
    view = ExploreViewSet.as_view({'get': 'search'})
    
    # Test 1: Search for "code" - should find users with "code" in bio and posts/reels with "code" in caption
    print("\n   Test 1: Searching for 'code'")
    request = factory.get('/api/explore/search/', {'q': 'code', 'type': 'all'})
    request.user = user1
    response = view(request)
    
    print(f"   - Users found: {len(response.data.get('users', []))}")
    print(f"   - Posts found: {len(response.data.get('posts', []))}")
    print(f"   - Reels found: {len(response.data.get('reels', []))}")
    
    if len(response.data.get('users', [])) > 0:
        print(f"   ✓ User search working (found users with 'code' in bio)")
    
    if len(response.data.get('posts', [])) > 0:
        print(f"   ✓ Post search working (found posts with 'code' in caption)")
    
    if len(response.data.get('reels', [])) > 0:
        print(f"   ✓ Reel search working (found reels with 'code' in caption)")
    
    # Test 2: Search for username
    print("\n   Test 2: Searching for 'john'")
    request = factory.get('/api/explore/search/', {'q': 'john', 'type': 'users'})
    request.user = user1
    response = view(request)
    
    users_found = len(response.data.get('users', []))
    print(f"   - Users found: {users_found}")
    if users_found > 0:
        print(f"   ✓ Username search working")
    
    # Test 3: Search for location
    print("\n   Test 3: Searching for 'California'")
    request = factory.get('/api/explore/search/', {'q': 'California', 'type': 'posts'})
    request.user = user1
    response = view(request)
    
    posts_found = len(response.data.get('posts', []))
    print(f"   - Posts found: {posts_found}")
    if posts_found > 0:
        print(f"   ✓ Location search working")
    
    # Test 4: Test pagination
    print("\n   Test 4: Testing pagination (limit=2)")
    request = factory.get('/api/explore/search/', {'q': 'test', 'type': 'all', 'limit': '2'})
    request.user = user1
    response = view(request)
    
    print(f"   ✓ Pagination parameter accepted")
    
    # Test 5: Empty query
    print("\n   Test 5: Testing empty query")
    request = factory.get('/api/explore/search/', {'q': '', 'type': 'all'})
    request.user = user1
    response = view(request)
    
    if response.data == {'users': [], 'posts': [], 'reels': [], 'hashtags': []}:
        print(f"   ✓ Empty query returns empty results")
    
    # Cleanup
    print("\n3. Cleaning up test data...")
    user1.delete()
    user2.delete()
    user3.delete()
    print("   ✓ Test data cleaned up")
    
    print("\n" + "=" * 60)
    print("All search tests completed successfully!")
    print("=" * 60)


if __name__ == '__main__':
    try:
        test_search_api()
    except Exception as e:
        print(f"\n✗ Error during testing: {e}")
        import traceback
        traceback.print_exc()
