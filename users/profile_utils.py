"""
Utility functions for user profile management.
"""

from PIL import Image
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile
import sys


def compress_image(image, max_size=(800, 800), quality=85):
    """
    Compress and resize an image for profile pictures.
    
    Args:
        image: Uploaded image file
        max_size: Maximum dimensions (width, height)
        quality: JPEG quality (1-100)
    
    Returns:
        Compressed image file
    """
    # Open the image
    img = Image.open(image)
    
    # Convert RGBA to RGB if necessary
    if img.mode in ('RGBA', 'LA', 'P'):
        background = Image.new('RGB', img.size, (255, 255, 255))
        background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
        img = background
    
    # Resize image while maintaining aspect ratio
    img.thumbnail(max_size, Image.Resampling.LANCZOS)
    
    # Save to BytesIO
    output = BytesIO()
    img.save(output, format='JPEG', quality=quality, optimize=True)
    output.seek(0)
    
    # Create InMemoryUploadedFile
    compressed_image = InMemoryUploadedFile(
        output,
        'ImageField',
        f"{image.name.split('.')[0]}.jpg",
        'image/jpeg',
        sys.getsizeof(output),
        None
    )
    
    return compressed_image


def validate_username(username):
    """
    Validate username format.
    
    Rules:
    - Alphanumeric characters, underscores, and periods only
    - 3-30 characters
    - Cannot start or end with period or underscore
    - Cannot have consecutive periods or underscores
    """
    import re
    
    if not username:
        return False, "Username is required."
    
    if len(username) < 3 or len(username) > 30:
        return False, "Username must be between 3 and 30 characters."
    
    if not re.match(r'^[a-zA-Z0-9._]+$', username):
        return False, "Username can only contain letters, numbers, periods, and underscores."
    
    if username[0] in '._' or username[-1] in '._':
        return False, "Username cannot start or end with a period or underscore."
    
    if '..' in username or '__' in username or '._' in username or '_.' in username:
        return False, "Username cannot have consecutive special characters."
    
    return True, "Username is valid."
