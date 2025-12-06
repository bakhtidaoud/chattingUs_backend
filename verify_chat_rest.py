import os
import django
from django.contrib.auth import get_user_model
# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chattingus_backend.settings')
django.setup()

from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from chat.models import Chat, Message, Reaction
from reels.models import Reel

User = get_user_model()

def verify_chat_rest():
    print("Starting Chat REST Verification...")
    
    # 1. Create Test Users
    username1 = "rest_user_1"
    username2 = "rest_user_2"
    password = "testpassword123"
    
    if User.objects.filter(username=username1).exists():
        User.objects.get(username=username1).delete()
    if User.objects.filter(username=username2).exists():
        User.objects.get(username=username2).delete()
        
    user1 = User.objects.create_user(username=username1, password=password)
    user2 = User.objects.create_user(username=username2, password=password)
    print(f"Created users: {username1}, {username2}")
    
    # 2. Login
    client = APIClient()
    client.force_authenticate(user=user1)
    
    # 3. Create Chat
    response = client.post('/api/chat/chats/', {'participants': [user2.id]})
    if response.status_code != 201:
        print(f"Create chat failed: {response.data}")
        return
    chat_id = response.data['id']
    print(f"Created chat: {chat_id}")
    
    # 4. Send Message
    response = client.post('/api/chat/messages/', {'chat': chat_id, 'content': 'Hello World', 'message_type': 'text'})
    if response.status_code != 201:
        print(f"Send message failed: {response.data}")
        return
    message_id = response.data['id']
    print(f"Sent message: {message_id}")
    
    # 5. React to Message
    response = client.post(f'/api/chat/messages/{message_id}/react/', {'reaction': 'like'})
    if response.status_code != 200:
        print(f"React failed: {response.data}")
        return
    print("Reacted to message.")
    
    # 6. Forward Message
    response = client.post('/api/chat/messages/', {'chat': chat_id, 'content': 'Forwarded', 'forwarded_from_id': message_id})
    if response.status_code != 201:
        print(f"Forward message failed: {response.data}")
        return
    print("Forwarded message.")
    
    # 7. Share Reel (Mock Reel)
    # Create dummy reel first
    # Need a video file... skipping file creation for simplicity, just mocking object
    # But Reel requires video file. We'll skip actual Reel creation and just test the endpoint logic if possible
    # Or create a minimal Reel object if model allows nulls (it doesn't usually).
    # Let's try to create a dummy reel.
    from django.core.files.uploadedfile import SimpleUploadedFile
    
    # Create dummy video file
    video_content = b'fake video content'
    video_file = SimpleUploadedFile("video.mp4", video_content, content_type="video/mp4")
    
    reel = Reel.objects.create(user=user1, video=video_file, caption="Test Reel")
    
    response = client.post(f'/api/chat/chats/{chat_id}/share-reel/', {'reel_id': reel.id})
    if response.status_code != 201:
        print(f"Share reel failed: {response.data}")
        return
    print("Shared reel.")
    
    # 8. Delete Message
    response = client.delete(f'/api/chat/messages/{message_id}/')
    if response.status_code != 204:
        print(f"Delete message failed: {response.status_code}")
        return
    print("Deleted message.")
    
    print("Verification Complete!")

if __name__ == "__main__":
    verify_chat_rest()
