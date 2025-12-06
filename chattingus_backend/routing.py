"""
WebSocket URL routing for chattingus_backend project.
"""

from django.urls import path
from chat import consumers
from live.routing import websocket_urlpatterns as live_websocket_urlpatterns

websocket_urlpatterns = [
    path('ws/api/chat/<int:room_id>/', consumers.ChatConsumer.as_asgi()),
    path('ws/notifications/', consumers.NotificationConsumer.as_asgi()),
] + live_websocket_urlpatterns
