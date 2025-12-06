"""
Celery tasks for media processing.
"""

from celery import shared_task
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


@shared_task
def process_image_task(media_id):
    """
    Process uploaded image asynchronously.
    
    Args:
        media_id: ID of the Media instance
    
    Returns:
        bool: True if successful
    """
    from .models import Media
    from .utils.image_processor import process_image
    
    try:
        media = Media.objects.get(id=media_id)
        
        if media.file_type != 'image':
            logger.error(f"Media {media_id} is not an image")
            return False
        
        media.status = 'processing'
        media.save()
        
        success = process_image(media)
        
        logger.info(f"Image processing task completed for media {media_id}: {success}")
        return success
    
    except Media.DoesNotExist:
        logger.error(f"Media {media_id} not found")
        return False
    except Exception as e:
        logger.error(f"Error in image processing task for media {media_id}: {e}")
        return False


@shared_task
def process_video_task(media_id):
    """
    Process uploaded video asynchronously.
    
    Args:
        media_id: ID of the Media instance
    
    Returns:
        bool: True if successful
    """
    from .models import Media
    from .utils.video_processor import process_video
    
    try:
        media = Media.objects.get(id=media_id)
        
        if media.file_type != 'video':
            logger.error(f"Media {media_id} is not a video")
            return False
        
        media.status = 'processing'
        media.save()
        
        success = process_video(media)
        
        logger.info(f"Video processing task completed for media {media_id}: {success}")
        return success
    
    except Media.DoesNotExist:
        logger.error(f"Media {media_id} not found")
        return False
    except Exception as e:
        logger.error(f"Error in video processing task for media {media_id}: {e}")
        return False


@shared_task
def process_audio_task(media_id):
    """
    Process uploaded audio asynchronously.
    
    Args:
        media_id: ID of the Media instance
    
    Returns:
        bool: True if successful
    """
    from .models import Media
    from .utils.audio_processor import process_audio
    
    try:
        media = Media.objects.get(id=media_id)
        
        if media.file_type != 'audio':
            logger.error(f"Media {media_id} is not audio")
            return False
        
        media.status = 'processing'
        media.save()
        
        success = process_audio(media)
        
        logger.info(f"Audio processing task completed for media {media_id}: {success}")
        return success
    
    except Media.DoesNotExist:
        logger.error(f"Media {media_id} not found")
        return False
    except Exception as e:
        logger.error(f"Error in audio processing task for media {media_id}: {e}")
        return False


@shared_task
def cleanup_failed_uploads(days=7):
    """
    Clean up failed uploads older than specified days.
    
    Args:
        days: Number of days to keep failed uploads
    
    Returns:
        int: Number of deleted media files
    """
    from .models import Media
    
    try:
        cutoff_date = timezone.now() - timedelta(days=days)
        
        failed_media = Media.objects.filter(
            status='failed',
            created_at__lt=cutoff_date
        )
        
        count = failed_media.count()
        
        # Delete all failed uploads
        for media in failed_media:
            media.delete()
        
        logger.info(f"Cleaned up {count} failed uploads older than {days} days")
        return count
    
    except Exception as e:
        logger.error(f"Error cleaning up failed uploads: {e}")
        return 0


@shared_task
def cleanup_orphaned_media(days=30):
    """
    Clean up media files not referenced by any model.
    This is a placeholder - implement based on your specific needs.
    
    Args:
        days: Number of days to keep orphaned media
    
    Returns:
        int: Number of deleted media files
    """
    from .models import Media
    
    try:
        # This is a basic implementation
        # You might want to check if media is referenced by posts, stories, etc.
        
        cutoff_date = timezone.now() - timedelta(days=days)
        
        # Find media that might be orphaned
        # This is just an example - customize based on your needs
        old_media = Media.objects.filter(
            created_at__lt=cutoff_date,
            is_public=False
        )
        
        count = 0
        for media in old_media:
            # Add your logic here to check if media is still referenced
            # For now, we'll just log it
            logger.info(f"Found potentially orphaned media: {media.id}")
            # media.delete()
            # count += 1
        
        logger.info(f"Checked {old_media.count()} old media files")
        return count
    
    except Exception as e:
        logger.error(f"Error cleaning up orphaned media: {e}")
        return 0


@shared_task
def process_media_task(media_id):
    """
    Generic media processing task that routes to specific processor.
    
    Args:
        media_id: ID of the Media instance
    
    Returns:
        bool: True if successful
    """
    from .models import Media
    
    try:
        media = Media.objects.get(id=media_id)
        
        if media.file_type == 'image':
            return process_image_task(media_id)
        elif media.file_type == 'video':
            return process_video_task(media_id)
        elif media.file_type == 'audio':
            return process_audio_task(media_id)
        else:
            logger.error(f"Unknown file type for media {media_id}: {media.file_type}")
            return False
    
    except Media.DoesNotExist:
        logger.error(f"Media {media_id} not found")
        return False
    except Exception as e:
        logger.error(f"Error in media processing task for media {media_id}: {e}")
        return False
