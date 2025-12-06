# Global Search API Documentation

## Overview

The ChattingUs API provides a comprehensive search endpoint that allows you to search across users, posts, reels, and hashtags with a single API call.

## Endpoint

```
GET /api/explore/search/
```

## Authentication

- **Optional**: The endpoint works for both authenticated and unauthenticated users
- **Search History**: Only saved for authenticated users

## Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `q` | string | **Yes** | - | Search query string |
| `type` | string | No | `all` | Type of content to search: `all`, `users`, `posts`, `reels`, `hashtags` |
| `limit` | integer | No | `10` | Number of results per type (min: 1, max: 50) |

## Search Fields

### Users
Searches in the following fields:
- `username`
- `first_name`
- `last_name`
- `bio`

**Ordering**: Verified users first, then by most recent

### Posts
Searches in the following fields:
- `caption`
- `location`

**Ordering**: Most recent first

### Reels
Searches in the following fields:
- `caption`

**Ordering**: Most recent first

### Hashtags
Searches in the following fields:
- `name`

**Ordering**: By popularity (posts_count + reels_count)

## Response Format

```json
{
  "users": [
    {
      "id": 1,
      "username": "john_doe",
      "first_name": "John",
      "last_name": "Doe",
      "bio": "Software engineer who loves coding",
      "profile_picture": "https://example.com/media/profile.jpg",
      "is_verified": true,
      "is_private": false
    }
  ],
  "posts": [
    {
      "id": 1,
      "user": {
        "id": 1,
        "username": "john_doe",
        "profile_picture": "https://example.com/media/profile.jpg"
      },
      "image": "https://example.com/media/posts/image.jpg",
      "caption": "Learning to code in Python",
      "location": "New York",
      "likes_count": 42,
      "comments_count": 5,
      "created_at": "2025-12-05T01:00:00Z"
    }
  ],
  "reels": [
    {
      "id": 1,
      "user": {
        "id": 3,
        "username": "coding_master",
        "profile_picture": "https://example.com/media/profile.jpg"
      },
      "video": "https://example.com/media/reels/video.mp4",
      "thumbnail": "https://example.com/media/reels/thumb.jpg",
      "caption": "Quick coding tutorial",
      "likes_count": 100,
      "views_count": 500,
      "created_at": "2025-12-05T02:00:00Z"
    }
  ],
  "hashtags": [
    {
      "id": 1,
      "name": "coding",
      "posts_count": 150,
      "reels_count": 75
    }
  ]
}
```

## Examples

### 1. Search All Content Types

```bash
GET /api/explore/search/?q=coding
```

Returns users, posts, reels, and hashtags matching "coding"

### 2. Search Only Users

```bash
GET /api/explore/search/?q=john&type=users
```

Returns only users with "john" in username, first_name, last_name, or bio

### 3. Search with Custom Limit

```bash
GET /api/explore/search/?q=python&type=posts&limit=20
```

Returns up to 20 posts containing "python" in caption or location

### 4. Search for Location

```bash
GET /api/explore/search/?q=New%20York&type=posts
```

Returns posts with "New York" in caption or location

### 5. Empty Query

```bash
GET /api/explore/search/?q=
```

Returns empty results for all types:
```json
{
  "users": [],
  "posts": [],
  "reels": [],
  "hashtags": []
}
```

## Flutter/Dart Integration

### Example Service Method

```dart
import 'package:http/http.dart' as http;
import 'dart:convert';

class SearchService {
  final String baseUrl = 'https://your-api.com';
  
  Future<Map<String, dynamic>> search({
    required String query,
    String type = 'all',
    int limit = 10,
    String? jwtToken,
  }) async {
    final uri = Uri.parse('$baseUrl/api/explore/search/').replace(
      queryParameters: {
        'q': query,
        'type': type,
        'limit': limit.toString(),
      },
    );
    
    final headers = {
      'Content-Type': 'application/json',
      if (jwtToken != null) 'Authorization': 'Bearer $jwtToken',
    };
    
    final response = await http.get(uri, headers: headers);
    
    if (response.statusCode == 200) {
      return json.decode(response.body);
    } else {
      throw Exception('Failed to search: ${response.body}');
    }
  }
  
  // Search only users
  Future<List<dynamic>> searchUsers(String query, {String? jwtToken}) async {
    final results = await search(
      query: query,
      type: 'users',
      limit: 20,
      jwtToken: jwtToken,
    );
    return results['users'] ?? [];
  }
  
  // Search only posts
  Future<List<dynamic>> searchPosts(String query, {String? jwtToken}) async {
    final results = await search(
      query: query,
      type: 'posts',
      limit: 20,
      jwtToken: jwtToken,
    );
    return results['posts'] ?? [];
  }
  
  // Search only reels
  Future<List<dynamic>> searchReels(String query, {String? jwtToken}) async {
    final results = await search(
      query: query,
      type: 'reels',
      limit: 20,
      jwtToken: jwtToken,
    );
    return results['reels'] ?? [];
  }
}
```

### Example Usage in Flutter

```dart
final searchService = SearchService();

// Search all content
final results = await searchService.search(
  query: 'coding',
  jwtToken: yourJwtToken,
);

print('Found ${results['users'].length} users');
print('Found ${results['posts'].length} posts');
print('Found ${results['reels'].length} reels');

// Search only users
final users = await searchService.searchUsers('john', jwtToken: yourJwtToken);
for (var user in users) {
  print('${user['username']}: ${user['bio']}');
}
```

## Search History

For authenticated users, all search queries are automatically saved to search history. This can be used to:
- Show recent searches
- Provide search suggestions
- Analyze user behavior

## Performance Considerations

1. **Query Optimization**: The API uses `select_related()` for efficient database queries
2. **Limit Parameter**: Use appropriate limits to balance between results and performance
3. **Specific Type Search**: When you know what you're looking for, use the `type` parameter to search only that content type
4. **Caching**: Consider implementing client-side caching for frequently searched terms

## Rate Limiting

- Standard rate limits apply (check your API rate limit configuration)
- Consider implementing debouncing on the client side for search-as-you-type features

## Related Endpoints

- `GET /api/explore/trending/` - Get trending content
- `GET /api/explore/` - Get explore feed
- `GET /api/hashtags/{name}/posts/` - Get posts for a specific hashtag
- `GET /api/hashtags/{name}/reels/` - Get reels for a specific hashtag

## Notes

- Search is case-insensitive
- Partial matches are supported (e.g., "cod" will match "coding")
- Results are ordered by relevance and recency
- Verified users appear first in user search results
- Private user profiles may have restricted visibility based on follow status
