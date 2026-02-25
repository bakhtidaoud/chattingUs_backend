from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from core.models import Post, Follow, FeedPost, Block
from django.db.models import Q
from django.utils import timezone

User = get_user_model()

class Command(BaseCommand):
    help = 'Pre-compute feeds for all active users'

    def handle(self, *args, **options):
        users = User.objects.all()
        processed_count = 0
        
        for user in users:
            # 1. Get posts from followed accounts
            following_ids = Follow.objects.filter(
                follower=user, 
                status='accepted'
            ).values_list('followed_id', flat=True)
            
            followed_posts = Post.objects.filter(user_id__in=following_ids)
            
            # 2. Suggested posts (popular tags or just recent ones from public accounts)
            # For simplicity, getting recent posts not from current user/already filtered
            # excluding blocks
            blocked_users = Block.objects.filter(user=user).values_list('blocked_user_id', flat=True)
            blocked_by_users = Block.objects.filter(blocked_user=user).values_list('user_id', flat=True)
            
            exclude_ids = set(following_ids)
            exclude_ids.add(user.id)
            exclude_ids.update(blocked_users)
            exclude_ids.update(blocked_by_users)
            
            suggested_posts = Post.objects.exclude(
                user_id__in=exclude_ids
            ).filter(user__is_private=False).order_by('-created_at')[:20]
            
            # 3. Combine and refresh feed
            # Clear existing feed for the user
            # In production, you might want to only append new ones
            FeedPost.objects.filter(user=user).delete()
            
            feed_entries = []
            
            # Add followed posts
            for post in followed_posts.order_by('-created_at')[:100]:
                feed_entries.append(FeedPost(user=user, post=post, source='following'))
                
            # Add suggested posts
            for post in suggested_posts:
                feed_entries.append(FeedPost(user=user, post=post, source='suggested'))
            
            FeedPost.objects.bulk_create(feed_entries, ignore_conflicts=True)
            processed_count += 1
            
        self.stdout.write(self.style.SUCCESS(f'Successfully generated feeds for {processed_count} users'))
