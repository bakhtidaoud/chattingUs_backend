from celery import shared_task
from .models import Reel
from .utils import process_video

@shared_task
def process_reel_upload(reel_id):
    """
    Background task to process uploaded reel video.
    """
    try:
        reel = Reel.objects.get(id=reel_id)
        process_video(reel)
        return f"Processed reel {reel_id}"
    except Reel.DoesNotExist:
        return f"Reel {reel_id} not found"
    except Exception as e:
        return f"Error processing reel {reel_id}: {e}"
