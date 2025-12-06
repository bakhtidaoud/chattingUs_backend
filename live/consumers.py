"""
WebSocket consumer for live streaming real-time interactions.
"""

import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .models import LiveStream, LiveViewer, LiveComment, LiveReaction

User = get_user_model()


class LiveStreamConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for live stream interactions.
    
    Handles:
    - WebRTC signaling (offer, answer, ICE candidates)
    - Real-time comments
    - Real-time reactions
    - Viewer join/leave notifications
    - Viewer count updates
    """
    
    async def connect(self):
        """Handle WebSocket connection."""
        self.stream_id = self.scope['url_route']['kwargs']['stream_id']
        self.room_group_name = f'live_stream_{self.stream_id}'
        self.user = self.scope['user']
        
        # Check if user is authenticated
        if not self.user.is_authenticated:
            await self.close()
            return
        
        # Check if stream exists and is live
        stream = await self.get_stream()
        if not stream or stream.status not in ['live', 'waiting']:
            await self.close()
            return
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send current viewer count
        viewer_count = await self.get_viewer_count()
        await self.send(text_data=json.dumps({
            'type': 'viewer_count',
            'count': viewer_count
        }))
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """
        Receive message from WebSocket.
        
        Message types:
        - webrtc_offer: WebRTC offer from broadcaster
        - webrtc_answer: WebRTC answer from viewer
        - ice_candidate: ICE candidate for WebRTC
        - comment: Live comment
        - reaction: Live reaction
        - viewer_join: Viewer joined notification
        - viewer_leave: Viewer left notification
        """
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'webrtc_offer':
                # Broadcast WebRTC offer to all viewers
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'webrtc_signal',
                        'signal_type': 'offer',
                        'sdp': data.get('sdp'),
                        'sender_id': self.user.id
                    }
                )
            
            elif message_type == 'webrtc_answer':
                # Send WebRTC answer to broadcaster
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'webrtc_signal',
                        'signal_type': 'answer',
                        'sdp': data.get('sdp'),
                        'sender_id': self.user.id,
                        'target_id': data.get('target_id')
                    }
                )
            
            elif message_type == 'ice_candidate':
                # Broadcast ICE candidate
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'webrtc_signal',
                        'signal_type': 'ice_candidate',
                        'candidate': data.get('candidate'),
                        'sender_id': self.user.id
                    }
                )
            
            elif message_type == 'comment':
                # Save and broadcast comment
                comment = await self.save_comment(data.get('text'))
                if comment:
                    user_data = await self.get_user_data(self.user)
                    await self.channel_layer.group_send(
                        self.room_group_name,
                        {
                            'type': 'live_comment',
                            'comment': {
                                'id': comment.id,
                                'user': user_data,
                                'text': comment.text,
                                'created_at': comment.created_at.isoformat()
                            }
                        }
                    )
            
            elif message_type == 'reaction':
                # Save and broadcast reaction
                reaction = await self.save_reaction(data.get('reaction_type'))
                if reaction:
                    user_data = await self.get_user_data(self.user)
                    await self.channel_layer.group_send(
                        self.room_group_name,
                        {
                            'type': 'live_reaction',
                            'reaction': {
                                'id': reaction.id,
                                'user': user_data,
                                'reaction_type': reaction.reaction_type,
                                'created_at': reaction.created_at.isoformat()
                            }
                        }
                    )
            
            elif message_type == 'viewer_update':
                # Update viewer count
                viewer_count = await self.get_viewer_count()
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'viewer_count_update',
                        'count': viewer_count
                    }
                )
        
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON'
            }))
        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': str(e)
            }))
    
    # Group message handlers
    
    async def webrtc_signal(self, event):
        """Send WebRTC signaling message."""
        await self.send(text_data=json.dumps({
            'type': 'webrtc_signal',
            'signal_type': event['signal_type'],
            'sdp': event.get('sdp'),
            'candidate': event.get('candidate'),
            'sender_id': event['sender_id'],
            'target_id': event.get('target_id')
        }))
    
    async def live_comment(self, event):
        """Send live comment to all viewers."""
        await self.send(text_data=json.dumps({
            'type': 'comment',
            'comment': event['comment']
        }))
    
    async def live_reaction(self, event):
        """Send live reaction to all viewers."""
        await self.send(text_data=json.dumps({
            'type': 'reaction',
            'reaction': event['reaction']
        }))
    
    async def viewer_count_update(self, event):
        """Send viewer count update."""
        await self.send(text_data=json.dumps({
            'type': 'viewer_count',
            'count': event['count']
        }))
    
    # Database operations
    
    @database_sync_to_async
    def get_stream(self):
        """Get the live stream."""
        try:
            return LiveStream.objects.get(id=self.stream_id)
        except LiveStream.DoesNotExist:
            return None
    
    @database_sync_to_async
    def get_viewer_count(self):
        """Get current viewer count."""
        try:
            stream = LiveStream.objects.get(id=self.stream_id)
            return stream.viewers.filter(is_active=True).count()
        except LiveStream.DoesNotExist:
            return 0
    
    @database_sync_to_async
    def save_comment(self, text):
        """Save a comment to the database."""
        try:
            stream = LiveStream.objects.get(id=self.stream_id)
            comment = LiveComment.objects.create(
                stream=stream,
                user=self.user,
                text=text
            )
            return comment
        except Exception:
            return None
    
    @database_sync_to_async
    def save_reaction(self, reaction_type):
        """Save a reaction to the database."""
        try:
            stream = LiveStream.objects.get(id=self.stream_id)
            reaction = LiveReaction.objects.create(
                stream=stream,
                user=self.user,
                reaction_type=reaction_type
            )
            return reaction
        except Exception:
            return None
    
    @database_sync_to_async
    def get_user_data(self, user):
        """Get user data for serialization."""
        return {
            'id': user.id,
            'username': user.username,
            'full_name': user.get_full_name(),
            'profile_picture': user.profile_picture.url if user.profile_picture else None
        }
