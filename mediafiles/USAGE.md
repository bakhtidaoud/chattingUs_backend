# Media Handling System - Usage Guide

## Overview

The media handling system provides comprehensive file upload and processing capabilities for images, videos, and audio files with:

- ✅ **Local File Storage** (easily switchable to S3)
- ✅ **Image Processing** - Multiple sizes, WebP conversion, compression
- ✅ **Video Processing** - MP4 conversion, compression, thumbnails
- ✅ **Audio Processing** - MP3 conversion, compression
- ✅ **Async Processing** with Celery
- ✅ **REST API** for upload, retrieve, delete

## Prerequisites

### FFmpeg Installation

Video and audio processing requires FFmpeg. Install it based on your OS:

#### Windows
```powershell
# Using Chocolatey
choco install ffmpeg

# Or download from: https://ffmpeg.org/download.html
# Add to PATH after installation
```

#### Linux
```bash
sudo apt-get update
sudo apt-get install ffmpeg
```

#### macOS
```bash
brew install ffmpeg
```

### Verify Installation
```bash
ffmpeg -version
```

## API Endpoints

### Upload Media

**Endpoint:** `POST /api/media/upload/`

**Headers:**
```
Authorization: Bearer YOUR_TOKEN
Content-Type: multipart/form-data
```

**Request:**
```bash
curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@/path/to/image.jpg" \
  http://localhost:8000/api/media/upload/
```

**Response:**
```json
{
  "id": 1,
  "user": 2,
  "user_username": "john_doe",
  "file_type": "image",
  "status": "processing",
  "file_size": 1048576,
  "mime_type": "image/jpeg",
  "display_url": "http://localhost:8000/media/user_2/image/1_photo.jpg",
  "thumbnail_url": "http://localhost:8000/media/thumbnails/photo_thumbnail.jpg",
  "urls": {
    "thumbnail": "http://localhost:8000/media/thumbnails/photo_thumbnail.jpg",
    "small": "http://localhost:8000/media/small/photo_small.jpg",
    "medium": "http://localhost:8000/media/medium/photo_medium.jpg",
    "large": "http://localhost:8000/media/large/photo_large.jpg",
    "webp": "http://localhost:8000/media/webp/photo_webp.webp",
    "original": "http://localhost:8000/media/user_2/image/1_photo.jpg"
  },
  "width": null,
  "height": null,
  "duration": null,
  "bitrate": null,
  "metadata": {},
  "is_public": true,
  "created_at": "2025-12-04T11:00:00Z",
  "updated_at": "2025-12-04T11:00:00Z"
}
```

### Get Media Details

**Endpoint:** `GET /api/media/{id}/`

**Response:**
```json
{
  "id": 1,
  "file_type": "image",
  "status": "ready",
  "display_url": "http://localhost:8000/media/medium/photo_medium.jpg",
  "thumbnail_url": "http://localhost:8000/media/thumbnails/photo_thumbnail.jpg",
  "urls": {
    "thumbnail": "...",
    "small": "...",
    "medium": "...",
    "large": "...",
    "webp": "...",
    "original": "..."
  },
  "width": 1920,
  "height": 1080,
  "created_at": "2025-12-04T11:00:00Z"
}
```

### List Media Files

**Endpoint:** `GET /api/media/`

**Query Parameters:**
- `type` - Filter by file type (image, video, audio)
- `status` - Filter by status (uploading, processing, ready, failed)
- `page` - Page number
- `page_size` - Items per page

**Example:**
```bash
GET /api/media/?type=image&status=ready&page=1&page_size=20
```

**Response:**
```json
{
  "count": 50,
  "next": "http://localhost:8000/api/media/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "file_type": "image",
      "status": "ready",
      "display_url": "...",
      "thumbnail_url": "...",
      "created_at": "2025-12-04T11:00:00Z"
    }
  ]
}
```

### Delete Media

**Endpoint:** `DELETE /api/media/{id}/`

**Response:** 204 No Content

### Reprocess Failed Media

**Endpoint:** `POST /api/media/{id}/reprocess/`

Retriggers processing for failed media files.

### Get Media Statistics

**Endpoint:** `GET /api/media/stats/`

**Response:**
```json
{
  "total": 150,
  "by_type": {
    "image": 100,
    "video": 40,
    "audio": 10
  },
  "by_status": {
    "ready": 145,
    "processing": 3,
    "failed": 2,
    "uploading": 0
  },
  "total_size": 524288000
}
```

## File Size Limits

- **Images:** 10 MB
- **Videos:** 100 MB
- **Audio:** 20 MB

## Supported Formats

### Images
- JPEG (.jpg, .jpeg)
- PNG (.png)
- GIF (.gif)
- WebP (.webp)
- BMP (.bmp)

### Videos
- MP4 (.mp4)
- QuickTime (.mov)
- AVI (.avi)
- MKV (.mkv)
- WebM (.webm)

### Audio
- MP3 (.mp3)
- WAV (.wav)
- OGG (.ogg)
- AAC (.aac)
- M4A (.m4a)

## Image Processing

When an image is uploaded, the following versions are automatically generated:

| Size | Dimensions | Description |
|------|------------|-------------|
| Thumbnail | 150x150 | Square crop |
| Small | 320x320 | Max dimension |
| Medium | 640x640 | Max dimension |
| Large | 1080x1080 | Max dimension |
| WebP | 640x640 | WebP format |

**Quality Settings:**
- JPEG: 85%
- WebP: 80%

## Video Processing

Videos are automatically:
1. Compressed to H.264 codec
2. Converted to MP4 format
3. Resized to max 1080p
4. Thumbnail extracted at 1 second (or middle of video)

**Settings:**
- Max resolution: 1920x1080
- Video codec: H.264
- Audio codec: AAC
- CRF: 23 (quality)

## Audio Processing

Audio files are automatically:
1. Converted to MP3 format
2. Compressed to 128kbps
3. Resampled to 44.1kHz

## Usage in Code

### Upload from Frontend

```javascript
// JavaScript/React example
const uploadMedia = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await fetch('http://localhost:8000/api/media/upload/', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`
    },
    body: formData
  });
  
  const data = await response.json();
  console.log('Media uploaded:', data);
  
  // Poll for processing status
  const checkStatus = setInterval(async () => {
    const statusResponse = await fetch(`http://localhost:8000/api/media/${data.id}/`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    
    const statusData = await statusResponse.json();
    
    if (statusData.status === 'ready') {
      clearInterval(checkStatus);
      console.log('Processing complete!', statusData);
      // Use statusData.urls to display different sizes
    } else if (statusData.status === 'failed') {
      clearInterval(checkStatus);
      console.error('Processing failed');
    }
  }, 2000);
};
```

### Reference Media in Models

```python
# In your models (e.g., posts/models.py)
from django.db import models
from mediafiles.models import Media

class Post(models.Model):
    author = models.ForeignKey('users.User', on_delete=models.CASCADE)
    caption = models.TextField()
    media = models.ForeignKey(Media, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

### Upload and Attach to Post

```python
# In your views
from mediafiles.models import Media
from mediafiles.serializers import MediaUploadSerializer

def create_post(request):
    # Upload media first
    media_serializer = MediaUploadSerializer(
        data={'file': request.FILES.get('image')},
        context={'request': request}
    )
    
    if media_serializer.is_valid():
        media = media_serializer.save()
        
        # Create post with media
        post = Post.objects.create(
            author=request.user,
            caption=request.data.get('caption'),
            media=media
        )
        
        # Trigger async processing
        from mediafiles.tasks import process_media_task
        process_media_task.delay(media.id)
        
        return Response({'post_id': post.id, 'media_id': media.id})
```

## Celery Configuration

### Start Celery Worker

```bash
# Terminal 1: Start Celery worker
celery -A chattingus_backend worker -l info

# Terminal 2: Start Celery beat (for scheduled cleanup)
celery -A chattingus_backend beat -l info
```

### Scheduled Tasks

Add to `settings.py` for automatic cleanup:

```python
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'cleanup-failed-uploads': {
        'task': 'mediafiles.tasks.cleanup_failed_uploads',
        'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
        'args': (7,)  # Keep failed uploads for 7 days
    },
}
```

## Troubleshooting

### FFmpeg Not Found

**Error:** `FFmpeg is not installed`

**Solution:**
1. Install FFmpeg (see Prerequisites)
2. Ensure it's in your PATH
3. Restart your Django server

### Processing Stuck

**Error:** Media status stays at "processing"

**Solution:**
1. Check Celery worker is running
2. Check Celery logs for errors
3. Try reprocessing: `POST /api/media/{id}/reprocess/`

### File Too Large

**Error:** `File size exceeds maximum allowed size`

**Solution:**
- Compress file before uploading
- Or increase limits in `mediafiles/utils/validators.py`

### Out of Disk Space

**Solution:**
1. Run cleanup task: `cleanup_failed_uploads.delay()`
2. Delete old media via admin
3. Implement automatic cleanup schedule

## Performance Tips

1. **Use Thumbnails:** Always use appropriate size for display
   ```javascript
   // Use thumbnail for lists
   <img src={media.urls.thumbnail} />
   
   // Use medium for detail view
   <img src={media.urls.medium} />
   ```

2. **Lazy Loading:** Load images progressively
   ```html
   <img src={media.urls.thumbnail} 
        data-src={media.urls.large} 
        loading="lazy" />
   ```

3. **WebP Format:** Use WebP for better compression
   ```html
   <picture>
     <source srcset={media.urls.webp} type="image/webp">
     <img src={media.urls.medium} alt="...">
   </picture>
   ```

4. **CDN:** Consider using a CDN for media delivery in production

## Switching to S3 (Future)

To switch to AWS S3 storage later:

1. Install boto3 and django-storages
2. Configure S3 settings in `settings.py`
3. Update `DEFAULT_FILE_STORAGE`
4. No code changes needed!

```python
# settings.py
INSTALLED_APPS += ['storages']

AWS_ACCESS_KEY_ID = 'your-key'
AWS_SECRET_ACCESS_KEY = 'your-secret'
AWS_STORAGE_BUCKET_NAME = 'your-bucket'
AWS_S3_REGION_NAME = 'us-east-1'

DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
```

## Admin Interface

Access the admin at `/admin/mediafiles/media/` to:
- View all uploaded media
- Filter by type, status, date
- Reprocess failed media
- Mark as public/private
- Delete media files

## Security Notes

1. **File Validation:** All files are validated for type and size
2. **User Isolation:** Users can only access their own media
3. **Public/Private:** Use `is_public` flag for access control
4. **Malware Scanning:** Consider adding virus scanning for production

## Next Steps

1. Integrate media upload into your Posts, Stories, Reels apps
2. Set up Celery workers for production
3. Configure automatic cleanup tasks
4. Consider CDN for better performance
5. Implement media galleries and albums
