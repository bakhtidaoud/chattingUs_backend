import os
import django
import random
import requests
import json
from faker import Faker
from django.core.files.base import ContentFile
from django.utils import timezone
from datetime import timedelta

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chattingus_backend.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.core.management import call_command
from posts.models import Post, Comment, Like
from reels.models import Reel, ReelComment, ReelLike
from chat.models import Chat, Message
from users.models import UserProfile, Follow
from stories.models import Story, StoryView

User = get_user_model()
fake = Faker()

# Constants
NUM_USERS = 30
NUM_POSTS_PER_USER = 5  # Increased
NUM_REELS_PER_USER = 3  # Increased
NUM_STORIES_PER_USER = 3 # New
NUM_CHATS = 30 # Increased

# Sample Media URLs (Direct links to ensure stability)
IMAGE_URLS = [
    "https://picsum.photos/seed/1/800/800",
    "https://picsum.photos/seed/2/800/800",
    "https://picsum.photos/seed/3/800/800",
    "https://picsum.photos/seed/4/800/800",
    "https://picsum.photos/seed/5/800/800",
]

# Using a small valid MP4 for testing (approx 1MB)
VIDEO_URL = "https://test-videos.co.uk/vids/bigbuckbunny/mp4/h264/360/Big_Buck_Bunny_360_10s_1MB.mp4"

def download_file(url):
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return ContentFile(response.content)
    except Exception as e:
        print(f"Error downloading {url}: {e}")
    return None

def run():
    print("=== STARTING DATABASE POPULATION ===")
    
    # 1. Clear Database
    print("Clearing existing data...")
    # Delete in order of dependencies
    Message.objects.all().delete()
    Chat.objects.all().delete()
    StoryView.objects.all().delete()
    Story.objects.all().delete()
    ReelComment.objects.all().delete()
    ReelLike.objects.all().delete()
    Reel.objects.all().delete()
    Comment.objects.all().delete()
    Like.objects.all().delete()
    Post.objects.all().delete()
    Follow.objects.all().delete()
    UserProfile.objects.all().delete()
    User.objects.all().delete()
    
    # 2. Create Users
    print(f"Creating {NUM_USERS} users...")
    users = []
    user_credentials = []
    
    # Create Superuser
    admin_user = User.objects.create_superuser(
        username='admin',
        email='admin@example.com',
        password='AdminPassword123!'
    )
    users.append(admin_user)
    user_credentials.append(f"SUPERUSER | Username: admin | Email: admin@example.com | Password: AdminPassword123!")

    for i in range(NUM_USERS):
        profile = fake.profile()
        username = profile['username'] + str(random.randint(100, 999))
        email = profile['mail']
        password = "TestPassword123!"
        
        # Ensure unique email/username
        if User.objects.filter(username=username).exists():
            continue
            
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=fake.first_name(),
            last_name=fake.last_name(),
            phone_number=fake.phone_number()[:15], # Truncate to fit max_length if needed
            bio=fake.text(max_nb_chars=100),
            date_of_birth=fake.date_of_birth(minimum_age=18, maximum_age=50)
        )
        
        # Create UserProfile if not automatically created (depends on signals)
        UserProfile.objects.get_or_create(user=user)
        
        users.append(user)
        user_credentials.append(f"User {i+1} | Username: {username} | Email: {email} | Password: {password} | Phone: {user.phone_number}")
        print(f"  Created user: {username}")

    # Save credentials
    with open('user_credentials.txt', 'w') as f:
        f.write('\n'.join(user_credentials))
    print("Saved credentials to user_credentials.txt")

    # 3. Create Follows
    print("Creating relationships...")
    for user in users:
        # Follow 5 random users
        targets = random.sample(users, k=min(len(users), 5))
        for target in targets:
            if user != target:
                Follow.objects.get_or_create(follower=user, following=target)

    # 4. Download Media Assets (Cache them to avoid spamming requests)
    print("Downloading media assets...")
    sample_images = []
    for url in IMAGE_URLS:
        img = download_file(url)
        if img:
            sample_images.append(img)
            
    sample_video = download_file(VIDEO_URL)
    
    if not sample_images:
        print("WARNING: Could not download images. Using placeholders.")
    if not sample_video:
        print("WARNING: Could not download video. Skipping reels.")

    # 5. Create Posts
    print("Creating posts...")
    for user in users:
        for _ in range(NUM_POSTS_PER_USER):
            if not sample_images:
                break
                
            img_content = random.choice(sample_images)
            # Must create a new ContentFile for each save to avoid file closed errors
            img_file = ContentFile(img_content.read())
            img_file.name = f"post_{random.randint(1000,9999)}.jpg"
            
            post = Post.objects.create(
                user=user,
                caption=fake.sentence(),
                location=fake.city(),
                image=img_file
            )
            
            # Add likes and comments
            for _ in range(random.randint(0, 5)):
                liker = random.choice(users)
                Like.objects.get_or_create(user=liker, post=post)
                
            for _ in range(random.randint(0, 3)):
                commenter = random.choice(users)
                Comment.objects.create(
                    user=commenter,
                    post=post,
                    text=fake.sentence()
                )
    
    # 6. Create Stories
    if sample_images:
        print("Creating stories...")
        for user in users:
            for _ in range(NUM_STORIES_PER_USER):
                img_content = random.choice(sample_images)
                img_file = ContentFile(img_content.read())
                img_file.name = f"story_{random.randint(1000,9999)}.jpg"
                
                story = Story.objects.create(
                    user=user,
                    media=img_file,
                    media_type='image',
                    text=fake.sentence() if random.choice([True, False]) else ""
                )
                
                # Add views
                for _ in range(random.randint(0, 10)):
                    viewer = random.choice(users)
                    if viewer != user:
                        StoryView.objects.get_or_create(story=story, user=viewer)

    # 7. Create Reels
    if sample_video:
        print("Creating reels...")
        for user in users:
            for _ in range(NUM_REELS_PER_USER):
                video_file = ContentFile(sample_video.read())
                video_file.name = f"reel_{random.randint(1000,9999)}.mp4"
                
                reel = Reel.objects.create(
                    user=user,
                    caption=fake.sentence(),
                    video=video_file,
                    audio="Original Audio",
                    duration=10
                )
                
                # Add likes
                for _ in range(random.randint(0, 5)):
                    liker = random.choice(users)
                    ReelLike.objects.get_or_create(user=liker, reel=reel)

    # 7. Create Chats
    print("Creating chats...")
    # Duo Chats
    for _ in range(NUM_CHATS):
        participants = random.sample(users, 2)
        chat = Chat.objects.create(is_group=False)
        chat.participants.add(*participants)
        
        # Add messages
        for _ in range(random.randint(5, 15)):
            sender = random.choice(participants)
            Message.objects.create(
                chat=chat,
                sender=sender,
                content=fake.sentence(),
                message_type='text'
            )
            
    # Group Chats
    for _ in range(5):
        participants = random.sample(users, k=random.randint(3, 8))
        chat = Chat.objects.create(
            is_group=True,
            group_name=f"{fake.word()} Group"
        )
        chat.participants.add(*participants)
        
        for _ in range(random.randint(5, 20)):
            sender = random.choice(participants)
            Message.objects.create(
                chat=chat,
                sender=sender,
                content=fake.sentence(),
                message_type='text'
            )

    print("=== POPULATION COMPLETE ===")

if __name__ == '__main__':
    run()
