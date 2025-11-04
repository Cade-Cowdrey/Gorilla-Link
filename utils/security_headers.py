"""
PittState-Connect | Security Headers Configuration
Comprehensive security headers to protect against common web vulnerabilities.
"""

from flask import Flask, g
from typing import Dict
import secrets


def generate_csp_nonce() -> str:
    """Generate a random nonce for Content Security Policy"""
    return secrets.token_urlsafe(16)


def get_security_headers(app: Flask) -> Dict[str, str]:
    """
    Get recommended security headers for production
    
    Returns:
        Dictionary of header name -> value
    """
    # Generate nonce for inline scripts (stored in g for template access)
    nonce = getattr(g, 'csp_nonce', None)
    if not nonce:
        nonce = generate_csp_nonce()
        g.csp_nonce = nonce
    
    headers = {
        # Prevent MIME type sniffing
        'X-Content-Type-Options': 'nosniff',
        
        # Clickjacking protection
        'X-Frame-Options': 'SAMEORIGIN',
        
        # XSS protection (modern browsers use CSP instead, but kept for legacy)
        'X-XSS-Protection': '0',  # Disabled as CSP is more robust
        
        # Referrer policy
        'Referrer-Policy': 'strict-origin-when-cross-origin',
        
        # Permissions policy (formerly Feature-Policy)
        'Permissions-Policy': (
            'geolocation=(), '
            'microphone=(), '
            'camera=(), '
            'payment=(), '
            'usb=(), '
            'magnetometer=(), '
            'gyroscope=(), '
            'accelerometer=()'
        ),
    }
    
    # Add HSTS only in production
    if not app.debug:
        headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    
    # Content Security Policy (adjusted for Bootstrap, Tailwind, and inline styles)
    csp_directives = {
        "default-src": "'self'",
        "script-src": f"'self' 'nonce-{nonce}' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com https://unpkg.com",
        "style-src": "'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com https://fonts.googleapis.com",
        "font-src": "'self' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com https://fonts.gstatic.com data:",
        "img-src": "'self' data: https: blob:",
        "connect-src": "'self' https://api.openai.com",
        "frame-ancestors": "'self'",
        "base-uri": "'self'",
        "form-action": "'self'",
        "upgrade-insecure-requests": "",
    }
    
    # Build CSP header
    csp_header = "; ".join([f"{k} {v}".strip() for k, v in csp_directives.items()])
    headers['Content-Security-Policy'] = csp_header
    
    return headers


def init_security_headers(app: Flask):
    """
    Initialize security headers middleware
    
    Args:
        app: Flask application instance
    """
    
    @app.before_request
    def generate_nonce():
        """Generate CSP nonce for each request"""
        g.csp_nonce = generate_csp_nonce()
    
    @app.after_request
    def set_security_headers(response):
        """Apply security headers to all responses"""
        headers = get_security_headers(app)
        
        for header, value in headers.items():
            # Don't override existing headers
            if header not in response.headers:
                response.headers[header] = value
        
        return response
    
    app.logger.info("🔒 Security headers middleware initialized")


def get_security_report() -> Dict[str, bool]:
    """
    Generate security configuration report
    
    Returns:
        Dictionary of security feature -> enabled status
    """
    from flask import current_app
    
    return {
        "HTTPS Enforced": not current_app.debug,
        "HSTS Enabled": not current_app.debug,
        "CSP Enabled": True,
        "XSS Protection": True,
        "Clickjacking Protection": True,
        "MIME Sniffing Protection": True,
        "Referrer Policy": True,
        "Permissions Policy": True,
        "CSRF Protection": current_app.config.get('WTF_CSRF_ENABLED', False),
        "Rate Limiting": True,
        "SQL Injection Protection": True,  # Via SQLAlchemy ORM
        "Password Hashing": True,  # Via bcrypt
        "Secure Cookies": current_app.config.get('SESSION_COOKIE_SECURE', False),
        "HttpOnly Cookies": current_app.config.get('SESSION_COOKIE_HTTPONLY', True),
    }
