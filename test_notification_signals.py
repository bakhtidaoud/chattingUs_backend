"""
Test script to verify notification signals work correctly.
Run this with: python test_notification_signals.py
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chattingus_backend.settings')
django.setup()

from django.contrib.auth import get_user_model
from users.models import Follow
from chat.models import Chat, Message
from stories.models import Story, StoryReply
from notifications.models import Notification

User = get_user_model()

def test_follow_notification():
    """Test that following a user creates a notification."""
    print("\n=== Testing Follow Notification ===")
    
    # Create test users
    follower = User.objects.create_user(
        username='test_follower',
        email='follower@test.com',
        password='testpass123'
    )
    following = User.objects.create_user(
        username='test_following',
        email='following@test.com',
        password='testpass123'
    )
    
    # Get initial notification count
    initial_count = Notification.objects.filter(recipient=following).count()
    
    # Create a follow relationship
    follow = Follow.objects.create(follower=follower, following=following)
    
    # Check if notification was created
    final_count = Notification.objects.filter(recipient=following).count()
    
    if final_count > initial_count:
        notification = Notification.objects.filter(
            recipient=following,
            sender=follower,
            notification_type='follow'
        ).first()
        
        if notification:
            print(f"✓ Follow notification created successfully!")
            print(f"  - Recipient: {notification.recipient.username}")
            print(f"  - Sender: {notification.sender.username}")
            print(f"  - Type: {notification.notification_type}")
            print(f"  - Text: {notification.get_notification_text()}")
        else:
            print("✗ Notification created but with wrong type or sender")
    else:
        print("✗ No notification was created")
    
    # Cleanup
    follower.delete()
    following.delete()


def test_message_notification():
    """Test that sending a message creates notifications for recipients."""
    print("\n=== Testing Message Notification ===")
    
    # Create test users
    sender = User.objects.create_user(
        username='test_sender',
        email='sender@test.com',
        password='testpass123'
    )
    recipient1 = User.objects.create_user(
        username='test_recipient1',
        email='recipient1@test.com',
        password='testpass123'
    )
    recipient2 = User.objects.create_user(
        username='test_recipient2',
        email='recipient2@test.com',
        password='testpass123'
    )
    
    # Create a chat
    chat = Chat.objects.create(is_group=True, group_name='Test Group')
    chat.participants.add(sender, recipient1, recipient2)
    
    # Get initial notification count
    initial_count1 = Notification.objects.filter(recipient=recipient1).count()
    initial_count2 = Notification.objects.filter(recipient=recipient2).count()
    
    # Send a message
    message = Message.objects.create(
        chat=chat,
        sender=sender,
        content='Hello everyone!'
    )
    
    # Check if notifications were created
    final_count1 = Notification.objects.filter(recipient=recipient1).count()
    final_count2 = Notification.objects.filter(recipient=recipient2).count()
    
    if final_count1 > initial_count1 and final_count2 > initial_count2:
        print(f"✓ Message notifications created successfully!")
        print(f"  - Notifications sent to {final_count1 - initial_count1 + final_count2 - initial_count2} recipients")
        
        notification = Notification.objects.filter(
            recipient=recipient1,
            sender=sender,
            notification_type='message'
        ).first()
        
        if notification:
            print(f"  - Type: {notification.notification_type}")
            print(f"  - Text: {notification.get_notification_text()}")
    else:
        print("✗ Not all notifications were created")
    
    # Cleanup
    sender.delete()
    recipient1.delete()
    recipient2.delete()


def test_story_reply_notification():
    """Test that replying to a story creates a notification."""
    print("\n=== Testing Story Reply Notification ===")
    
    # Create test users
    story_owner = User.objects.create_user(
        username='test_story_owner',
        email='owner@test.com',
        password='testpass123'
    )
    replier = User.objects.create_user(
        username='test_replier',
        email='replier@test.com',
        password='testpass123'
    )
    
    # Create a story
    story = Story.objects.create(
        user=story_owner,
        media_type='image'
    )
    
    # Get initial notification count
    initial_count = Notification.objects.filter(recipient=story_owner).count()
    
    # Create a reply
    reply = StoryReply.objects.create(
        story=story,
        user=replier,
        text='Nice story!'
    )
    
    # Check if notification was created
    final_count = Notification.objects.filter(recipient=story_owner).count()
    
    if final_count > initial_count:
        notification = Notification.objects.filter(
            recipient=story_owner,
            sender=replier,
            notification_type='comment'
        ).first()
        
        if notification:
            print(f"✓ Story reply notification created successfully!")
            print(f"  - Recipient: {notification.recipient.username}")
            print(f"  - Sender: {notification.sender.username}")
            print(f"  - Type: {notification.notification_type}")
            print(f"  - Text: {notification.get_notification_text()}")
        else:
            print("✗ Notification created but with wrong type or sender")
    else:
        print("✗ No notification was created")
    
    # Cleanup
    story_owner.delete()
    replier.delete()


if __name__ == '__main__':
    print("=" * 60)
    print("Testing Notification Signals")
    print("=" * 60)
    
    try:
        test_follow_notification()
        test_message_notification()
        test_story_reply_notification()
        
        print("\n" + "=" * 60)
        print("All tests completed!")
        print("=" * 60)
    except Exception as e:
        print(f"\n✗ Error during testing: {e}")
        import traceback
        traceback.print_exc()
