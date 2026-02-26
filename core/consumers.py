import json
from django.utils import timezone
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Conversation, Message, MessageReaction, CustomUser, Profile
from .serializers import MessageSerializer, MessageReactionSerializer

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.conversation_id = self.scope['url_route']['kwargs']['conversation_id']
        self.room_group_name = f'chat_{self.conversation_id}'
        
        # Check if user is authenticated and is a participant of the conversation
        self.user = self.scope["user"]
        if not self.user.is_authenticated:
            await self.close()
            return
            
        if not await self.is_participant(self.user, self.conversation_id):
            await self.close()
            return

        # Update last_seen and online status
        await self.update_user_status(True)

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

        # Notify participants that user is online
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_status',
                'user_id': self.user.id,
                'username': self.user.username,
                'is_online': True
            }
        )

    async def disconnect(self, close_code):
        # Update last_seen and offline status
        await self.update_user_status(False)

        # Notify participants that user is offline
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_status',
                'user_id': self.user.id,
                'username': self.user.username,
                'is_online': False,
                'last_seen': timezone.now().isoformat()
            }
        )

        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type')

        if message_type == 'typing':
            # Send typing event to room group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_typing',
                    'user_id': self.user.id,
                    'username': self.user.username,
                    'is_typing': data.get('is_typing')
                }
            )
        
        elif message_type == 'message':
            message_text = data.get('message')
            if message_text:
                # Save message to database
                message = await self.save_message(self.user, self.conversation_id, message_text)
                
                # Send message to room group
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'chat_message',
                        'message': MessageSerializer(message).data
                    }
                )

        elif message_type == 'reaction':
            message_id = data.get('message_id')
            emoji = data.get('emoji')
            action = data.get('action', 'add') # 'add' or 'remove'
            
            if message_id and emoji:
                if action == 'add':
                    reaction = await self.add_reaction(self.user, message_id, emoji)
                    reaction_data = MessageReactionSerializer(reaction).data
                else:
                    await self.remove_reaction(self.user, message_id, emoji)
                    reaction_data = {'emoji': emoji, 'user_id': self.user.id}

                # Send reaction to room group
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'chat_reaction',
                        'reaction': reaction_data,
                        'message_id': message_id,
                        'action': action
                    }
                )

    # Receive typing message from room group
    async def chat_typing(self, event):
        # Only send to other participants (not yourself)
        if event['user_id'] != self.user.id:
            await self.send(text_data=json.dumps({
                'type': 'typing',
                'user_id': event['user_id'],
                'username': event['username'],
                'is_typing': event['is_typing']
            }))

    # Receive chat message from room group
    async def chat_message(self, event):
        message_data = event['message']
        
        # Mark as read if received by a participant who is not the sender
        if message_data['sender']['id'] != self.user.id:
            await self.mark_as_read(message_data['id'])
            message_data['is_read'] = True

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'message',
            'message': message_data
        }))

    # Receive reaction from room group
    async def chat_reaction(self, event):
        await self.send(text_data=json.dumps({
            'type': 'reaction',
            'reaction': event['reaction'],
            'message_id': event['message_id'],
            'action': event['action']
        }))

    # Receive user status change from room group
    async def user_status(self, event):
        if event['user_id'] != self.user.id:
            await self.send(text_data=json.dumps({
                'type': 'user_status',
                'user_id': event['user_id'],
                'username': event['username'],
                'is_online': event['is_online'],
                'last_seen': event.get('last_seen')
            }))

    @database_sync_to_async
    def is_participant(self, user, conversation_id):
        try:
            return Conversation.objects.filter(id=conversation_id, participants=user).exists()
        except:
            return False

    @database_sync_to_async
    def save_message(self, user, conversation_id, text):
        try:
            conversation = Conversation.objects.get(id=conversation_id)
            return Message.objects.create(
                conversation=conversation,
                sender=user,
                text=text
            )
        except Conversation.DoesNotExist:
            return None

    @database_sync_to_async
    def mark_as_read(self, message_id):
        Message.objects.filter(id=message_id).update(is_read=True)

    @database_sync_to_async
    def add_reaction(self, user, message_id, emoji):
        reaction, created = MessageReaction.objects.get_or_create(
            message_id=message_id,
            user=user,
            emoji=emoji
        )
        return reaction

    @database_sync_to_async
    def remove_reaction(self, user, message_id, emoji):
        MessageReaction.objects.filter(
            message_id=message_id,
            user=user,
            emoji=emoji
        ).delete()

    @database_sync_to_async
    def update_user_status(self, is_online):
        CustomUser.objects.filter(id=self.user.id).update(last_login=timezone.now())
        Profile.objects.update_or_create(
            user=self.user,
            defaults={
                'is_online': is_online,
                'last_seen': timezone.now()
            }
        )
