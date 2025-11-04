"""
Sentry Error Tracking and Performance Monitoring Configuration
Provides comprehensive error tracking, performance monitoring, and user feedback
"""

import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
import logging
import os


def init_sentry(app):
    """
    Initialize Sentry SDK for error tracking and performance monitoring
    
    Args:
        app: Flask application instance
    """
    sentry_dsn = os.getenv('SENTRY_DSN')
    
    if not sentry_dsn:
        app.logger.warning('SENTRY_DSN not configured. Error tracking disabled.')
        return None
    
    environment = os.getenv('FLASK_ENV', 'production')
    release_version = os.getenv('APP_VERSION', 'unknown')
    
    # Configure Sentry
    sentry_sdk.init(
        dsn=sentry_dsn,
        integrations=[
            FlaskIntegration(
                transaction_style='url'  # Use URL patterns for transaction names
            ),
            SqlalchemyIntegration(),
            RedisIntegration(),
            CeleryIntegration(),
            LoggingIntegration(
                level=logging.INFO,  # Capture info and above as breadcrumbs
                event_level=logging.ERROR  # Send errors as events
            )
        ],
        
        # Set traces_sample_rate to 1.0 to capture 100% of transactions for performance monitoring
        # Adjust this value in production (e.g., 0.1 = 10% of transactions)
        traces_sample_rate=float(os.getenv('SENTRY_TRACES_SAMPLE_RATE', '0.1')),
        
        # Set profiles_sample_rate to 1.0 to profile 100% of sampled transactions
        # Profiling helps identify performance bottlenecks
        profiles_sample_rate=float(os.getenv('SENTRY_PROFILES_SAMPLE_RATE', '0.1')),
        
        # Environment (production, staging, development)
        environment=environment,
        
        # Release version for tracking
        release=f"pittstate-connect@{release_version}",
        
        # Send default PII (Personally Identifiable Information)
        send_default_pii=False,  # Set to False for privacy compliance
        
        # Attach stack trace to messages
        attach_stacktrace=True,
        
        # Maximum breadcrumbs to capture
        max_breadcrumbs=50,
        
        # Before send callback for filtering/modifying events
        before_send=before_send_handler,
        
        # Before breadcrumb callback for filtering breadcrumbs
        before_breadcrumb=before_breadcrumb_handler,
        
        # Debug mode
        debug=environment == 'development',
        
        # Enable tracing for database queries
        enable_tracing=True
    )
    
    app.logger.info(f'Sentry initialized for {environment} environment (release: {release_version})')
    
    return sentry_sdk


def before_send_handler(event, hint):
    """
    Filter and modify events before sending to Sentry
    
    Args:
        event: Event data dictionary
        hint: Additional context about the event
        
    Returns:
        Modified event or None to drop the event
    """
    # Ignore certain exceptions
    if 'exc_info' in hint:
        exc_type, exc_value, tb = hint['exc_info']
        
        # Ignore common client errors
        ignored_exceptions = [
            'werkzeug.exceptions.NotFound',  # 404 errors
            'werkzeug.exceptions.BadRequest',  # 400 errors
        ]
        
        exception_name = f"{exc_type.__module__}.{exc_type.__name__}"
        if exception_name in ignored_exceptions:
            return None
    
    # Sanitize sensitive data
    if 'request' in event:
        request_data = event['request']
        
        # Remove sensitive headers
        if 'headers' in request_data:
            sensitive_headers = ['Authorization', 'Cookie', 'X-API-Key']
            for header in sensitive_headers:
                if header in request_data['headers']:
                    request_data['headers'][header] = '[Filtered]'
        
        # Remove sensitive POST data
        if 'data' in request_data:
            sensitive_fields = ['password', 'token', 'secret', 'api_key', 'ssn', 'credit_card']
            if isinstance(request_data['data'], dict):
                for field in sensitive_fields:
                    if field in request_data['data']:
                        request_data['data'][field] = '[Filtered]'
    
    # Add custom tags
    event.setdefault('tags', {})
    event['tags']['app_version'] = os.getenv('APP_VERSION', 'unknown')
    
    return event


def before_breadcrumb_handler(crumb, hint):
    """
    Filter and modify breadcrumbs before adding to event
    
    Args:
        crumb: Breadcrumb data dictionary
        hint: Additional context
        
    Returns:
        Modified breadcrumb or None to drop it
    """
    # Ignore verbose breadcrumbs
    if crumb.get('category') == 'query' and crumb.get('message', '').startswith('SELECT 1'):
        return None  # Ignore health check queries
    
    # Sanitize SQL queries with sensitive data
    if crumb.get('category') == 'query':
        message = crumb.get('message', '')
        if any(keyword in message.lower() for keyword in ['password', 'token', 'secret']):
            crumb['message'] = '[Query with sensitive data]'
    
    return crumb


def capture_exception(error, context=None, level='error'):
    """
    Manually capture an exception and send to Sentry
    
    Args:
        error: Exception instance or error message
        context: Additional context dictionary
        level: Error level (error, warning, info)
    """
    with sentry_sdk.push_scope() as scope:
        # Set level
        scope.level = level
        
        # Add context
        if context:
            for key, value in context.items():
                scope.set_context(key, value)
        
        # Capture exception
        if isinstance(error, Exception):
            sentry_sdk.capture_exception(error)
        else:
            sentry_sdk.capture_message(str(error), level=level)


def capture_message(message, level='info', context=None):
    """
    Capture a message and send to Sentry
    
    Args:
        message: Message string
        level: Message level (info, warning, error)
        context: Additional context dictionary
    """
    with sentry_sdk.push_scope() as scope:
        scope.level = level
        
        if context:
            for key, value in context.items():
                scope.set_context(key, value)
        
        sentry_sdk.capture_message(message, level=level)


def set_user_context(user):
    """
    Set user context for error tracking
    
    Args:
        user: User object or dictionary with id, email, username
    """
    user_data = {}
    
    if hasattr(user, 'id'):
        user_data['id'] = user.id
    elif isinstance(user, dict) and 'id' in user:
        user_data['id'] = user['id']
    
    if hasattr(user, 'email'):
        user_data['email'] = user.email
    elif isinstance(user, dict) and 'email' in user:
        user_data['email'] = user['email']
    
    if hasattr(user, 'username'):
        user_data['username'] = user.username
    elif isinstance(user, dict) and 'username' in user:
        user_data['username'] = user['username']
    
    if hasattr(user, 'role'):
        user_data['role'] = user.role
    elif isinstance(user, dict) and 'role' in user:
        user_data['role'] = user['role']
    
    sentry_sdk.set_user(user_data)


def clear_user_context():
    """Clear user context (e.g., on logout)"""
    sentry_sdk.set_user(None)


def add_breadcrumb(message, category='custom', level='info', data=None):
    """
    Add a custom breadcrumb
    
    Args:
        message: Breadcrumb message
        category: Category (http, navigation, query, etc.)
        level: Level (info, warning, error)
        data: Additional data dictionary
    """
    sentry_sdk.add_breadcrumb(
        message=message,
        category=category,
        level=level,
        data=data or {}
    )


def set_tag(key, value):
    """
    Set a custom tag for the current scope
    
    Args:
        key: Tag key
        value: Tag value
    """
    sentry_sdk.set_tag(key, value)


def set_context(name, context):
    """
    Set a custom context for the current scope
    
    Args:
        name: Context name
        context: Context dictionary
    """
    sentry_sdk.set_context(name, context)


def start_transaction(name, op='http.server'):
    """
    Start a performance monitoring transaction
    
    Args:
        name: Transaction name
        op: Operation type
        
    Returns:
        Transaction instance
    """
    return sentry_sdk.start_transaction(name=name, op=op)


def start_span(operation, description=None):
    """
    Start a performance monitoring span
    
    Args:
        operation: Span operation name
        description: Span description
        
    Returns:
        Span instance
    """
    return sentry_sdk.start_span(op=operation, description=description)


class SentryMiddleware:
    """
    Flask middleware for enhanced Sentry integration
    """
    
    def __init__(self, app):
        self.app = app
        app.before_request(self.before_request)
        app.after_request(self.after_request)
        app.teardown_request(self.teardown_request)
    
    def before_request(self):
        """Set up request context"""
        from flask import request, g
        from flask_login import current_user
        
        # Start transaction
        transaction_name = f"{request.method} {request.endpoint or request.path}"
        g.sentry_transaction = sentry_sdk.start_transaction(
            name=transaction_name,
            op='http.server'
        )
        g.sentry_transaction.__enter__()
        
        # Set user context
        if current_user and current_user.is_authenticated:
            set_user_context(current_user)
        
        # Add request breadcrumb
        add_breadcrumb(
            message=f"{request.method} {request.path}",
            category='http',
            data={
                'url': request.url,
                'method': request.method,
                'headers': dict(request.headers)
            }
        )
    
    def after_request(self, response):
        """Add response context"""
        from flask import g
        
        # Set response status tag
        set_tag('http.status_code', response.status_code)
        
        return response
    
    def teardown_request(self, exception=None):
        """Finish transaction and capture exceptions"""
        from flask import g
        
        # Capture exception if present
        if exception:
            capture_exception(exception)
        
        # Finish transaction
        if hasattr(g, 'sentry_transaction'):
            g.sentry_transaction.__exit__(None, None, None)


def init_sentry_middleware(app):
    """
    Initialize Sentry middleware
    
    Args:
        app: Flask application instance
    """
    return SentryMiddleware(app)
