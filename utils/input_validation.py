"""
PittState-Connect | Input Validation & Sanitization
Centralized security utilities for validating and sanitizing user input.
"""

import bleach
import re
from typing import Optional, Dict, Any
from flask import abort


# HTML sanitization settings
ALLOWED_TAGS = {
    'basic': ['p', 'br', 'strong', 'em', 'u'],
    'rich': ['p', 'br', 'strong', 'em', 'u', 'ul', 'ol', 'li', 'a', 'h1', 'h2', 'h3'],
    'none': []
}

ALLOWED_ATTRS = {
    'basic': {},
    'rich': {'a': ['href', 'title']},
    'none': {}
}


def sanitize_html(text: str, level: str = 'basic') -> str:
    """
    Sanitize HTML content to prevent XSS attacks
    
    Args:
        text: Raw HTML/text input
        level: 'basic', 'rich', or 'none' (strips all HTML)
        
    Returns:
        Sanitized text safe for database/display
    """
    if not text:
        return ""
    
    tags = ALLOWED_TAGS.get(level, ALLOWED_TAGS['basic'])
    attrs = ALLOWED_ATTRS.get(level, ALLOWED_ATTRS['basic'])
    
    return bleach.clean(text, tags=tags, attributes=attrs, strip=True)


def validate_email(email: str) -> bool:
    """
    Validate email format
    
    Args:
        email: Email address to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not email:
        return False
    
    # RFC 5322 compliant regex (simplified)
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_phone(phone: str) -> bool:
    """
    Validate phone number format (US/international)
    
    Args:
        phone: Phone number to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not phone:
        return False
    
    # Remove common separators
    cleaned = re.sub(r'[\s\-\(\)\.]', '', phone)
    
    # Check if it's all digits and reasonable length
    return cleaned.isdigit() and 10 <= len(cleaned) <= 15


def validate_url(url: str, require_https: bool = False) -> bool:
    """
    Validate URL format
    
    Args:
        url: URL to validate
        require_https: If True, only allow HTTPS URLs
        
    Returns:
        True if valid, False otherwise
    """
    if not url:
        return False
    
    if require_https:
        pattern = r'^https://[a-zA-Z0-9\-\.]+\.[a-zA-Z]{2,}(/.*)?$'
    else:
        pattern = r'^https?://[a-zA-Z0-9\-\.]+\.[a-zA-Z]{2,}(/.*)?$'
    
    return bool(re.match(pattern, url))


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent directory traversal attacks
    
    Args:
        filename: Original filename
        
    Returns:
        Safe filename
    """
    # Remove path separators and null bytes
    filename = filename.replace('/', '').replace('\\', '').replace('\x00', '')
    
    # Remove leading dots (hidden files)
    filename = filename.lstrip('.')
    
    # Only allow alphanumeric, dash, underscore, and dot
    filename = re.sub(r'[^\w\-\.]', '_', filename)
    
    # Limit length
    if len(filename) > 255:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        filename = name[:240] + ('.' + ext if ext else '')
    
    return filename


def validate_integer(value: Any, min_val: Optional[int] = None, max_val: Optional[int] = None) -> Optional[int]:
    """
    Safely convert and validate integer
    
    Args:
        value: Value to convert
        min_val: Minimum allowed value (inclusive)
        max_val: Maximum allowed value (inclusive)
        
    Returns:
        Validated integer or None if invalid
    """
    try:
        num = int(value)
        
        if min_val is not None and num < min_val:
            return None
        if max_val is not None and num > max_val:
            return None
        
        return num
    except (ValueError, TypeError):
        return None


def validate_float(value: Any, min_val: Optional[float] = None, max_val: Optional[float] = None) -> Optional[float]:
    """
    Safely convert and validate float
    
    Args:
        value: Value to convert
        min_val: Minimum allowed value (inclusive)
        max_val: Maximum allowed value (inclusive)
        
    Returns:
        Validated float or None if invalid
    """
    try:
        num = float(value)
        
        if min_val is not None and num < min_val:
            return None
        if max_val is not None and num > max_val:
            return None
        
        return num
    except (ValueError, TypeError):
        return None


def sanitize_sql_like(text: str) -> str:
    """
    Escape special characters in SQL LIKE patterns
    
    Args:
        text: Search text
        
    Returns:
        Escaped text safe for LIKE queries
    """
    if not text:
        return ""
    
    # Escape LIKE wildcards
    text = text.replace('\\', '\\\\')
    text = text.replace('%', '\\%')
    text = text.replace('_', '\\_')
    
    return text


def validate_csrf_token(form_data: Dict[str, Any], required: bool = True) -> bool:
    """
    Validate CSRF token presence (Flask-WTF handles actual validation)
    
    Args:
        form_data: Form data dictionary
        required: If True, token must be present
        
    Returns:
        True if valid or not required, False otherwise
    """
    if not required:
        return True
    
    return 'csrf_token' in form_data


def check_sql_injection_patterns(text: str) -> bool:
    """
    Check for common SQL injection patterns
    
    Args:
        text: Text to check
        
    Returns:
        True if suspicious patterns found, False otherwise
    """
    if not text:
        return False
    
    # Common SQL injection patterns
    patterns = [
        r"(\bUNION\b.*\bSELECT\b)",
        r"(\bDROP\b.*\bTABLE\b)",
        r"(\bINSERT\b.*\bINTO\b)",
        r"(\bDELETE\b.*\bFROM\b)",
        r"(\bUPDATE\b.*\bSET\b)",
        r"(--|\#|\/\*|\*\/)",
        r"(\bOR\b.*=.*)",
        r"(\bAND\b.*=.*)",
        r"(1=1|'=')"
    ]
    
    text_upper = text.upper()
    for pattern in patterns:
        if re.search(pattern, text_upper, re.IGNORECASE):
            return True
    
    return False


def safe_redirect_url(url: str, allowed_hosts: list = None) -> Optional[str]:
    """
    Validate redirect URL to prevent open redirect vulnerabilities
    
    Args:
        url: URL to validate
        allowed_hosts: List of allowed hostnames
        
    Returns:
        Safe URL or None if unsafe
    """
    if not url:
        return None
    
    # Only allow relative URLs or URLs from allowed hosts
    if url.startswith('/'):
        return url
    
    if allowed_hosts:
        for host in allowed_hosts:
            if url.startswith(f'https://{host}') or url.startswith(f'http://{host}'):
                return url
    
    return None


def require_field(data: Dict[str, Any], field: str, field_type: type = str, error_msg: str = None):
    """
    Require a field to be present and of correct type, abort if not
    
    Args:
        data: Data dictionary
        field: Field name
        field_type: Expected type
        error_msg: Custom error message
        
    Raises:
        400 Bad Request if field missing or wrong type
    """
    if field not in data:
        abort(400, description=error_msg or f"Missing required field: {field}")
    
    if not isinstance(data[field], field_type):
        abort(400, description=error_msg or f"Field '{field}' must be of type {field_type.__name__}")


def sanitize_json_keys(data: Dict[str, Any], allowed_keys: list) -> Dict[str, Any]:
    """
    Filter JSON/dict to only include allowed keys
    
    Args:
        data: Original data
        allowed_keys: List of allowed key names
        
    Returns:
        Filtered dictionary
    """
    return {k: v for k, v in data.items() if k in allowed_keys}
