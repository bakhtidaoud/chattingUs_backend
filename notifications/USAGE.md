# Notification System Usage Guide

## Overview

The ChattingUs notification system provides comprehensive notification functionality including:
- In-app notifications
- Real-time WebSocket notifications
- Push notifications via Firebase Cloud Messaging (FCM)
- Email notifications
- User-configurable notification preferences
- Grouped notifications for better UX

## Installation & Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Apply Migrations

```bash
python manage.py migrate notifications
```

### 3. Create Notification Preferences for Existing Users

If you have existing users, create notification preferences for them:

```bash
python manage.py shell
```

```python
from users.models import User
from notifications.models import NotificationPreference

for user in User.objects.all():
    NotificationPreference.objects.get_or_create(user=user)
```

### 4. Start Celery Worker (Optional but Recommended)

For async notification processing:

```bash
# Start Celery worker
celery -A chattingus_backend worker -l info

# Start Celery beat for scheduled tasks (optional)
celery -A chattingus_backend beat -l info
```

## API Endpoints

### Notifications

#### List All Notifications
```http
GET /api/notifications/
```

Query Parameters:
- `is_read` (boolean): Filter by read status (true/false)
- `type` (string): Filter by notification type (like, comment, follow, message, mention)
- `page` (int): Page number for pagination
- `page_size` (int): Number of items per page (max 100)

Response:
```json
{
  "count": 50,
  "next": "http://localhost:8000/api/notifications/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "recipient": 2,
      "sender": 3,
      "sender_username": "john_doe",
      "sender_profile_picture": "http://localhost:8000/media/profile_pictures/john.jpg",
      "sender_full_name": "John Doe",
      "notification_type": "like",
      "text": "John Doe liked your post",
      "link": "/posts/123/",
      "content_type": 10,
      "object_id": 123,
      "content_object_data": {
        "type": "post",
        "id": 123,
        "caption": "Amazing sunset...",
        "image": "http://localhost:8000/media/posts/sunset.jpg"
      },
      "is_read": false,
      "created_at": "2025-12-04T10:30:00Z",
      "time_ago": "2h ago"
    }
  ]
}
```

#### Get Single Notification
```http
GET /api/notifications/{id}/
```

#### Mark Notification as Read
```http
PUT /api/notifications/{id}/read/
```

Response:
```json
{
  "id": 1,
  "is_read": true,
  ...
}
```

#### Mark All Notifications as Read
```http
PUT /api/notifications/read-all/
```

Response:
```json
{
  "status": "all notifications marked as read",
  "updated_count": 15
}
```

#### Delete Notification
```http
DELETE /api/notifications/{id}/
```

Response: 204 No Content

#### Get Unread Count
```http
GET /api/notifications/unread-count/
```

Response:
```json
{
  "unread_count": 5
}
```

#### Get Grouped Notifications
```http
GET /api/notifications/grouped/
```

Query Parameters:
- `limit` (int): Number of notifications to group (default: 50)

Response:
```json
[
  {
    "notification_type": "like",
    "count": 3,
    "is_read": false,
    "latest_created_at": "2025-12-04T10:30:00Z",
    "text": "John Doe and 2 others liked your post",
    "content_object_data": {
      "type": "post",
      "id": 123,
      "caption": "Amazing sunset...",
      "image": "http://localhost:8000/media/posts/sunset.jpg"
    },
    "notifications": [...]
  }
]
```

### Notification Preferences

#### Get User Preferences
```http
GET /api/notifications/preferences/
```

Response:
```json
{
  "id": 1,
  "user": 2,
  "like_push": true,
  "like_email": false,
  "like_in_app": true,
  "comment_push": true,
  "comment_email": true,
  "comment_in_app": true,
  "follow_push": true,
  "follow_email": false,
  "follow_in_app": true,
  "message_push": true,
  "message_email": false,
  "message_in_app": true,
  "mention_push": true,
  "mention_email": true,
  "mention_in_app": true,
  "fcm_tokens": ["token1", "token2"],
  "created_at": "2025-12-01T10:00:00Z",
  "updated_at": "2025-12-04T10:30:00Z"
}
```

#### Update Preferences
```http
PUT /api/notifications/preferences/{id}/
```

Request Body:
```json
{
  "like_push": false,
  "comment_email": true
}
```

#### Add FCM Token
```http
POST /api/notifications/preferences/add-fcm-token/
```

Request Body:
```json
{
  "token": "fcm_device_token_here"
}
```

#### Remove FCM Token
```http
POST /api/notifications/preferences/remove-fcm-token/
```

Request Body:
```json
{
  "token": "fcm_device_token_here"
}
```

## WebSocket Connection

### Connect to Notifications Stream

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/notifications/');

ws.onopen = () => {
  console.log('Connected to notifications');
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('New notification:', data.notification);
  
  // Update UI with new notification
  displayNotification(data.notification);
};

ws.onclose = () => {
  console.log('Disconnected from notifications');
};
```

## Creating Notifications in Code

### Basic Usage

```python
from notifications.utils import notify_user
from posts.models import Post

# When a user likes a post
post = Post.objects.get(id=123)
notify_user(
    recipient=post.author,
    notification_type='like',
    sender=request.user,
    content_object=post
)
```

### Advanced Usage with All Channels

```python
from notifications.utils import notify_user
from posts.models import Post, Comment

# When a user comments on a post
comment = Comment.objects.get(id=456)
notification = notify_user(
    recipient=comment.post.author,
    notification_type='comment',
    sender=request.user,
    content_object=comment
)

# The notify_user function will automatically:
# 1. Create the notification in the database
# 2. Send real-time notification via WebSocket
# 3. Send push notification if enabled
# 4. Send email notification if enabled
```

### Manual Control

```python
from notifications.utils import (
    create_notification,
    send_push_notification,
    send_email_notification,
    send_realtime_notification
)

# Create notification only
notification = create_notification(
    recipient=user,
    notification_type='follow',
    sender=request.user,
    content_object=request.user
)

# Send through specific channels
if notification:
    send_realtime_notification(notification)
    
    # Send push if user has tokens
    if user.notification_preferences.fcm_tokens:
        send_push_notification(
            notification,
            user.notification_preferences.fcm_tokens
        )
```

## Integration Examples

### Posts App - Like Notification

```python
# In posts/views.py
from notifications.utils import notify_user

class PostLikeView(APIView):
    def post(self, request, pk):
        post = Post.objects.get(id=pk)
        
        # Create like
        like, created = Like.objects.get_or_create(
            post=post,
            user=request.user
        )
        
        if created:
            # Send notification
            notify_user(
                recipient=post.author,
                notification_type='like',
                sender=request.user,
                content_object=post
            )
        
        return Response({'status': 'liked'})
```

### Posts App - Comment Notification

```python
# In posts/views.py
from notifications.utils import notify_user

class CommentCreateView(APIView):
    def post(self, request, post_id):
        post = Post.objects.get(id=post_id)
        
        # Create comment
        comment = Comment.objects.create(
            post=post,
            author=request.user,
            text=request.data['text']
        )
        
        # Notify post author
        notify_user(
            recipient=post.author,
            notification_type='comment',
            sender=request.user,
            content_object=comment
        )
        
        return Response(CommentSerializer(comment).data)
```

### Users App - Follow Notification

```python
# In users/views.py
from notifications.utils import notify_user

class FollowUserView(APIView):
    def post(self, request, username):
        user_to_follow = User.objects.get(username=username)
        
        # Create follow
        follow, created = Follow.objects.get_or_create(
            follower=request.user,
            following=user_to_follow
        )
        
        if created:
            # Send notification
            notify_user(
                recipient=user_to_follow,
                notification_type='follow',
                sender=request.user,
                content_object=request.user
            )
        
        return Response({'status': 'following'})
```

### Chat App - Message Notification

```python
# In chat/consumers.py
from notifications.utils import notify_user

class ChatConsumer(AsyncWebsocketConsumer):
    async def receive(self, text_data):
        # ... save message ...
        
        # Send notification to recipient
        await self.send_notification_async(
            recipient=recipient_user,
            notification_type='message',
            sender=self.user,
            content_object=message
        )
    
    @database_sync_to_async
    def send_notification_async(self, recipient, notification_type, sender, content_object):
        notify_user(
            recipient=recipient,
            notification_type=notification_type,
            sender=sender,
            content_object=content_object
        )
```

## Testing

### Test Notification Creation

```python
from django.test import TestCase
from users.models import User
from posts.models import Post
from notifications.models import Notification
from notifications.utils import notify_user

class NotificationTestCase(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username='user1')
        self.user2 = User.objects.create_user(username='user2')
        self.post = Post.objects.create(author=self.user1, caption='Test')
    
    def test_create_like_notification(self):
        notification = notify_user(
            recipient=self.user1,
            notification_type='like',
            sender=self.user2,
            content_object=self.post
        )
        
        self.assertIsNotNone(notification)
        self.assertEqual(notification.recipient, self.user1)
        self.assertEqual(notification.sender, self.user2)
        self.assertEqual(notification.notification_type, 'like')
        self.assertEqual(notification.content_object, self.post)
```

### Test API Endpoints

```python
from rest_framework.test import APITestCase
from rest_framework import status

class NotificationAPITestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='test123')
        self.client.force_authenticate(user=self.user)
    
    def test_list_notifications(self):
        response = self.client.get('/api/notifications/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_mark_notification_read(self):
        notification = Notification.objects.create(
            recipient=self.user,
            notification_type='like'
        )
        
        response = self.client.put(f'/api/notifications/{notification.id}/read/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        notification.refresh_from_db()
        self.assertTrue(notification.is_read)
```

## Troubleshooting

### Firebase Push Notifications Not Working

1. Verify Firebase credentials file exists:
   ```bash
   ls chattingus-c4b25-firebase-adminsdk-fbsvc-bd8023e7eb.json
   ```

2. Check Firebase initialization in logs:
   ```
   Firebase Admin SDK initialized successfully
   ```

3. Verify FCM tokens are registered:
   ```python
   user.notification_preferences.fcm_tokens
   ```

### WebSocket Notifications Not Received

1. Ensure Redis is running:
   ```bash
   redis-cli ping
   # Should return: PONG
   ```

2. Check WebSocket connection in browser console

3. Verify channel layer configuration in settings.py

### Email Notifications Not Sent

1. Check email backend configuration in settings.py
2. For development, use console backend:
   ```python
   EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
   ```
3. For production, configure SMTP settings in .env

## Performance Optimization

### Database Indexes

The Notification model includes indexes on:
- `(recipient, is_read, created_at)`
- `(recipient, notification_type, created_at)`

### Query Optimization

Always use `select_related` when querying notifications:

```python
notifications = Notification.objects.filter(
    recipient=user
).select_related('sender', 'content_type')
```

### Cleanup Old Notifications

Run periodic cleanup task:

```python
from notifications.tasks import cleanup_old_notifications

# Clean up notifications older than 30 days
cleanup_old_notifications.delay(days=30)
```

Or set up Celery Beat for automatic cleanup:

```python
# In settings.py
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'cleanup-old-notifications': {
        'task': 'notifications.tasks.cleanup_old_notifications',
        'schedule': crontab(hour=2, minute=0),  # Run daily at 2 AM
        'args': (30,)  # Keep 30 days
    },
}
```
