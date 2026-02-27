from django.urls import re_path
from . import consumers, admin_consumers

websocket_urlpatterns = [
    re_path(r'ws/chat/(?P<conversation_id>\w+)/$', consumers.ChatConsumer.as_asgi()),
    re_path(r'ws/admin/analytics/$', admin_consumers.AdminAnalyticsConsumer.as_asgi()),
]
