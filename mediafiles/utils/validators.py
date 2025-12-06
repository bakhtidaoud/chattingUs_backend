"""
File validation utilities for media uploads.
"""

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile
import mimetypes


# File size limits (in bytes)
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10 MB
MAX_VIDEO_SIZE = 100 * 1024 * 1024  # 100 MB
MAX_AUDIO_SIZE = 20 * 1024 * 1024  # 20 MB

# Allowed MIME types
ALLOWED_IMAGE_TYPES = [
    'image/jpeg',
    'image/png',
    'image/gif',
    'image/webp',
    'image/bmp',
]

ALLOWED_VIDEO_TYPES = [
    'video/mp4',
    'video/quicktime',
    'video/x-msvideo',
    'video/x-matroska',
    'video/webm',
]

ALLOWED_AUDIO_TYPES = [
    'audio/mpeg',
    'audio/mp3',
    'audio/wav',
    'audio/ogg',
    'audio/aac',
    'audio/x-m4a',
]


def validate_file_size(file: UploadedFile, max_size: int) -> None:
    """
    Validate file size.
    
    Args:
        file: Uploaded file
        max_size: Maximum size in bytes
    
    Raises:
        ValidationError: If file is too large
    """
    if file.size > max_size:
        max_size_mb = max_size / (1024 * 1024)
        raise ValidationError(
            f'File size exceeds maximum allowed size of {max_size_mb:.1f} MB'
        )


def validate_file_type(file: UploadedFile, allowed_types: list) -> None:
    """
    Validate file MIME type.
    
    Args:
        file: Uploaded file
        allowed_types: List of allowed MIME types
    
    Raises:
        ValidationError: If file type is not allowed
    """
    # Get MIME type from file
    mime_type = file.content_type
    
    # Also try to guess from filename
    if not mime_type:
        mime_type, _ = mimetypes.guess_type(file.name)
    
    if mime_type not in allowed_types:
        raise ValidationError(
            f'File type "{mime_type}" is not allowed. '
            f'Allowed types: {", ".join(allowed_types)}'
        )


def validate_image(file: UploadedFile) -> None:
    """
    Validate image file.
    
    Args:
        file: Uploaded image file
    
    Raises:
        ValidationError: If validation fails
    """
    validate_file_size(file, MAX_IMAGE_SIZE)
    validate_file_type(file, ALLOWED_IMAGE_TYPES)
    
    # Additional validation: Try to open with Pillow
    try:
        from PIL import Image
        img = Image.open(file)
        img.verify()
        
        # Reset file pointer
        file.seek(0)
    except Exception as e:
        raise ValidationError(f'Invalid image file: {str(e)}')


def validate_video(file: UploadedFile) -> None:
    """
    Validate video file.
    
    Args:
        file: Uploaded video file
    
    Raises:
        ValidationError: If validation fails
    """
    validate_file_size(file, MAX_VIDEO_SIZE)
    validate_file_type(file, ALLOWED_VIDEO_TYPES)


def validate_audio(file: UploadedFile) -> None:
    """
    Validate audio file.
    
    Args:
        file: Uploaded audio file
    
    Raises:
        ValidationError: If validation fails
    """
    validate_file_size(file, MAX_AUDIO_SIZE)
    validate_file_type(file, ALLOWED_AUDIO_TYPES)


def get_file_type(file: UploadedFile) -> str:
    """
    Determine file type from MIME type.
    
    Args:
        file: Uploaded file
    
    Returns:
        str: 'image', 'video', or 'audio'
    
    Raises:
        ValidationError: If file type cannot be determined
    """
    mime_type = file.content_type
    
    if not mime_type:
        mime_type, _ = mimetypes.guess_type(file.name)
    
    if not mime_type:
        raise ValidationError('Could not determine file type')
    
    if mime_type in ALLOWED_IMAGE_TYPES:
        return 'image'
    elif mime_type in ALLOWED_VIDEO_TYPES:
        return 'video'
    elif mime_type in ALLOWED_AUDIO_TYPES:
        return 'audio'
    else:
        raise ValidationError(f'Unsupported file type: {mime_type}')


def validate_media_file(file: UploadedFile) -> str:
    """
    Validate media file and return its type.
    
    Args:
        file: Uploaded file
    
    Returns:
        str: File type ('image', 'video', or 'audio')
    
    Raises:
        ValidationError: If validation fails
    """
    file_type = get_file_type(file)
    
    if file_type == 'image':
        validate_image(file)
    elif file_type == 'video':
        validate_video(file)
    elif file_type == 'audio':
        validate_audio(file)
    
    return file_type
