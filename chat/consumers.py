"""
WebSocket consumers for real-time messaging.
"""

import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .models import Chat, Message

User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for handling real-time chat messages.
    """
    
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'chat_{self.room_id}'
        self.user = self.scope['user']

        if not self.user.is_authenticated:
            await self.close()
            return

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()
        
        # Send online status
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_status',
                'user_id': self.user.id,
                'status': 'online'
            }
        )

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        
        # Send offline status
        if hasattr(self, 'user') and self.user.is_authenticated:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_status',
                    'user_id': self.user.id,
                    'status': 'offline'
                }
            )

    async def receive(self, text_data):
        """
        Receive message from WebSocket
        """
        text_data_json = json.loads(text_data)
        message_type = text_data_json.get('type', 'chat_message')
        
        if message_type == 'chat_message':
            message_content = text_data_json.get('message')
            msg_type = text_data_json.get('message_type', 'text')
            
            # Save message to DB
            message = await self.save_message(self.room_id, self.user.id, message_content, msg_type)
            
            # Send message to room group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': message_content,
                    'sender': self.user.username,
                    'sender_id': self.user.id,
                    'message_id': message.id,
                    'message_type': msg_type,
                    'created_at': str(message.created_at)
                }
            )
            
        elif message_type == 'typing':
            is_typing = text_data_json.get('is_typing', False)
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_typing',
                    'user_id': self.user.id,
                    'is_typing': is_typing
                }
            )
            
        elif message_type == 'read_receipt':
            message_id = text_data_json.get('message_id')
            await self.mark_message_read(message_id)
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'message_read',
                    'message_id': message_id,
                    'user_id': self.user.id
                }
            )

    async def chat_message(self, event):
        """
        Receive message from room group
        """
        await self.send(text_data=json.dumps(event))

    async def user_typing(self, event):
        """
        Receive typing event from room group
        """
        await self.send(text_data=json.dumps(event))
        
    async def user_status(self, event):
        """
        Receive user status event from room group
        """
        await self.send(text_data=json.dumps(event))

    async def message_read(self, event):
        """
        Receive read receipt from room group
        """
        await self.send(text_data=json.dumps(event))

    @database_sync_to_async
    def save_message(self, chat_id, user_id, content, msg_type):
        chat = Chat.objects.get(id=chat_id)
        user = User.objects.get(id=user_id)
        return Message.objects.create(chat=chat, sender=user, content=content, message_type=msg_type)

    @database_sync_to_async
    def mark_message_read(self, message_id):
        try:
            message = Message.objects.get(id=message_id)
            message.is_read = True
            message.save()
        except Message.DoesNotExist:
            pass


class NotificationConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for handling real-time notifications.
    """
    
    async def connect(self):
        self.user_id = self.scope['user'].id if self.scope['user'].is_authenticated else None
        
        if self.user_id:
            self.notification_group_name = f'notifications_{self.user_id}'

            # Join notification group
            await self.channel_layer.group_add(
                self.notification_group_name,
                self.channel_name
            )

            await self.accept()
        else:
            await self.close()

    async def disconnect(self, close_code):
        if self.user_id:
            # Leave notification group
            await self.channel_layer.group_discard(
                self.notification_group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        """
        Receive notification from WebSocket
        """
        pass

    async def send_notification(self, event):
        """
        Send notification to WebSocket
        """
        notification = event['notification']

        # Send notification to WebSocket
        await self.send(text_data=json.dumps({
            'notification': notification
        }))
