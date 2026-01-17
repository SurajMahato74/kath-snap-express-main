from PIL import Image
import os
from django.conf import settings
from django.core.files.storage import default_storage
import uuid

class ImageProcessor:
    """Utility class for processing images in vendor messages"""
    
    ALLOWED_FORMATS = ['JPEG', 'PNG', 'GIF', 'WEBP']
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
    MAX_DIMENSIONS = (1920, 1920)
    THUMBNAIL_SIZE = (300, 300)
    
    @classmethod
    def validate_image(cls, uploaded_file):
        """Validate image file size and format"""
        # Check file size
        if uploaded_file.size > cls.MAX_FILE_SIZE:
            raise ValueError(f"Image size must be less than {cls.MAX_FILE_SIZE // (1024*1024)}MB")
        
        # Check if it's a valid image
        try:
            with Image.open(uploaded_file) as img:
                if img.format not in cls.ALLOWED_FORMATS:
                    raise ValueError(f"Unsupported format. Allowed: {', '.join(cls.ALLOWED_FORMATS)}")
                return True
        except Exception:
            raise ValueError("Invalid image file")
    
    @classmethod
    def process_message_image(cls, uploaded_file, conversation_id, user_id):
        """Process and save message image with optimization"""
        cls.validate_image(uploaded_file)
        
        # Generate unique filename
        file_extension = os.path.splitext(uploaded_file.name)[1].lower()
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = f"messages/{conversation_id}_{user_id}_{unique_filename}"
        
        # Open and process image
        with Image.open(uploaded_file) as img:
            # Convert to RGB if necessary
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')
            
            # Resize if too large
            if img.size[0] > cls.MAX_DIMENSIONS[0] or img.size[1] > cls.MAX_DIMENSIONS[1]:
                img.thumbnail(cls.MAX_DIMENSIONS, Image.Resampling.LANCZOS)
            
            # Save optimized image
            from io import BytesIO
            output = BytesIO()
            img.save(output, format='JPEG', quality=85, optimize=True)
            output.seek(0)
            
            # Save to storage
            saved_path = default_storage.save(file_path, output)
            
            # Create thumbnail
            thumbnail_path = cls.create_thumbnail(img, conversation_id, user_id, unique_filename)
            
            width, height = img.size
            return {
                'file_url': saved_path,
                'file_name': uploaded_file.name,
                'thumbnail_url': thumbnail_path,
                'file_size': output.getvalue().__len__(),
                'image_width': width,
                'image_height': height
            }
    
    @classmethod
    def create_thumbnail(cls, img, conversation_id, user_id, filename):
        """Create thumbnail for message image"""
        thumbnail_name = f"thumb_{filename}"
        thumbnail_path = f"messages/thumbnails/{conversation_id}_{user_id}_{thumbnail_name}"
        
        # Create thumbnail
        img_copy = img.copy()
        img_copy.thumbnail(cls.THUMBNAIL_SIZE, Image.Resampling.LANCZOS)
        
        from io import BytesIO
        output = BytesIO()
        img_copy.save(output, format='JPEG', quality=70, optimize=True)
        output.seek(0)
        
        return default_storage.save(thumbnail_path, output)