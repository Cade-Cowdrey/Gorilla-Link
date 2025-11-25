"""
Example: Integrating all production features into your Flask app
This shows how to enable Swagger, Sentry, Testing, and Analytics
"""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from extensions import db, login_manager, cache, mail

# Import production feature utilities
from utils.swagger_config import init_swagger
from utils.sentry_config import init_sentry, init_sentry_middleware
from utils.security_headers import init_security_headers
from utils.advanced_rate_limiting import AdvancedRateLimiter

def create_app(config=None):
    """
    Application factory with all production features enabled
    """
    app = Flask(__name__)
    
    # Load configuration
    if config:
        app.config.update(config)
    else:
        app.config.from_object('config.prod')
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    cache.init_app(app)
    mail.init_app(app)
    
    # ==========================================
    # PRODUCTION FEATURE 1: Swagger API Documentation
    # ==========================================
    init_swagger(app)
    print("✅ Swagger API documentation enabled at /docs/")
    
    # ==========================================
    # PRODUCTION FEATURE 2: Sentry Error Tracking
    # ==========================================
    if app.config.get('SENTRY_DSN'):
        init_sentry(app)
        init_sentry_middleware(app)
        print("✅ Sentry error tracking enabled")
    else:
        print("⚠️  Sentry not configured (set SENTRY_DSN)")
    
    # ==========================================
    # PRODUCTION FEATURE 3: Security Headers
    # ==========================================
    init_security_headers(app)
    print("✅ Security headers middleware enabled")
    
    # ==========================================
    # PRODUCTION FEATURE 4: Advanced Rate Limiting
    # ==========================================
    rate_limiter = AdvancedRateLimiter()
    app.rate_limiter = rate_limiter
    print("✅ Advanced rate limiting enabled")
    
    # ==========================================
    # PRODUCTION FEATURE 5: Performance Monitoring
    # ==========================================
    from utils.query_optimizer import QueryTracker
    query_tracker = QueryTracker()
    query_tracker.init_app(app)
    print("✅ Query performance monitoring enabled")
    
    # ==========================================
    # Register Blueprints
    # ==========================================
    
    # Core blueprints
    from blueprints.auth import routes as auth_bp
    from blueprints.profile import routes as profile_bp
    from blueprints.careers import routes as careers_bp
    from blueprints.events import routes as events_bp
    from blueprints.scholarships import routes as scholarships_bp
    
    # Admin blueprints
    from blueprints.admin import routes as admin_bp
    from blueprints.admin.performance import bp as performance_bp
    
    # Analytics blueprint
    from blueprints.analytics import routes as analytics_bp
    
    # System blueprints
    from blueprints.system.health import bp as health_bp
    
    # Register all blueprints
    app.register_blueprint(auth_bp.bp)
    app.register_blueprint(profile_bp.bp)
    app.register_blueprint(careers_bp.bp)
    app.register_blueprint(events_bp.bp)
    app.register_blueprint(scholarships_bp.bp)
    app.register_blueprint(admin_bp.bp)
    app.register_blueprint(performance_bp)
    app.register_blueprint(analytics_bp.bp)
    app.register_blueprint(health_bp)
    
    print("✅ All blueprints registered")
    
    # ==========================================
    # Example: Documented API Endpoint with Rate Limiting
    # ==========================================
    
    from flask import jsonify, request
    from flask_login import login_required, current_user
    from utils.advanced_rate_limiting import rate_limit
    from utils.sentry_config import capture_exception, add_breadcrumb
    
    @app.route('/api/example', methods=['GET'])
    @login_required
    @rate_limit(limit=100, window=3600)  # 100 requests per hour
    def api_example():
        """
        Example API endpoint with full production features
        ---
        tags:
          - Examples
        parameters:
          - name: query
            in: query
            type: string
            required: false
            description: Search query
        responses:
          200:
            description: Successful response
            schema:
              type: object
              properties:
                message:
                  type: string
                user:
                  type: string
                data:
                  type: array
          401:
            description: Unauthorized
          429:
            description: Rate limit exceeded
        security:
          - Bearer: []
        """
        try:
            # Add breadcrumb for Sentry
            add_breadcrumb(
                message=f"API example called by {current_user.email}",
                category='api',
                level='info'
            )
            
            # Your API logic here
            query = request.args.get('query', '')
            
            return jsonify({
                'message': 'Success',
                'user': current_user.email,
                'query': query,
                'data': []
            }), 200
            
        except Exception as e:
            # Automatically captured by Sentry middleware
            # But you can add context:
            query = request.args.get('query', '')
            capture_exception(e, context={
                'endpoint': '/api/example',
                'user_id': current_user.id,
                'query': query
            })
            return jsonify({'error': 'Internal server error'}), 500
    
    # ==========================================
    # Error Handlers
    # ==========================================
    
    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 errors with Swagger-documented response"""
        return jsonify({
            'error': 'Not found',
            'code': 'NOT_FOUND',
            'message': 'The requested resource was not found'
        }), 404
    
    @app.errorhandler(429)
    def rate_limit_exceeded(error):
        """Handle rate limit errors"""
        return jsonify({
            'error': 'Too many requests',
            'code': 'RATE_LIMIT_EXCEEDED',
            'message': 'You have exceeded the rate limit. Please try again later.',
            'retry_after': error.description if hasattr(error, 'description') else 60
        }), 429
    
    @app.errorhandler(500)
    def internal_error(error):
        """Handle internal errors (automatically sent to Sentry)"""
        return jsonify({
            'error': 'Internal server error',
            'code': 'INTERNAL_ERROR',
            'message': 'An unexpected error occurred'
        }), 500
    
    # ==========================================
    # Health Check
    # ==========================================
    
    @app.route('/health/features')
    def health_features():
        """
        Check status of production features
        ---
        tags:
          - Health
        responses:
          200:
            description: Feature status
        """
        return jsonify({
            'status': 'healthy',
            'features': {
                'swagger': True,
                'sentry': bool(app.config.get('SENTRY_DSN')),
                'rate_limiting': True,
                'security_headers': True,
                'query_monitoring': True,
                'analytics': True
            },
            'endpoints': {
                'api_docs': '/docs/',
                'analytics': '/analytics/',
                'performance': '/admin/performance/',
                'health': '/health/'
            }
        })
    
    print("\n" + "="*60)
    print("🚀 PittState Connect - Production Ready!")
    print("="*60)
    print("📚 API Documentation: http://localhost:5000/docs/")
    print("📊 Analytics Dashboard: http://localhost:5000/analytics/")
    print("⚡ Performance Monitor: http://localhost:5000/admin/performance/")
    print("❤️  Health Check: http://localhost:5000/health/")
    print("✅ All production features enabled!")
    print("="*60 + "\n")
    
    return app


# ==========================================
# Example: Testing with Pytest
# ==========================================
"""
# tests/test_integration.py

def test_api_example_endpoint(authenticated_client):
    '''Test the example API endpoint'''
    response = authenticated_client.get('/api/example?query=test')
    assert response.status_code == 200
    
    data = response.get_json()
    assert data['message'] == 'Success'
    assert 'user' in data
    assert 'query' in data

def test_rate_limiting(authenticated_client):
    '''Test that rate limiting works'''
    # Make 101 requests (limit is 100)
    for i in range(101):
        response = authenticated_client.get('/api/example')
        
        if i < 100:
            assert response.status_code == 200
        else:
            assert response.status_code == 429  # Rate limit exceeded

def test_swagger_docs(client):
    '''Test that Swagger docs are accessible'''
    response = client.get('/docs/')
    assert response.status_code == 200

def test_analytics_dashboard(admin_client):
    '''Test analytics dashboard access'''
    response = admin_client.get('/analytics/')
    assert response.status_code == 200
"""


# ==========================================
# Example: Running Tests
# ==========================================
"""
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run only API tests
pytest -m api tests/test_integration.py

# Run specific test
pytest tests/test_integration.py::test_api_example_endpoint
"""


# ==========================================
# Example: CI/CD Deployment
# ==========================================
"""
# .github/workflows/ci-cd.yml is already configured!
# 
# It will automatically:
# 1. Run linting (Black, Flake8, Pylint)
# 2. Run security scans (Bandit, Safety)
# 3. Run all tests with coverage
# 4. Build Docker image
# 5. Deploy to production (on main branch)
# 6. Run performance tests
# 7. Send notifications
#
# Required secrets in GitHub:
# - DOCKER_USERNAME
# - DOCKER_PASSWORD
# - RENDER_API_KEY
# - RENDER_SERVICE_ID
# - DATABASE_URL
# - SENTRY_DSN
# - SLACK_WEBHOOK_URL
"""


if __name__ == '__main__':
    # Create app with production features
    app = create_app()
    
    # Run development server
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )
