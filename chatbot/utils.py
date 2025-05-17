from django.conf import settings
import os
import magic
from typing import Dict, Any

def validate_attachment(attachment: Dict[str, Any]) -> bool:
    """
    Validate an attachment file.
    
    Args:
        attachment: Dictionary containing attachment data with keys:
            - name: File name
            - type: MIME type
            - size: File size in bytes
            - data: Base64 encoded file data (optional)
    
    Returns:
        bool: True if attachment is valid, False otherwise
    """
    try:
        # Check required fields
        if not all(key in attachment for key in ['name', 'type', 'size']):
            return False

        # Validate file size
        max_size = getattr(settings, 'MAX_ATTACHMENT_SIZE', 5 * 1024 * 1024)  # 5MB default
        if attachment['size'] > max_size:
            return False

        # Validate file type
        allowed_types = getattr(settings, 'ALLOWED_ATTACHMENT_TYPES', [
            'image/jpeg',
            'image/png',
            'image/gif',
            'application/pdf',
            'text/plain',
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        ])
        
        if attachment['type'] not in allowed_types:
            return False

        # If data is provided, validate it
        if 'data' in attachment:
            try:
                # Decode base64 data
                import base64
                file_data = base64.b64decode(attachment['data'])
                
                # Check MIME type using python-magic
                mime = magic.Magic(mime=True)
                detected_type = mime.from_buffer(file_data)
                
                if detected_type != attachment['type']:
                    return False
                
                # Check file size matches
                if len(file_data) != attachment['size']:
                    return False
                    
            except Exception:
                return False

        return True

    except Exception:
        return False

def get_file_extension(filename: str) -> str:
    """Get file extension from filename."""
    return os.path.splitext(filename)[1].lower()

def is_safe_filename(filename: str) -> bool:
    """Check if filename is safe to use."""
    # Remove any directory components
    filename = os.path.basename(filename)
    
    # Check for invalid characters
    invalid_chars = '<>:"/\\|?*'
    if any(char in filename for char in invalid_chars):
        return False
        
    # Check for reserved names
    reserved_names = ['CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4',
                     'LPT1', 'LPT2', 'LPT3', 'LPT4']
    if filename.upper() in reserved_names:
        return False
        
    return True

def sanitize_filename(filename: str) -> str:
    """Sanitize filename to make it safe."""
    # Remove any directory components
    filename = os.path.basename(filename)
    
    # Replace invalid characters with underscore
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
        
    # Add timestamp to prevent name collisions
    from django.utils import timezone
    timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
    name, ext = os.path.splitext(filename)
    return f"{name}_{timestamp}{ext}"

def get_attachment_path(conversation_id: int, filename: str) -> str:
    """Get the path where an attachment should be stored."""
    # Create directory if it doesn't exist
    base_dir = getattr(settings, 'ATTACHMENT_BASE_DIR', 'attachments')
    conversation_dir = os.path.join(base_dir, str(conversation_id))
    os.makedirs(conversation_dir, exist_ok=True)
    
    # Return full path
    return os.path.join(conversation_dir, filename)

def save_attachment(conversation_id: int, attachment: Dict[str, Any]) -> str:
    """
    Save an attachment file.
    
    Args:
        conversation_id: ID of the conversation
        attachment: Dictionary containing attachment data
    
    Returns:
        str: Path to saved file
    """
    if not validate_attachment(attachment):
        raise ValueError("Invalid attachment")
        
    # Decode base64 data
    import base64
    file_data = base64.b64decode(attachment['data'])
    
    # Sanitize filename
    filename = sanitize_filename(attachment['name'])
    
    # Get full path
    file_path = get_attachment_path(conversation_id, filename)
    
    # Save file
    with open(file_path, 'wb') as f:
        f.write(file_data)
        
    return file_path 