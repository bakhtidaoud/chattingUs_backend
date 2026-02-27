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
