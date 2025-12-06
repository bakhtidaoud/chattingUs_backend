"""
Video processing utilities using FFmpeg.
"""

import os
import subprocess
import logging
from PIL import Image
from django.core.files.base import ContentFile
from io import BytesIO

logger = logging.getLogger(__name__)

# Video settings
MAX_VIDEO_WIDTH = 1920
MAX_VIDEO_HEIGHT = 1080
VIDEO_CODEC = 'libx264'
AUDIO_CODEC = 'aac'
VIDEO_BITRATE = 'auto'  # Will be calculated based on resolution
CRF = 23  # Constant Rate Factor (18-28, lower is better quality)


def check_ffmpeg_installed() -> bool:
    """
    Check if FFmpeg is installed and available.
    
    Returns:
        bool: True if FFmpeg is available
    """
    try:
        subprocess.run(
            ['ffmpeg', '-version'],
            capture_output=True,
            check=True
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def get_video_metadata(video_path: str) -> dict:
    """
    Get video metadata using FFprobe.
    
    Args:
        video_path: Path to video file
    
    Returns:
        Dict with metadata (duration, width, height, etc.)
    """
    try:
        cmd = [
            'ffprobe',
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            '-show_streams',
            video_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        import json
        data = json.loads(result.stdout)
        
        # Find video stream
        video_stream = None
        for stream in data.get('streams', []):
            if stream.get('codec_type') == 'video':
                video_stream = stream
                break
        
        if not video_stream:
            return {}
        
        metadata = {
            'duration': float(data.get('format', {}).get('duration', 0)),
            'width': int(video_stream.get('width', 0)),
            'height': int(video_stream.get('height', 0)),
            'codec': video_stream.get('codec_name', ''),
            'bitrate': int(data.get('format', {}).get('bit_rate', 0)),
        }
        
        return metadata
    
    except Exception as e:
        logger.error(f"Error getting video metadata: {e}")
        return {}


def generate_video_thumbnail(video_path: str, time_offset: float = 1.0) -> BytesIO:
    """
    Generate thumbnail from video at specified time.
    
    Args:
        video_path: Path to video file
        time_offset: Time in seconds to extract frame
    
    Returns:
        BytesIO object containing thumbnail image
    """
    try:
        # Create temporary output file
        output_path = video_path + '_thumb.jpg'
        
        cmd = [
            'ffmpeg',
            '-ss', str(time_offset),
            '-i', video_path,
            '-vframes', '1',
            '-q:v', '2',
            '-y',
            output_path
        ]
        
        subprocess.run(cmd, capture_output=True, check=True)
        
        # Read the generated thumbnail
        with open(output_path, 'rb') as f:
            thumbnail_data = BytesIO(f.read())
        
        # Clean up temporary file
        os.remove(output_path)
        
        return thumbnail_data
    
    except Exception as e:
        logger.error(f"Error generating video thumbnail: {e}")
        raise


def compress_video(input_path: str, output_path: str, max_width: int = MAX_VIDEO_WIDTH) -> bool:
    """
    Compress and convert video to MP4.
    
    Args:
        input_path: Path to input video
        output_path: Path to output video
        max_width: Maximum width (height will be calculated to maintain aspect ratio)
    
    Returns:
        bool: True if successful
    """
    try:
        # Get video metadata
        metadata = get_video_metadata(input_path)
        width = metadata.get('width', 1920)
        height = metadata.get('height', 1080)
        
        # Calculate new dimensions maintaining aspect ratio
        if width > max_width:
            new_width = max_width
            new_height = int((max_width / width) * height)
            # Ensure even dimensions (required by some codecs)
            new_height = new_height - (new_height % 2)
            scale_filter = f'scale={new_width}:{new_height}'
        else:
            scale_filter = None
        
        # Build FFmpeg command
        cmd = [
            'ffmpeg',
            '-i', input_path,
            '-c:v', VIDEO_CODEC,
            '-crf', str(CRF),
            '-preset', 'medium',
            '-c:a', AUDIO_CODEC,
            '-b:a', '128k',
            '-movflags', '+faststart',  # Enable streaming
        ]
        
        if scale_filter:
            cmd.extend(['-vf', scale_filter])
        
        cmd.extend(['-y', output_path])
        
        # Run FFmpeg
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            logger.error(f"FFmpeg error: {result.stderr}")
            return False
        
        return True
    
    except Exception as e:
        logger.error(f"Error compressing video: {e}")
        return False


def convert_to_mp4(input_path: str, output_path: str) -> bool:
    """
    Convert video to MP4 format.
    
    Args:
        input_path: Path to input video
        output_path: Path to output MP4
    
    Returns:
        bool: True if successful
    """
    return compress_video(input_path, output_path)


def process_video(media_instance):
    """
    Process uploaded video: compress, convert to MP4, generate thumbnail.
    
    Args:
        media_instance: Media model instance
    
    Returns:
        bool: True if successful
    """
    try:
        # Check if FFmpeg is available
        if not check_ffmpeg_installed():
            logger.error("FFmpeg is not installed")
            media_instance.status = 'failed'
            media_instance.metadata['error'] = 'FFmpeg not installed'
            media_instance.save()
            return False
        
        # Get original file path
        original_path = media_instance.original_file.path
        
        # Get video metadata
        metadata = get_video_metadata(original_path)
        media_instance.duration = metadata.get('duration', 0)
        media_instance.width = metadata.get('width', 0)
        media_instance.height = metadata.get('height', 0)
        media_instance.metadata.update(metadata)
        
        # Generate thumbnail
        try:
            thumbnail_time = min(1.0, metadata.get('duration', 1.0) / 2)
            thumbnail_data = generate_video_thumbnail(original_path, thumbnail_time)
            
            filename = f"{os.path.splitext(os.path.basename(original_path))[0]}_thumb.jpg"
            media_instance.video_thumbnail.save(
                filename,
                ContentFile(thumbnail_data.read()),
                save=False
            )
        except Exception as e:
            logger.warning(f"Could not generate video thumbnail: {e}")
        
        # Compress video
        output_path = original_path + '_processed.mp4'
        
        if compress_video(original_path, output_path):
            # Save processed video
            with open(output_path, 'rb') as f:
                filename = f"{os.path.splitext(os.path.basename(original_path))[0]}_processed.mp4"
                media_instance.processed_video.save(
                    filename,
                    ContentFile(f.read()),
                    save=False
                )
            
            # Clean up temporary file
            os.remove(output_path)
        
        # Update status
        media_instance.status = 'ready'
        media_instance.save()
        
        logger.info(f"Successfully processed video {media_instance.id}")
        return True
    
    except Exception as e:
        logger.error(f"Error processing video {media_instance.id}: {e}")
        media_instance.status = 'failed'
        media_instance.metadata['error'] = str(e)
        media_instance.save()
        return False
