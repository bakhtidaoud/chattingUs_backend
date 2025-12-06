# FCM Token Registration Guide

## Overview

This guide explains how to get FCM (Firebase Cloud Messaging) tokens from your Flutter app and register them with the Django backend to enable push notifications.

## Backend API Endpoints (Already Implemented)

Your Django backend already has the necessary endpoints:

### 1. Add FCM Token
```
POST /api/notifications/preferences/add-fcm-token/
```

**Request Body:**
```json
{
  "token": "your-fcm-token-here"
}
```

**Headers:**
```
Authorization: Bearer <your-jwt-token>
Content-Type: application/json
```

**Response:**
```json
{
  "id": 1,
  "user": 1,
  "like_push": true,
  "comment_push": true,
  "follow_push": true,
  "message_push": true,
  "mention_push": true,
  "fcm_tokens": ["your-fcm-token-here"],
  ...
}
```

### 2. Remove FCM Token
```
POST /api/notifications/preferences/remove-fcm-token/
```

**Request Body:**
```json
{
  "token": "your-fcm-token-here"
}
```

---

## Flutter Implementation

### Step 1: Add Firebase Messaging Dependency

In your Flutter app's `pubspec.yaml`:

```yaml
dependencies:
  firebase_messaging: ^14.7.0
  firebase_core: ^2.24.0
```

### Step 2: Initialize Firebase in Flutter

In your `main.dart`:

```dart
import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await Firebase.initializeApp();
  runApp(MyApp());
}
```

### Step 3: Get FCM Token

Create a notification service in your Flutter app:

```dart
// lib/services/notification_service.dart
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

class NotificationService {
  final FirebaseMessaging _firebaseMessaging = FirebaseMessaging.instance;
  
  // Get FCM token
  Future<String?> getFCMToken() async {
    try {
      // Request permission first (iOS)
      NotificationSettings settings = await _firebaseMessaging.requestPermission(
        alert: true,
        badge: true,
        sound: true,
      );
      
      if (settings.authorizationStatus == AuthorizationStatus.authorized) {
        // Get the token
        String? token = await _firebaseMessaging.getToken();
        print('FCM Token: $token');
        return token;
      }
      
      return null;
    } catch (e) {
      print('Error getting FCM token: $e');
      return null;
    }
  }
  
  // Register token with Django backend
  Future<bool> registerFCMToken(String token, String jwtToken) async {
    try {
      final response = await http.post(
        Uri.parse('https://your-backend.com/api/notifications/preferences/add-fcm-token/'),
        headers: {
          'Authorization': 'Bearer $jwtToken',
          'Content-Type': 'application/json',
        },
        body: json.encode({
          'token': token,
        }),
      );
      
      if (response.statusCode == 200) {
        print('FCM token registered successfully');
        return true;
      } else {
        print('Failed to register FCM token: ${response.body}');
        return false;
      }
    } catch (e) {
      print('Error registering FCM token: $e');
      return false;
    }
  }
  
  // Unregister token (e.g., on logout)
  Future<bool> unregisterFCMToken(String token, String jwtToken) async {
    try {
      final response = await http.post(
        Uri.parse('https://your-backend.com/api/notifications/preferences/remove-fcm-token/'),
        headers: {
          'Authorization': 'Bearer $jwtToken',
          'Content-Type': 'application/json',
        },
        body: json.encode({
          'token': token,
        }),
      );
      
      return response.statusCode == 200;
    } catch (e) {
      print('Error unregistering FCM token: $e');
      return false;
    }
  }
  
  // Listen for token refresh
  void listenToTokenRefresh(Function(String) onTokenRefresh) {
    _firebaseMessaging.onTokenRefresh.listen((newToken) {
      print('FCM Token refreshed: $newToken');
      onTokenRefresh(newToken);
    });
  }
}
```

### Step 4: Register Token After Login

In your login controller or authentication service:

```dart
// After successful login
final notificationService = NotificationService();

// Get FCM token
String? fcmToken = await notificationService.getFCMToken();

if (fcmToken != null) {
  // Register with backend
  await notificationService.registerFCMToken(
    fcmToken,
    yourJwtToken, // Your JWT token from login
  );
}

// Listen for token refresh
notificationService.listenToTokenRefresh((newToken) async {
  await notificationService.registerFCMToken(newToken, yourJwtToken);
});
```

### Step 5: Handle Incoming Notifications

```dart
class NotificationService {
  // ... previous code ...
  
  // Setup notification handlers
  void setupNotificationHandlers() {
    // Handle notification when app is in foreground
    FirebaseMessaging.onMessage.listen((RemoteMessage message) {
      print('Got a message whilst in the foreground!');
      print('Message data: ${message.data}');
      
      if (message.notification != null) {
        print('Message also contained a notification: ${message.notification}');
        // Show local notification or update UI
      }
    });
    
    // Handle notification when app is in background but opened
    FirebaseMessaging.onMessageOpenedApp.listen((RemoteMessage message) {
      print('A new onMessageOpenedApp event was published!');
      // Navigate to specific screen based on notification data
      _handleNotificationTap(message.data);
    });
    
    // Check if app was opened from a notification
    FirebaseMessaging.instance.getInitialMessage().then((RemoteMessage? message) {
      if (message != null) {
        _handleNotificationTap(message.data);
      }
    });
  }
  
  void _handleNotificationTap(Map<String, dynamic> data) {
    // Navigate based on notification type
    String? notificationType = data['notification_type'];
    String? link = data['link'];
    
    if (notificationType == 'message') {
      // Navigate to chat screen
    } else if (notificationType == 'follow') {
      // Navigate to profile screen
    } else if (notificationType == 'comment') {
      // Navigate to post/story screen
    }
  }
}
```

### Step 6: Unregister on Logout

```dart
// In your logout function
final notificationService = NotificationService();
String? fcmToken = await notificationService.getFCMToken();

if (fcmToken != null) {
  await notificationService.unregisterFCMToken(fcmToken, yourJwtToken);
}
```

---

## Testing Push Notifications

### 1. Test from Django Admin or Shell

```python
from notifications.utils import notify_user
from users.models import User

# Get a user
user = User.objects.get(username='testuser')

# Send a test notification
notify_user(
    recipient=user,
    notification_type='message',
    sender=None,  # Can be None for system notifications
    content_object=None
)
```

### 2. Test via API

Use Postman or curl to create a follow/message/story reply, which will trigger the notification signals.

### 3. Check FCM Tokens

```python
from notifications.models import NotificationPreference

# Get user's preferences
prefs = NotificationPreference.objects.get(user__username='testuser')
print(prefs.fcm_tokens)
```

---

## Notification Payload Structure

When a notification is sent, the Flutter app receives:

```json
{
  "notification": {
    "title": "ChattingUs",
    "body": "username started following you",
    "image": "https://example.com/profile.jpg"
  },
  "data": {
    "notification_id": "123",
    "notification_type": "follow",
    "sender_id": "456",
    "link": "/profile/username/"
  }
}
```

---

## Troubleshooting

### FCM Token Not Received
- Check Firebase project configuration
- Ensure `google-services.json` (Android) or `GoogleService-Info.plist` (iOS) is properly added
- Verify Firebase Cloud Messaging is enabled in Firebase Console

### Notifications Not Sent
- Check if FCM tokens are registered: `GET /api/notifications/preferences/`
- Verify Firebase Admin SDK credentials are configured in Django settings
- Check Django logs for FCM errors
- Ensure user has push notifications enabled in preferences

### Token Refresh Issues
- Implement `onTokenRefresh` listener to handle token updates
- Re-register new tokens with the backend immediately

---

## Summary

1. ✅ Backend endpoints are already implemented
2. 📱 Get FCM token in Flutter using `firebase_messaging`
3. 🔐 Send token to backend with JWT authentication
4. 🔔 Handle incoming notifications in Flutter
5. 🚪 Unregister token on logout
6. 🔄 Listen for token refresh and update backend

The notification system will automatically send push notifications when:
- Someone follows the user
- Someone sends a message
- Someone replies to a story
- Someone comments on a post
- Someone mentions the user
