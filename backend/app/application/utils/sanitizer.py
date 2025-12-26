"""Content sanitization utilities for XSS protection (GAP-SEC-001)"""

import bleach
from typing import Optional, List, Dict
import logging

logger = logging.getLogger(__name__)

# Allowed HTML tags for safe content rendering
ALLOWED_TAGS = [
    'p', 'br', 'strong', 'em', 'u', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'blockquote', 'code', 'pre', 'hr', 'ul', 'ol', 'li',
    'a', 'img', 'table', 'thead', 'tbody', 'tr', 'th', 'td'
]

# Allowed HTML attributes for safe content rendering
ALLOWED_ATTRIBUTES = {
    'a': ['href', 'title', 'target'],
    'img': ['src', 'alt', 'title', 'width', 'height'],
    'code': ['class'],
    'pre': ['class'],
    '*': ['id', 'class']
}

# Allowed protocols for links and images
ALLOWED_PROTOCOLS = ['http', 'https', 'mailto', 'data']


class ContentSanitizer:
    """Content sanitizer for XSS protection"""
    
    @staticmethod
    def sanitize_html(content: str, strip: bool = False) -> str:
        """
        Sanitize HTML content to prevent XSS attacks
        
        Args:
            content: HTML content to sanitize
            strip: If True, strip all tags (plain text only)
            
        Returns:
            Sanitized HTML content
        """
        if not content:
            return ""
        
        try:
            if strip:
                # Strip all HTML tags - plain text only
                return bleach.clean(content, tags=[], attributes={}, strip=True)
            else:
                # Clean HTML with allowed tags and attributes
                return bleach.clean(
                    content,
                    tags=ALLOWED_TAGS,
                    attributes=ALLOWED_ATTRIBUTES,
                    protocols=ALLOWED_PROTOCOLS,
                    strip=True
                )
        except Exception as e:
            logger.error(f"Failed to sanitize HTML: {e}")
            # If sanitization fails, return plain text
            return bleach.clean(content, tags=[], attributes={}, strip=True)
    
    @staticmethod
    def sanitize_text(content: str) -> str:
        """
        Sanitize plain text content by removing all HTML
        
        Args:
            content: Text content to sanitize
            
        Returns:
            Sanitized plain text
        """
        return ContentSanitizer.sanitize_html(content, strip=True)
    
    @staticmethod
    def sanitize_user_message(message: str) -> str:
        """
        Sanitize user message content for chat
        
        Args:
            message: User message to sanitize
            
        Returns:
            Sanitized message
        """
        # For user messages, allow limited formatting
        return ContentSanitizer.sanitize_html(message, strip=False)
    
    @staticmethod
    def sanitize_dict(data: Dict, fields: List[str]) -> Dict:
        """
        Sanitize specific fields in a dictionary
        
        Args:
            data: Dictionary to sanitize
            fields: List of field names to sanitize
            
        Returns:
            Dictionary with sanitized fields
        """
        sanitized = data.copy()
        for field in fields:
            if field in sanitized and isinstance(sanitized[field], str):
                sanitized[field] = ContentSanitizer.sanitize_html(sanitized[field])
        return sanitized
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        Sanitize filename to prevent path traversal attacks
        
        Args:
            filename: Filename to sanitize
            
        Returns:
            Safe filename
        """
        if not filename:
            return ""
        
        # Remove path traversal attempts (../, ..\, etc.)
        safe_name = filename
        
        # Remove all path separators and null bytes
        safe_name = safe_name.replace("/", "_").replace("\\", "_").replace("\0", "")
        
        # Remove dots that could be used for path traversal
        safe_name = safe_name.replace("..", "_")
        
        # Remove leading dots to prevent hidden files
        safe_name = safe_name.lstrip(".")
        
        # Limit length
        max_length = 255
        if len(safe_name) > max_length:
            # Keep extension
            parts = safe_name.rsplit(".", 1)
            if len(parts) == 2:
                name, ext = parts
                max_name_length = max_length - len(ext) - 1
                safe_name = name[:max_name_length] + "." + ext
            else:
                safe_name = safe_name[:max_length]
        
        return safe_name or "unnamed_file"


# Convenience functions for common use cases
def sanitize_html(content: str, strip: bool = False) -> str:
    """Sanitize HTML content"""
    return ContentSanitizer.sanitize_html(content, strip=strip)


def sanitize_text(content: str) -> str:
    """Sanitize plain text content"""
    return ContentSanitizer.sanitize_text(content)


def sanitize_user_message(message: str) -> str:
    """Sanitize user message"""
    return ContentSanitizer.sanitize_user_message(message)


def sanitize_filename(filename: str) -> str:
    """Sanitize filename"""
    return ContentSanitizer.sanitize_filename(filename)
