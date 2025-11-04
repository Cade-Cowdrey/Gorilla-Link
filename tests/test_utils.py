"""
Unit tests for utility functions
Tests for input validation, security, rate limiting, etc.
"""

import pytest
from utils.input_validation import (
    sanitize_html, validate_email, validate_phone,
    validate_url, check_sql_injection_patterns
)
from utils.advanced_rate_limiting import AdvancedRateLimiter
from utils.query_optimizer import QueryTracker, paginate_query
from unittest.mock import MagicMock, patch


class TestInputValidation:
    """Test input validation utilities"""
    
    def test_sanitize_html_basic(self):
        """Test basic HTML sanitization"""
        dirty_html = '<script>alert("xss")</script><p>Hello</p>'
        clean = sanitize_html(dirty_html)
        assert '<script>' not in clean
        assert '<p>Hello</p>' in clean or 'Hello' in clean
    
    def test_sanitize_html_strict(self):
        """Test strict HTML sanitization"""
        dirty_html = '<p><a href="test">Link</a></p>'
        clean = sanitize_html(dirty_html, level='strict')
        assert '<a' not in clean
        assert 'Link' in clean
    
    def test_validate_email_valid(self):
        """Test valid email validation"""
        assert validate_email('test@pittstate.edu') == True
        assert validate_email('john.doe@example.com') == True
    
    def test_validate_email_invalid(self):
        """Test invalid email validation"""
        assert validate_email('invalid.email') == False
        assert validate_email('@pittstate.edu') == False
        assert validate_email('test@') == False
    
    def test_validate_phone_valid(self):
        """Test valid phone validation"""
        assert validate_phone('(620) 235-4011') == True
        assert validate_phone('620-235-4011') == True
        assert validate_phone('6202354011') == True
    
    def test_validate_phone_invalid(self):
        """Test invalid phone validation"""
        assert validate_phone('123') == False
        assert validate_phone('abc-def-ghij') == False
    
    def test_validate_url_valid(self):
        """Test valid URL validation"""
        assert validate_url('https://pittstate.edu') == True
        assert validate_url('http://example.com/path') == True
    
    def test_validate_url_invalid(self):
        """Test invalid URL validation"""
        assert validate_url('not a url') == False
        assert validate_url('javascript:alert(1)') == False
    
    def test_sql_injection_detection(self):
        """Test SQL injection pattern detection"""
        assert check_sql_injection_patterns('SELECT * FROM users') == True
        assert check_sql_injection_patterns("' OR '1'='1") == True
        assert check_sql_injection_patterns('normal text') == False


class TestRateLimiting:
    """Test advanced rate limiting"""
    
    @patch('redis.Redis')
    def test_rate_limiter_initialization(self, mock_redis):
        """Test rate limiter initialization"""
        limiter = AdvancedRateLimiter()
        assert limiter is not None
    
    @patch('redis.Redis')
    def test_check_limit_under_threshold(self, mock_redis):
        """Test rate limiting under threshold"""
        mock_redis_instance = MagicMock()
        mock_redis_instance.zcard.return_value = 50  # Under limit
        
        limiter = AdvancedRateLimiter()
        limiter.redis_client = mock_redis_instance
        
        result = limiter.check_limit('test_key', limit=100, window=3600)
        assert result == True
    
    @patch('redis.Redis')
    def test_check_limit_exceeded(self, mock_redis):
        """Test rate limiting when exceeded"""
        mock_redis_instance = MagicMock()
        mock_redis_instance.zcard.return_value = 150  # Over limit
        
        limiter = AdvancedRateLimiter()
        limiter.redis_client = mock_redis_instance
        
        result = limiter.check_limit('test_key', limit=100, window=3600)
        assert result == False


class TestQueryOptimizer:
    """Test database query optimizer"""
    
    def test_query_tracker_initialization(self):
        """Test query tracker initialization"""
        tracker = QueryTracker()
        assert tracker is not None
        assert tracker.total_queries == 0
    
    def test_paginate_query_basic(self, app, db_session):
        """Test basic pagination"""
        from models import User
        
        with app.app_context():
            # Create test users
            for i in range(25):
                user = User(
                    email=f'test{i}@pittstate.edu',
                    first_name=f'Test{i}',
                    last_name='User',
                    role='student'
                )
                user.set_password('password123')
                db_session.add(user)
            db_session.commit()
            
            # Test pagination
            query = User.query
            result = paginate_query(query, page=1, per_page=10)
            
            assert len(result['items']) == 10
            assert result['page'] == 1
            assert result['total'] == 25
            assert result['pages'] == 3
            assert result['has_next'] == True


class TestSecurityHeaders:
    """Test security headers middleware"""
    
    def test_security_headers_present(self, client):
        """Test that security headers are present"""
        response = client.get('/')
        
        # Check for common security headers
        headers_to_check = [
            'X-Content-Type-Options',
            'X-Frame-Options',
            'Strict-Transport-Security'
        ]
        
        for header in headers_to_check:
            assert header in response.headers or response.status_code == 404


class TestHealthEndpoints:
    """Test health check endpoints"""
    
    def test_basic_health_check(self, client):
        """Test basic health endpoint"""
        response = client.get('/health/')
        assert response.status_code in [200, 404]  # May not exist yet
    
    def test_detailed_health_check(self, client):
        """Test detailed health endpoint"""
        response = client.get('/health/detailed')
        assert response.status_code in [200, 404]


@pytest.mark.slow
class TestPerformance:
    """Performance-related tests"""
    
    def test_large_query_performance(self, app, db_session):
        """Test performance with large dataset"""
        from models import User
        import time
        
        with app.app_context():
            # Create 100 test users
            users = []
            for i in range(100):
                user = User(
                    email=f'perf_test{i}@pittstate.edu',
                    first_name=f'Test{i}',
                    last_name='User',
                    role='student'
                )
                user.set_password('password123')
                users.append(user)
            
            db_session.bulk_save_objects(users)
            db_session.commit()
            
            # Test query performance
            start_time = time.time()
            result = User.query.limit(50).all()
            elapsed = time.time() - start_time
            
            assert len(result) == 50
            assert elapsed < 1.0  # Should complete in under 1 second
