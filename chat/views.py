"""
Views for the messages app.
"""

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes
from django.utils import timezone
from datetime import timedelta
from .models import Chat, Message, Reaction
from .serializers import ChatSerializer, MessageSerializer, ReactionSerializer
from reels.models import Reel


class MessageViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Message model.
    """
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Filter messages to only show those in user's chats.
        """
        user = self.request.user
        return Message.objects.filter(chat__participants=user)

    def perform_create(self, serializer):
        serializer.save(sender=self.request.user)

    def destroy(self, request, *args, **kwargs):
        """
        Delete message. Check for 'delete for everyone' time limit.
        """
        instance = self.get_object()
        if instance.sender != request.user:
            return Response({'error': 'You can only delete your own messages'}, status=status.HTTP_403_FORBIDDEN)
        
        # Check if message is older than 1 hour
        if timezone.now() - instance.created_at > timedelta(hours=1):
             # Soft delete or just hide content? Requirement says "Delete for everyone"
             # Usually we keep the record but clear content.
             # For now, let's just delete it as per standard REST, or maybe update content to "Deleted"
             # But standard DELETE implies removal. Let's stick to removal for now.
             return Response({'error': 'Cannot delete message older than 1 hour'}, status=status.HTTP_400_BAD_REQUEST)

        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'])
    @extend_schema(
        summary="React to message",
        description="Add a reaction to a message.",
        request=ReactionSerializer,
        responses={200: ReactionSerializer}
    )
    def react(self, request, pk=None):
        """
        Add a reaction to a message.
        """
        message = self.get_object()
        reaction_text = request.data.get('reaction')
        if not reaction_text:
            return Response({'error': 'Reaction text required'}, status=status.HTTP_400_BAD_REQUEST)
            
        reaction, created = Reaction.objects.update_or_create(
            message=message,
            user=request.user,
            defaults={'reaction': reaction_text}
        )
        return Response(ReactionSerializer(reaction).data)

    @action(detail=True, methods=['put'])
    @extend_schema(
        summary="Mark message read",
        description="Mark a single message as read.",
        responses={200: OpenApiTypes.OBJECT}
    )
    def read(self, request, pk=None):
        """
        Mark message as read.
        """
        message = self.get_object()
        if message.sender != request.user:
            message.is_read = True
            message.save()
        return Response({'status': 'marked as read'})


class ChatViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Chat model.
    """
    serializer_class = ChatSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Filter chats to only show user's chats.
        """
        return Chat.objects.filter(participants=self.request.user)

    def perform_create(self, serializer):
        chat = serializer.save()
        chat.participants.add(self.request.user)

    @action(detail=True, methods=['get'])
    @extend_schema(
        summary="Get chat messages",
        description="Get messages for a chat (paginated).",
        responses={200: MessageSerializer(many=True)}
    )
    def messages(self, request, pk=None):
        """
        Get messages for a chat (paginated).
        """
        chat = self.get_object()
        messages = chat.messages.all().order_by('-created_at') # Newest first for pagination usually
        page = self.paginate_queryset(messages)
        if page is not None:
            serializer = MessageSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    @extend_schema(
        summary="Mark chat read",
        description="Mark all messages in a chat as read.",
        responses={200: OpenApiTypes.OBJECT}
    )
    def mark_read(self, request, pk=None):
        """
        Mark all messages in a chat as read.
        """
        chat = self.get_object()
        Message.objects.filter(
            chat=chat,
            is_read=False
        ).exclude(sender=request.user).update(is_read=True)
        
        return Response({'status': 'messages marked as read'})

    @action(detail=True, methods=['post'], url_path='share-reel')
    @extend_schema(
        summary="Share reel",
        description="Share a reel in the chat.",
        request=OpenApiTypes.OBJECT,
        parameters=[
            OpenApiParameter(
                name='reel_id',
                description='ID of the reel to share',
                required=True,
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY
            )
        ],
        responses={201: MessageSerializer}
    )
    def share_reel(self, request, pk=None):
        """
        Share a reel in the chat.
        """
        chat = self.get_object()
        reel_id = request.data.get('reel_id')
        
        try:
            reel = Reel.objects.get(id=reel_id)
        except Reel.DoesNotExist:
            return Response({'error': 'Reel not found'}, status=status.HTTP_404_NOT_FOUND)
            
        # Create a message with type 'reel' and content as reel ID or link
        message = Message.objects.create(
            chat=chat,
            sender=request.user,
            message_type='reel',
            content=str(reel.id) # Storing ID in content for simplicity
        )
        
        return Response(MessageSerializer(message).data, status=status.HTTP_201_CREATED)
