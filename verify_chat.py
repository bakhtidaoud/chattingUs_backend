import os
import django
import asyncio
import json
from channels.testing import WebsocketCommunicator
from channels.routing import URLRouter
from django.urls import path
from django.contrib.auth import get_user_model

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chattingus_backend.settings')
django.setup()

from chat import consumers
from chat.models import Chat, Message
from rest_framework.test import APIClient

User = get_user_model()

async def verify_chat():
    print("Starting Chat Verification...")
    
    # 1. Create Test Users
    username1 = "chat_user_1"
    username2 = "chat_user_2"
    password = "testpassword123"
    
    user1, _ = await User.objects.aget_or_create(username=username1, email=f"{username1}@example.com")
    user1.set_password(password)
    await user1.asave()
    
    user2, _ = await User.objects.aget_or_create(username=username2, email=f"{username2}@example.com")
    user2.set_password(password)
    await user2.asave()
    
    print(f"Created users: {username1}, {username2}")
    
    # 2. Create Chat via API (simulated)
    # Since we can't easily use APIClient in async, we'll use ORM directly for setup
    chat = await Chat.objects.acreate()
    await chat.participants.aadd(user1, user2)
    print(f"Created chat: {chat.id}")
    
    # 3. Test WebSocket Connection
    application = URLRouter([
        path('ws/api/chat/<int:room_id>/', consumers.ChatConsumer.as_asgi()),
    ])
    
    communicator = WebsocketCommunicator(application, f"/ws/api/chat/{chat.id}/")
    communicator.scope['user'] = user1
    connected, subprotocol = await communicator.connect()
    
    if not connected:
        print("WebSocket connection failed.")
        return
    print("WebSocket connected.")
    
    # 4. Receive Online Status
    response = await communicator.receive_json_from()
    print(f"Received status: {response}")
    
    # 5. Send Message
    message_content = "Hello from WebSocket!"
    await communicator.send_json_to({
        'type': 'chat_message',
        'message': message_content,
        'message_type': 'text'
    })
    
    # 6. Receive Message
    response = await communicator.receive_json_from()
    print(f"Received message: {response}")
    
    if response['message'] != message_content:
        print("Error: Message content mismatch.")
        return
        
    # 7. Test Typing
    await communicator.send_json_to({
        'type': 'typing',
        'is_typing': True
    })
    
    response = await communicator.receive_json_from()
    print(f"Received typing: {response}")
    
    # 8. Disconnect
    await communicator.disconnect()
    print("Verification Complete!")

if __name__ == "__main__":
    asyncio.run(verify_chat())
