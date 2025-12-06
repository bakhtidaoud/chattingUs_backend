"""
Image processing utilities.
"""

import os
from PIL import Image, ImageOps
from django.core.files.base import ContentFile
from io import BytesIO
import logging

logger = logging.getLogger(__name__)

# Image sizes configuration
IMAGE_SIZES = {
    'thumbnail': (150, 150),  # Square crop
    'small': (320, 320),      # Max dimension
    'medium': (640, 640),     # Max dimension
    'large': (1080, 1080),    # Max dimension
}

# Quality settings
JPEG_QUALITY = 85
WEBP_QUALITY = 80


def resize_image(image: Image.Image, size: tuple, crop: bool = False) -> Image.Image:
    """
    Resize image maintaining aspect ratio or crop to exact size.
    
    Args:
        image: PIL Image object
        size: Tuple of (width, height)
        crop: If True, crop to exact size. If False, fit within size.
    
    Returns:
        Resized PIL Image object
    """
    if crop:
        # Crop to exact size
        return ImageOps.fit(image, size, Image.Resampling.LANCZOS)
    else:
        # Resize maintaining aspect ratio
        image_copy = image.copy()
        image_copy.thumbnail(size, Image.Resampling.LANCZOS)
        return image_copy


def compress_image(image: Image.Image, format: str = 'JPEG', quality: int = JPEG_QUALITY) -> BytesIO:
    """
    Compress image to specified format and quality.
    
    Args:
        image: PIL Image object
        format: Output format ('JPEG', 'PNG', 'WEBP')
        quality: Compression quality (1-100)
    
    Returns:
        BytesIO object containing compressed image
    """
    output = BytesIO()
    
    # Convert RGBA to RGB for JPEG
    if format == 'JPEG' and image.mode in ('RGBA', 'LA', 'P'):
        # Create white background
        background = Image.new('RGB', image.size, (255, 255, 255))
        if image.mode == 'P':
            image = image.convert('RGBA')
        background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
        image = background
    
    # Save with compression
    save_kwargs = {'format': format, 'quality': quality}
    
    if format == 'JPEG':
        save_kwargs['optimize'] = True
    elif format == 'PNG':
        save_kwargs['optimize'] = True
    elif format == 'WEBP':
        save_kwargs['method'] = 6  # Compression method (0-6, higher is slower but better)
    
    image.save(output, **save_kwargs)
    output.seek(0)
    
    return output


def convert_to_webp(image: Image.Image) -> BytesIO:
    """
    Convert image to WebP format.
    
    Args:
        image: PIL Image object
    
    Returns:
        BytesIO object containing WebP image
    """
    return compress_image(image, format='WEBP', quality=WEBP_QUALITY)


def generate_thumbnails(image_path: str) -> dict:
    """
    Generate multiple thumbnail sizes from an image.
    
    Args:
        image_path: Path to original image file
    
    Returns:
        Dict with size names as keys and BytesIO objects as values
    """
    thumbnails = {}
    
    try:
        with Image.open(image_path) as img:
            # Auto-rotate based on EXIF data
            img = ImageOps.exif_transpose(img)
            
            # Generate each size
            for size_name, dimensions in IMAGE_SIZES.items():
                # Thumbnail is cropped, others maintain aspect ratio
                crop = (size_name == 'thumbnail')
                
                resized = resize_image(img, dimensions, crop=crop)
                
                # Determine format based on original
                format = 'JPEG' if img.format in ['JPEG', 'JPG'] else 'PNG'
                
                # Compress
                compressed = compress_image(resized, format=format)
                
                thumbnails[size_name] = compressed
            
            # Generate WebP version (medium size)
            webp_img = resize_image(img, IMAGE_SIZES['medium'], crop=False)
            thumbnails['webp'] = convert_to_webp(webp_img)
    
    except Exception as e:
        logger.error(f"Error generating thumbnails: {e}")
        raise
    
    return thumbnails


def get_image_dimensions(image_path: str) -> tuple:
    """
    Get image dimensions.
    
    Args:
        image_path: Path to image file
    
    Returns:
        Tuple of (width, height)
    """
    try:
        with Image.open(image_path) as img:
            # Auto-rotate based on EXIF data
            img = ImageOps.exif_transpose(img)
            return img.size
    except Exception as e:
        logger.error(f"Error getting image dimensions: {e}")
        return (0, 0)


def process_image(media_instance):
    """
    Process uploaded image: generate thumbnails and WebP version.
    
    Args:
        media_instance: Media model instance
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Get original file path
        original_path = media_instance.original_file.path
        
        # Get dimensions
        width, height = get_image_dimensions(original_path)
        media_instance.width = width
        media_instance.height = height
        
        # Generate all sizes
        thumbnails = generate_thumbnails(original_path)
        
        # Get original filename without extension
        original_name = os.path.splitext(os.path.basename(original_path))[0]
        
        # Save each size
        for size_name, image_data in thumbnails.items():
            if size_name == 'webp':
                ext = 'webp'
            else:
                # Use original extension or default to jpg
                ext = os.path.splitext(original_path)[1][1:] or 'jpg'
            
            filename = f"{original_name}_{size_name}.{ext}"
            
            # Save to appropriate field
            if size_name == 'thumbnail':
                media_instance.thumbnail.save(filename, ContentFile(image_data.read()), save=False)
            elif size_name == 'small':
                media_instance.small.save(filename, ContentFile(image_data.read()), save=False)
            elif size_name == 'medium':
                media_instance.medium.save(filename, ContentFile(image_data.read()), save=False)
            elif size_name == 'large':
                media_instance.large.save(filename, ContentFile(image_data.read()), save=False)
            elif size_name == 'webp':
                media_instance.webp.save(filename, ContentFile(image_data.read()), save=False)
        
        # Update status
        media_instance.status = 'ready'
        media_instance.save()
        
        logger.info(f"Successfully processed image {media_instance.id}")
        return True
    
    except Exception as e:
        logger.error(f"Error processing image {media_instance.id}: {e}")
        media_instance.status = 'failed'
        media_instance.metadata['error'] = str(e)
        media_instance.save()
        return False
