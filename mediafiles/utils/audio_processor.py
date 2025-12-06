"""
Audio processing utilities using FFmpeg.
"""

import os
import subprocess
import logging
from django.core.files.base import ContentFile

logger = logging.getLogger(__name__)

# Audio settings
AUDIO_BITRATE = '128k'
AUDIO_SAMPLE_RATE = 44100
AUDIO_CODEC = 'libmp3lame'


def get_audio_metadata(audio_path: str) -> dict:
    """
    Get audio metadata using FFprobe.
    
    Args:
        audio_path: Path to audio file
    
    Returns:
        Dict with metadata (duration, bitrate, etc.)
    """
    try:
        cmd = [
            'ffprobe',
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            '-show_streams',
            audio_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        import json
        data = json.loads(result.stdout)
        
        # Find audio stream
        audio_stream = None
        for stream in data.get('streams', []):
            if stream.get('codec_type') == 'audio':
                audio_stream = stream
                break
        
        if not audio_stream:
            return {}
        
        metadata = {
            'duration': float(data.get('format', {}).get('duration', 0)),
            'bitrate': int(data.get('format', {}).get('bit_rate', 0)) // 1000,  # Convert to kbps
            'codec': audio_stream.get('codec_name', ''),
            'sample_rate': int(audio_stream.get('sample_rate', 0)),
            'channels': int(audio_stream.get('channels', 0)),
        }
        
        return metadata
    
    except Exception as e:
        logger.error(f"Error getting audio metadata: {e}")
        return {}


def compress_audio(input_path: str, output_path: str, bitrate: str = AUDIO_BITRATE) -> bool:
    """
    Compress audio file to MP3.
    
    Args:
        input_path: Path to input audio
        output_path: Path to output audio
        bitrate: Target bitrate (e.g., '128k', '192k')
    
    Returns:
        bool: True if successful
    """
    try:
        cmd = [
            'ffmpeg',
            '-i', input_path,
            '-c:a', AUDIO_CODEC,
            '-b:a', bitrate,
            '-ar', str(AUDIO_SAMPLE_RATE),
            '-y',
            output_path
        ]
        
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
        logger.error(f"Error compressing audio: {e}")
        return False


def convert_to_mp3(input_path: str, output_path: str) -> bool:
    """
    Convert audio to MP3 format.
    
    Args:
        input_path: Path to input audio
        output_path: Path to output MP3
    
    Returns:
        bool: True if successful
    """
    return compress_audio(input_path, output_path)


def process_audio(media_instance):
    """
    Process uploaded audio: compress and convert to MP3.
    
    Args:
        media_instance: Media model instance
    
    Returns:
        bool: True if successful
    """
    try:
        # Get original file path
        original_path = media_instance.original_file.path
        
        # Get audio metadata
        metadata = get_audio_metadata(original_path)
        media_instance.duration = metadata.get('duration', 0)
        media_instance.bitrate = metadata.get('bitrate', 0)
        media_instance.metadata.update(metadata)
        
        # Compress audio
        output_path = original_path + '_processed.mp3'
        
        if compress_audio(original_path, output_path):
            # Save processed audio
            with open(output_path, 'rb') as f:
                filename = f"{os.path.splitext(os.path.basename(original_path))[0]}_processed.mp3"
                media_instance.processed_audio.save(
                    filename,
                    ContentFile(f.read()),
                    save=False
                )
            
            # Clean up temporary file
            os.remove(output_path)
        
        # Update status
        media_instance.status = 'ready'
        media_instance.save()
        
        logger.info(f"Successfully processed audio {media_instance.id}")
        return True
    
    except Exception as e:
        logger.error(f"Error processing audio {media_instance.id}: {e}")
        media_instance.status = 'failed'
        media_instance.metadata['error'] = str(e)
        media_instance.save()
        return False
