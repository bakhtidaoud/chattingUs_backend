import json
from channels.generic.websocket import AsyncWebsocketConsumer

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.conversation_id = self.scope['url_route']['kwargs']['conversation_id']
        self.room_group_name = f'chat_{self.conversation_id}'

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
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
                    'user_id': self.scope['user'].id if self.scope['user'].is_authenticated else None,
                    'username': self.scope['user'].username if self.scope['user'].is_authenticated else "Anonymous",
                    'is_typing': data.get('is_typing')
                }
            )

    # Receive message from room group
    async def chat_typing(self, event):
        # Send message to WebSocket
        # Only send to other participants (not yourself)
        current_user_id = self.scope['user'].id if self.scope['user'].is_authenticated else None
        if event['user_id'] != current_user_id:
            await self.send(text_data=json.dumps({
                'type': 'typing',
                'user_id': event['user_id'],
                'username': event['username'],
                'is_typing': event['is_typing']
            }))
