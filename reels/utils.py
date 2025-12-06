import os
from django.conf import settings
from moviepy import VideoFileClip
from django.core.files.base import ContentFile
from io import BytesIO
from PIL import Image

def process_video(reel_instance):
    """
    Process the uploaded video:
    - Check duration (max 90s)
    - Generate thumbnail
    - Extract audio info (placeholder for now)
    """
    video_path = reel_instance.video.path
    
    try:
        clip = VideoFileClip(video_path)
        
        # 1. Update Duration
        duration = int(clip.duration)
        if duration > 90:
            # Optionally trim or raise error. For now, we just record it.
            # In a real app, we might want to trim it.
            pass
        reel_instance.duration = duration
        
        # 2. Generate Thumbnail
        thumbnail_path = f"reels/thumbnails/{reel_instance.id}_thumb.jpg"
        # Get frame at 1 second or middle if shorter
        t = 1 if duration > 1 else duration / 2
        frame = clip.get_frame(t)
        image = Image.fromarray(frame)
        
        thumb_io = BytesIO()
        image.save(thumb_io, format='JPEG', quality=85)
        
        reel_instance.thumbnail.save(f"{reel_instance.id}_thumb.jpg", ContentFile(thumb_io.getvalue()), save=False)
        
        # 3. Audio (Placeholder)
        # In a real app, we'd use audio analysis or separate track upload
        reel_instance.audio = "Original Audio"
        
        reel_instance.save()
        
        clip.close()
        return True
    except Exception as e:
        print(f"Error processing video for reel {reel_instance.id}: {e}")
        return False
