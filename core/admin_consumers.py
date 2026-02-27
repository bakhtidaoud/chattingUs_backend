import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.db.models import Sum, Count
from .models import DailyAggregate, CustomUser, Listing, Order, Category

class AdminAnalyticsConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Only staff members can connect
        self.user = self.scope["user"]
        if not self.user.is_authenticated or not self.user.is_staff:
            await self.close()
            return

        self.room_group_name = 'admin_analytics'

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

    # Triggered when certain events happen (like a new order, user, etc.)
    async def dashboard_update(self, event):
        # Send data to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'dashboard_update',
            'data': event['data']
        }))

class PresenceConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        if not self.user.is_authenticated or not self.user.is_staff:
            await self.close()
            return

        self.resource_id = self.scope['url_route']['kwargs'].get('resource_id')
        self.room_group_name = f'presence_{self.resource_id}'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

        # Notify group about new join
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'presence_update',
                'user_id': self.user.id,
                'username': self.user.username,
                'action': 'join'
            }
        )

    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'presence_update',
                    'user_id': self.user.id,
                    'username': self.user.username,
                    'action': 'leave'
                }
            )
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    async def presence_update(self, event):
        await self.send(text_data=json.dumps(event))

    async def receive(self, text_data):
        data = json.loads(text_data)
        if data.get('type') == 'editing':
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'presence_update',
                    'user_id': self.user.id,
                    'username': self.user.username,
                    'action': 'editing'
                }
            )
