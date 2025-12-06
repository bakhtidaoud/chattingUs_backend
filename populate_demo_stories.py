"""
Script to populate demo stories for all users with images and create mutual follows.
Uses free images from Picsum (Lorem Picsum).
"""

import os
import django
import requests
from datetime import datetime, timedelta
import random

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chattingus_backend.settings')
django.setup()

from django.contrib.auth import get_user_model
from stories.models import Story
from users.models import Follow
from django.core.files.base import ContentFile
from django.utils import timezone

User = get_user_model()

# Picsum Photos - reliable free image service
PICSUM_BASE_URL = "https://picsum.photos/1080/1920"


def download_image():
    """
    Download a random image from Picsum Photos.
        
    Returns:
        ContentFile with image data or None
    """
    try:
        # Random image with cache busting
        url = f"{PICSUM_BASE_URL}?random={random.randint(1, 100000)}"
        
        print(f"  Downloading image...")
        response = requests.get(url, timeout=15, allow_redirects=True)
        
        if response.status_code == 200:
            return ContentFile(response.content, name=f'story_{random.randint(1000, 9999)}.jpg')
        else:
            print(f"  Failed to download image: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"  Error downloading image: {e}")
        return None


def create_stories_for_user(user, num_stories=3):
    """
    Create demo stories for a user with images.
    
    Args:
        user: User instance
        num_stories: Number of stories to create
    """
    print(f"\nCreating {num_stories} stories for {user.username}...")
    
    created_count = 0
    
    # Story captions for variety
    captions = [
        "Beautiful day! ☀️",
        "Check this out! 📸",
        "Amazing view! 🌟",
        "Love this moment! ❤️",
        "Perfect! ✨",
        "Incredible! 🔥",
        "Wow! 😍",
        "Awesome! 🎉",
        "Great times! 🌈",
        "Feeling good! 😊"
    ]
    
    for i in range(num_stories):
        # Download image
        image_file = download_image()
        
        if image_file:
            try:
                # Random caption
                caption = random.choice(captions)
                
                # Create story (using correct field names: text and media)
                story = Story.objects.create(
                    user=user,
                    text=caption,
                    media_type='image',
                    duration=5
                )
                
                # Save media file
                story.media.save(image_file.name, image_file, save=True)
                
                # Set created_at to random time in last 23 hours (stories expire after 24h)
                hours_ago = random.randint(1, 23)
                story.created_at = timezone.now() - timedelta(hours=hours_ago)
                story.save()
                
                created_count += 1
                print(f"  ✓ Created story {i+1}/{num_stories}")
                
            except Exception as e:
                print(f"  ✗ Failed to create story: {e}")
        else:
            print(f"  ✗ Skipped story {i+1} (image download failed)")
    
    print(f"  Total created: {created_count}/{num_stories}")
    return created_count


def create_mutual_follows():
    """
    Make all users follow each other (mutual follows).
    """
    print("\n" + "="*60)
    print("Creating mutual follows between all users...")
    print("="*60)
    
    users = list(User.objects.all())
    total_users = len(users)
    
    if total_users < 2:
        print("Need at least 2 users to create follows")
        return
    
    created_count = 0
    skipped_count = 0
    
    for i, user1 in enumerate(users):
        for user2 in users:
            # Don't follow yourself
            if user1.id == user2.id:
                continue
            
            # Create follow if doesn't exist
            follow, created = Follow.objects.get_or_create(
                follower=user1,
                following=user2
            )
            
            if created:
                created_count += 1
            else:
                skipped_count += 1
        
        print(f"  {user1.username} now follows {total_users - 1} users")
    
    print(f"\n✓ Created {created_count} new follows")
    print(f"  Skipped {skipped_count} existing follows")
    print(f"  Total users: {total_users}")
    print(f"  Each user follows: {total_users - 1} others")


def update_follow_counts():
    """
    Update followers_count and following_count for all users.
    """
    print("\n" + "="*60)
    print("Updating follower/following counts...")
    print("="*60)
    
    for user in User.objects.all():
        try:
            profile = user.profile
            profile.followers_count = Follow.objects.filter(following=user).count()
            profile.following_count = Follow.objects.filter(follower=user).count()
            profile.save()
            
            print(f"  {user.username}: {profile.followers_count} followers, {profile.following_count} following")
        except Exception as e:
            print(f"  Error updating {user.username}: {e}")


def main():
    """
    Main function to populate demo data.
    """
    print("\n" + "="*60)
    print("DEMO DATA POPULATION SCRIPT")
    print("="*60)
    print("This script will:")
    print("1. Create demo stories for all users with free images")
    print("2. Make all users follow each other")
    print("3. Update follower/following counts")
    print("="*60)
    
    # Get all users
    users = User.objects.all()
    total_users = users.count()
    
    if total_users == 0:
        print("\n✗ No users found in database!")
        print("  Please create users first using the registration endpoint or admin panel.")
        return
    
    print(f"\nFound {total_users} users in database")
    
    # Ask for confirmation
    response = input("\nDo you want to proceed? (yes/no): ").strip().lower()
    
    if response not in ['yes', 'y']:
        print("\n✗ Operation cancelled")
        return
    
    # Ask how many stories per user
    try:
        stories_per_user = int(input("\nHow many stories per user? (1-5, default 3): ").strip() or "3")
        stories_per_user = max(1, min(5, stories_per_user))
    except ValueError:
        stories_per_user = 3
    
    print(f"\nWill create {stories_per_user} stories per user")
    print("Using Picsum Photos for free images...")
    
    # Create stories
    print("\n" + "="*60)
    print("CREATING DEMO STORIES")
    print("="*60)
    
    total_stories_created = 0
    
    for user in users:
        count = create_stories_for_user(user, stories_per_user)
        total_stories_created += count
    
    print(f"\n✓ Total stories created: {total_stories_created}")
    
    # Create mutual follows
    create_mutual_follows()
    
    # Update counts
    update_follow_counts()
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"✓ Users: {total_users}")
    print(f"✓ Stories created: {total_stories_created}")
    print(f"✓ Total follows: {Follow.objects.count()}")
    print(f"✓ Each user follows: {total_users - 1} others")
    print("="*60)
    print("\n✓ Demo data population completed successfully!")
    print("\nYou can now:")
    print("1. View stories in the app")
    print("2. See all users following each other")
    print("3. Test story viewing, reactions, and replies")
    print("\nNote: Stories will expire after 24 hours from their created_at time")
    print("Image source: Picsum Photos (https://picsum.photos)")


if __name__ == '__main__':
    main()
